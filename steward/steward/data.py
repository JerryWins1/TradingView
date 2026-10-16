"""Market and economic data, cached as CSV under data/cache.

Prices come from Stooq (free, no key), falling back to yfinance if it is
installed. Economic series come from FRED's public CSV endpoint. If a source
is unreachable, drop a CSV with Date,Close (prices) or DATE,value (FRED)
columns into the cache folder and Steward will use it.
"""

from __future__ import annotations

import io
import urllib.request
from pathlib import Path

import pandas as pd

CACHE_DIR = Path(__file__).resolve().parent.parent / "data" / "cache"
STOOQ_URL = "https://stooq.com/q/d/l/?s={symbol}&i=d"
FRED_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"

CASH = "CASH"  # Synthetic 0%-return cash column, so "go to cash" is explicit.


def _download(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 steward"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8")


def parse_stooq(text: str) -> pd.Series:
    df = pd.read_csv(io.StringIO(text))
    if "Date" not in df or "Close" not in df:
        raise ValueError("Unexpected price CSV (need Date and Close columns)")
    s = pd.Series(df["Close"].astype(float).values, index=pd.to_datetime(df["Date"]))
    return s.sort_index()


def parse_fred(text: str) -> pd.Series:
    df = pd.read_csv(io.StringIO(text))
    date_col = "observation_date" if "observation_date" in df else "DATE"
    values = pd.to_numeric(df.iloc[:, 1], errors="coerce")  # FRED uses "." for missing
    s = pd.Series(values.values, index=pd.to_datetime(df[date_col]))
    return s.dropna().sort_index()


def _fetch_price_text(ticker: str) -> str:
    try:
        text = _download(STOOQ_URL.format(symbol=f"{ticker.lower()}.us"))
        parse_stooq(text)
        return text
    except Exception:
        import yfinance as yf  # optional fallback

        hist = yf.Ticker(ticker).history(period="max", auto_adjust=True)
        if hist.empty:
            raise RuntimeError(f"No price data for {ticker}")
        out = pd.DataFrame({"Date": hist.index.tz_localize(None).date, "Close": hist["Close"]})
        return out.to_csv(index=False)


def load_price(ticker: str, cache_dir: Path = CACHE_DIR, refresh: bool = False) -> pd.Series:
    path = cache_dir / f"{ticker.upper()}.csv"
    if refresh or not path.exists():
        cache_dir.mkdir(parents=True, exist_ok=True)
        path.write_text(_fetch_price_text(ticker))
    return parse_stooq(path.read_text()).rename(ticker.upper())


def load_prices(tickers: list[str], cache_dir: Path = CACHE_DIR, refresh: bool = False) -> pd.DataFrame:
    """Daily closes for all tickers on common dates, plus a flat CASH column."""
    frame = pd.concat([load_price(t, cache_dir, refresh) for t in tickers], axis=1).dropna()
    frame[CASH] = 1.0
    return frame


def load_fred(series_id: str, cache_dir: Path = CACHE_DIR, refresh: bool = False) -> pd.Series:
    path = cache_dir / f"FRED_{series_id}.csv"
    if refresh or not path.exists():
        cache_dir.mkdir(parents=True, exist_ok=True)
        path.write_text(_download(FRED_URL.format(series_id=series_id)))
    return parse_fred(path.read_text()).rename(series_id)
