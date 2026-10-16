"""Daily backtest of monthly target weights, with costs and a drawdown breaker."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .data import CASH

TRADING_DAYS = 252
SIX_MONTHS = 126


@dataclass
class Result:
    equity: pd.Series
    breaker_trips: int

    def metrics(self) -> dict[str, float]:
        return summarize(self.equity) | {"breaker_trips": self.breaker_trips}


def summarize(equity: pd.Series) -> dict[str, float]:
    rets = equity.pct_change().dropna()
    years = len(rets) / TRADING_DAYS
    six = equity.pct_change(SIX_MONTHS).dropna()
    return {
        "start_value": float(equity.iloc[0]),
        "end_value": float(equity.iloc[-1]),
        "cagr": float((equity.iloc[-1] / equity.iloc[0]) ** (1 / years) - 1),
        "volatility": float(rets.std() * np.sqrt(TRADING_DAYS)),
        "sharpe": float(rets.mean() / rets.std() * np.sqrt(TRADING_DAYS)) if rets.std() > 0 else 0.0,
        "max_drawdown": float((equity / equity.cummax() - 1).min()),
        "best_6m": float(six.max()),
        "worst_6m": float(six.min()),
        "pct_6m_windows_doubled": float((six >= 1.0).mean()),
    }


def run_backtest(
    prices: pd.DataFrame,
    targets: pd.DataFrame,
    initial: float = 20000.0,
    cost_bps: float = 5.0,
    max_drawdown: float | None = 0.15,
) -> Result:
    """Trade to `targets` at the close of the day after each month-end signal.

    A target computed from a month-end close is filled at the next day's
    close, so a signal never benefits from returns it could not have known. If equity falls
    `max_drawdown` below its peak, everything moves to cash until the next
    monthly signal.
    """
    prices = prices.loc[prices.index >= targets.index[0]]
    rets = prices.pct_change().fillna(0.0)
    # Each month-end target is executed on the following trading day.
    locs = prices.index.get_indexer(targets.index)
    if (locs < 0).any():
        raise ValueError("Every target date must be a trading day in `prices`")
    keep = locs + 1 < len(prices.index)
    orders = pd.DataFrame(targets.values[keep], index=prices.index[locs[keep] + 1], columns=targets.columns)
    orders = orders.reindex(columns=prices.columns, fill_value=0.0)

    cash_only = pd.Series(0.0, index=prices.columns)
    cash_only[CASH] = 1.0
    cost = cost_bps / 1e4

    positions = initial * cash_only
    equity_path = []
    peak = initial
    in_breaker = False
    trips = 0

    for day in prices.index:
        positions = positions * (1 + rets.loc[day])
        equity = positions.sum()

        if day in orders.index:  # Trade at this day's close, a full day after the signal.
            in_breaker = False
            target = equity * orders.loc[day]
            equity -= (target - positions).abs().sum() * cost
            positions = target * (equity / target.sum())
            peak = equity
        elif not in_breaker:
            peak = max(peak, equity)
            if max_drawdown is not None and equity <= peak * (1 - max_drawdown):
                in_breaker = True
                trips += 1
                equity -= (equity - positions[CASH]) * cost
                positions = equity * cash_only
        equity_path.append(equity)

    return Result(equity=pd.Series(equity_path, index=prices.index), breaker_trips=trips)


def buy_and_hold(prices: pd.Series, initial: float = 20000.0) -> pd.Series:
    return initial * prices / prices.iloc[0]
