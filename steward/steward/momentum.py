"""Momentum stocks sleeve: the rules-based version of "hot stocks".

Each month, rank a fixed list of liquid large caps by their return over the
past 12 months excluding the most recent month (the classic momentum
measure), and equal-weight the top N. Stops and the circuit breaker are
handled by trade.plan with this sleeve's own settings.
"""

from __future__ import annotations

import pandas as pd

from .data import CASH

TRADING_DAYS_PER_MONTH = 21


def rank(prices: pd.DataFrame, lookback_months: int = 12, skip_months: int = 1) -> pd.Series:
    """Momentum score per symbol, highest first. Symbols without enough history are dropped."""
    need = (lookback_months) * TRADING_DAYS_PER_MONTH + 1
    skip = skip_months * TRADING_DAYS_PER_MONTH
    scores = {}
    for sym in prices.columns:
        s = prices[sym].dropna()
        if sym == CASH or len(s) < need:
            continue
        end = s.iloc[-1 - skip] if skip else s.iloc[-1]
        start = s.iloc[-need]
        scores[sym] = float(end / start - 1)
    return pd.Series(scores, dtype=float).sort_values(ascending=False)


def target_weights(prices: pd.DataFrame, rules: dict) -> pd.Series:
    m = rules["momentum"]
    ranked = rank(prices, m["lookback_months"], m["skip_months"])
    picks = [s for s in ranked.index if ranked[s] > 0][: m["holdings"]]  # Only positive momentum
    w = pd.Series(0.0, index=list(prices.columns) + ([CASH] if CASH not in prices.columns else []))
    if picks:
        w[picks] = 1.0 / m["holdings"]
    w[CASH] = 1.0 - w.drop(CASH).sum()
    return w


def sleeve_rules(rules: dict) -> dict:
    """A rules dict whose [risk] section is this sleeve's, for trade.plan."""
    m = rules["momentum"]
    risk = dict(rules["risk"]) | {
        "trailing_stop": m["trailing_stop"],
        "max_drawdown": m["max_drawdown"],
        "rebalance_band": m["rebalance_band"],
    }
    return dict(rules) | {"risk": risk}
