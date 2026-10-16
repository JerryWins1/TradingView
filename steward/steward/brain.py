"""The brain: a current, dated picture of the economy and markets.

`python -m steward brain` refreshes brain/indicators.json and the data
section of brain/state.md from FRED and price data. Everything between the
NOTES markers in state.md is hand-written and preserved across refreshes.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pandas as pd

from .data import load_fred, load_prices
from .regime import FRED_SERIES, build_snapshot, classify
from .strategies import month_ends

BRAIN_DIR = Path(__file__).resolve().parent.parent / "brain"
STATE_FILE = BRAIN_DIR / "state.md"
INDICATORS_FILE = BRAIN_DIR / "indicators.json"
NOTES_START = "<!-- NOTES:START -->"
NOTES_END = "<!-- NOTES:END -->"

EXTRA_FRED = {
    "cpi": "CPIAUCSL",      # Consumer prices, for year-over-year inflation
    "core_cpi": "CPILFESL",
    "fed_funds": "FEDFUNDS",
    "tbill_3m": "DGS3MO",
    "treasury_10y": "DGS10",
}


def _last(s: pd.Series) -> tuple[float, str]:
    s = s.dropna()
    return float(s.iloc[-1]), s.index[-1].date().isoformat()


def _yoy(s: pd.Series) -> float:
    s = s.dropna()
    return float(s.iloc[-1] / s.iloc[-13] - 1) if len(s) >= 13 else float("nan")


def gather(rules: dict, refresh: bool = False) -> dict:
    """Collect every number the brain tracks, with the date of each reading."""
    macro = {k: load_fred(sid, refresh=refresh) for k, sid in FRED_SERIES.items()}
    extra = {k: load_fred(sid, refresh=refresh) for k, sid in EXTRA_FRED.items()}
    u, s = rules["universe"], rules["strategy"]
    tickers = [u["us_equity"], u["intl_equity"], u["bonds"]]
    prices = load_prices(tickers, refresh=refresh)

    snap = build_snapshot(macro)
    regime = classify(snap, rules["regime"]["exposure_caps"])

    m = month_ends(prices)
    sma = m[u["us_equity"]].rolling(s["trend_months"]).mean().iloc[-1]
    last = prices.iloc[-1]
    ret_12m = {t: float(prices[t].iloc[-1] / prices[t].iloc[-252] - 1) for t in tickers}
    cash_yield = _last(extra["tbill_3m"])[0] / 100

    us_beats_cash = ret_12m[u["us_equity"]] > cash_yield
    momentum_pick = (
        (u["us_equity"] if ret_12m[u["us_equity"]] >= ret_12m[u["intl_equity"]] else u["intl_equity"])
        if us_beats_cash else u["bonds"]
    )

    return {
        "updated": date.today().isoformat(),
        "prices_asof": prices.index[-1].date().isoformat(),
        "regime": {"name": regime.name, "equity_cap": regime.exposure_cap, "reasons": list(regime.reasons)},
        "indicators": {
            "yield_curve_10y2y": {"value": snap.curve, "asof": _last(macro["curve"])[1], "unit": "pct points"},
            "high_yield_spread": {"value": snap.hy_spread, "change_6m": snap.hy_spread_change_6m, "asof": _last(macro["hy_spread"])[1], "unit": "pct points"},
            "jobless_claims_4wk_vs_52wk_low": {"value": snap.claims_rise, "asof": _last(macro["claims"])[1], "unit": "fraction"},
            "unemployment_rate": {"value": _last(macro["unrate"])[0], "asof": _last(macro["unrate"])[1], "unit": "pct"},
            "sahm_gauge": {"value": snap.sahm, "trigger": 0.5, "unit": "pct points"},
            "cpi_yoy": {"value": _yoy(extra["cpi"]), "asof": _last(extra["cpi"])[1], "unit": "fraction"},
            "core_cpi_yoy": {"value": _yoy(extra["core_cpi"]), "asof": _last(extra["core_cpi"])[1], "unit": "fraction"},
            "fed_funds": {"value": _last(extra["fed_funds"])[0], "asof": _last(extra["fed_funds"])[1], "unit": "pct"},
            "tbill_3m": {"value": _last(extra["tbill_3m"])[0], "asof": _last(extra["tbill_3m"])[1], "unit": "pct"},
            "treasury_10y": {"value": _last(extra["treasury_10y"])[0], "asof": _last(extra["treasury_10y"])[1], "unit": "pct"},
        },
        "markets": {
            "prices": {t: float(last[t]) for t in tickers},
            "returns_12m": ret_12m,
            "trend": {
                "asset": u["us_equity"],
                "above_10m_average": bool(last[u["us_equity"]] > sma),
                "sma": float(sma),
                "distance": float(last[u["us_equity"]] / sma - 1),
            },
            "momentum": {"pick": momentum_pick, "us_beats_cash": us_beats_cash, "cash_yield": cash_yield},
        },
    }


def render_data(b: dict) -> str:
    i, mk, r = b["indicators"], b["markets"], b["regime"]
    tr, mo = mk["trend"], mk["momentum"]
    lines = [
        f"_Data refreshed {b['updated']} (prices as of {b['prices_asof']}). Numbers below are generated; edit only the notes section._",
        "",
        f"## Regime: {r['name']} (stocks capped at {r['equity_cap']:.0%})",
        "",
        *[f"- {x}" for x in r["reasons"]],
        "",
        "## Indicators",
        "",
        "| Indicator | Reading | As of |",
        "|---|---|---|",
        f"| Yield curve (10y-2y) | {i['yield_curve_10y2y']['value']:+.2f} pts | {i['yield_curve_10y2y']['asof']} |",
        f"| High-yield spread | {i['high_yield_spread']['value']:.2f} pts ({i['high_yield_spread']['change_6m']:+.2f} over 6 mo) | {i['high_yield_spread']['asof']} |",
        f"| Jobless claims, 4-wk avg vs 52-wk low | {i['jobless_claims_4wk_vs_52wk_low']['value']:+.0%} | {i['jobless_claims_4wk_vs_52wk_low']['asof']} |",
        f"| Unemployment rate | {i['unemployment_rate']['value']:.1f}% | {i['unemployment_rate']['asof']} |",
        f"| Sahm gauge | {i['sahm_gauge']['value']:.2f} (trigger 0.50) | |",
        f"| CPI inflation (yoy) | {i['cpi_yoy']['value']:.1%} | {i['cpi_yoy']['asof']} |",
        f"| Core CPI (yoy) | {i['core_cpi_yoy']['value']:.1%} | {i['core_cpi_yoy']['asof']} |",
        f"| Fed funds rate | {i['fed_funds']['value']:.2f}% | {i['fed_funds']['asof']} |",
        f"| 3-month T-bill | {i['tbill_3m']['value']:.2f}% | {i['tbill_3m']['asof']} |",
        f"| 10-year Treasury | {i['treasury_10y']['value']:.2f}% | {i['treasury_10y']['asof']} |",
        "",
        "## Markets",
        "",
        "| Fund | Price | 12-month return |",
        "|---|---|---|",
        *[f"| {t} | ${p:,.2f} | {mk['returns_12m'][t]:+.1%} |" for t, p in mk["prices"].items()],
        "",
        f"- Trend: {tr['asset']} is {'above' if tr['above_10m_average'] else 'BELOW'} its 10-month average ({tr['distance']:+.1%}), so the trend sleeve is {'invested' if tr['above_10m_average'] else 'in cash'}.",
        f"- Momentum: U.S. stocks {'beat' if mo['us_beats_cash'] else 'trail'} cash ({mo['cash_yield']:.1%}); the momentum sleeve picks **{mo['pick']}**.",
    ]
    return "\n".join(lines)


def extract_notes(text: str) -> str:
    if NOTES_START in text and NOTES_END in text:
        return text.split(NOTES_START)[1].split(NOTES_END)[0]
    return "\n\n"


def render_state(b: dict, notes: str) -> str:
    return f"# Steward brain\n\n{render_data(b)}\n\n{NOTES_START}{notes}{NOTES_END}\n"


def refresh(rules: dict, do_refresh: bool = False, brain_dir: Path = BRAIN_DIR) -> dict:
    b = gather(rules, refresh=do_refresh)
    brain_dir.mkdir(parents=True, exist_ok=True)
    state = brain_dir / "state.md"
    notes = extract_notes(state.read_text()) if state.exists() else "\n\n"
    state.write_text(render_state(b, notes))
    (brain_dir / "indicators.json").write_text(json.dumps(b, indent=2) + "\n")
    return b
