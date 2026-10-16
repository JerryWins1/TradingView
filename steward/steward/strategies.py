"""Target-weight strategies, evaluated on the last trading day of each month.

Each function returns a DataFrame of target weights (rows = month-end
trading days, columns = the price columns), with every row summing to 1.
"""

from __future__ import annotations

import pandas as pd

from .data import CASH


def month_ends(prices: pd.DataFrame) -> pd.DataFrame:
    """Rows for the last actual trading day of each month."""
    return prices.groupby(prices.index.to_period("M")).tail(1)


def trend_weights(prices: pd.DataFrame, asset: str, months: int = 10) -> pd.DataFrame:
    """Faber timing: hold `asset` while above its N-month average, else cash."""
    m = month_ends(prices)
    sma = m[asset].rolling(months).mean()
    w = pd.DataFrame(0.0, index=m.index, columns=prices.columns)
    above = m[asset] > sma
    w.loc[above, asset] = 1.0
    w.loc[~above, CASH] = 1.0
    return w[sma.notna()]


def dual_momentum_weights(prices: pd.DataFrame, us: str, intl: str, bonds: str, months: int = 12) -> pd.DataFrame:
    """Antonacci global equities momentum.

    If U.S. stocks beat cash over the lookback, hold the stronger of U.S. and
    international stocks; otherwise hold bonds.
    """
    m = month_ends(prices)
    r = m.pct_change(months)
    w = pd.DataFrame(0.0, index=m.index, columns=prices.columns)
    for date, row in r.dropna().iterrows():
        if row[us] > row[CASH]:
            pick = us if row[us] >= row[intl] else intl
        else:
            pick = bonds
        w.loc[date, pick] = 1.0
    return w.loc[r.dropna().index]


def combine(rules: dict, prices: pd.DataFrame, exposure_caps: pd.Series | None = None) -> pd.DataFrame:
    """Blend the two strategies, then cap stock exposure by economic regime."""
    u, s = rules["universe"], rules["strategy"]
    trend = trend_weights(prices, u["us_equity"], s["trend_months"])
    mom = dual_momentum_weights(prices, u["us_equity"], u["intl_equity"], u["bonds"], s["momentum_months"])
    idx = trend.index.intersection(mom.index)
    w = s["trend_weight"] * trend.loc[idx] + s["momentum_weight"] * mom.loc[idx]

    if exposure_caps is not None:
        caps = exposure_caps.reindex(idx).fillna(1.0)
        equities = u["equities"]
        stock = w[equities].sum(axis=1)
        scale = (caps / stock.where(stock > 0)).clip(upper=1.0).fillna(1.0)
        trimmed = w[equities].mul(scale, axis=0)
        w[CASH] += (w[equities] - trimmed).sum(axis=1)
        w[equities] = trimmed
    return w
