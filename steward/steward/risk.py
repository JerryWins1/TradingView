"""Position sizing and stop-loss rules."""

from __future__ import annotations

import math

import pandas as pd


def position_size(equity: float, entry: float, stop: float, risk_pct: float = 0.01, max_position_pct: float = 0.25) -> int:
    """Shares to buy so that hitting the stop loses at most `risk_pct` of equity."""
    if stop >= entry:
        raise ValueError("Stop must be below the entry price for a long position")
    by_risk = math.floor(equity * risk_pct / (entry - stop))
    by_cap = math.floor(equity * max_position_pct / entry)
    return max(0, min(by_risk, by_cap))


def trailing_stop(previous_stop: float | None, price: float, trail_pct: float) -> float:
    """A stop that only ever moves up."""
    candidate = price * (1 - trail_pct)
    return candidate if previous_stop is None else max(previous_stop, candidate)


def portfolio_heat(positions: list[tuple[float, float, float]], equity: float) -> float:
    """Share of equity lost if every (shares, price, stop) position hits its stop."""
    return sum(max(0.0, shares * (price - stop)) for shares, price, stop in positions) / equity


def drawdown(equity: pd.Series) -> pd.Series:
    return equity / equity.cummax() - 1
