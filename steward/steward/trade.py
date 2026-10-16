"""Turn target weights into paper orders, with stops and the circuit breaker.

Order of operations each run:
1. Circuit breaker: if equity is 15% below its recorded peak, sell everything
   and stop until the next monthly signal.
2. Trailing stops: close any position trading below its stop.
3. Rebalance: sell what is over target, then buy what is under, ignoring
   gaps inside the rebalance band.

Every order is appended to paper/trades.csv with its reason.
"""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path

import pandas as pd

from .data import CASH

PAPER_DIR = Path(__file__).resolve().parent.parent / "paper"
TRADES_FILE = PAPER_DIR / "trades.csv"
STATE_FILE = PAPER_DIR / "state.json"
STOP_LOOKBACK_DAYS = 63
MIN_ORDER_DOLLARS = 5.0


@dataclass
class Order:
    date: str
    symbol: str
    side: str
    dollars: float
    reason: str
    close: bool = False  # Sell the whole position, not a dollar amount
    order_id: str = ""
    status: str = "planned"


def load_state(path: Path = STATE_FILE) -> dict:
    if path.exists():
        return json.loads(path.read_text())
    return {"peak_equity": None, "breaker_until": None, "last_signal_month": None}


def save_state(state: dict, path: Path = STATE_FILE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2) + "\n")


def append_trades(orders: list[Order], path: Path = TRADES_FILE) -> None:
    if not orders:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    new = not path.exists()
    with open(path, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(asdict(orders[0]).keys()))
        if new:
            w.writeheader()
        for o in orders:
            w.writerow(asdict(o))


def plan(
    target: pd.Series,
    equity: float,
    positions: dict[str, tuple[float, float]],  # symbol -> (market_value, current_price)
    prices: pd.DataFrame,
    rules: dict,
    state: dict,
    today: date,
) -> tuple[list[Order], dict]:
    """Decide the orders for today. Pure: no network, no files."""
    risk = rules["risk"]
    state = dict(state)
    orders: list[Order] = []
    this_month = today.strftime("%Y-%m")
    d = today.isoformat()

    # A new monthly signal lifts the breaker and resets the peak.
    if state.get("last_signal_month") != this_month:
        state["last_signal_month"] = this_month
        state["breaker_until"] = None
        state["peak_equity"] = equity
    state["peak_equity"] = max(state.get("peak_equity") or equity, equity)

    if state.get("breaker_until") == this_month:
        return [], state  # Already in cash for the month.

    if equity <= state["peak_equity"] * (1 - risk["max_drawdown"]):
        state["breaker_until"] = this_month
        for sym, (value, _) in positions.items():
            if value > 0:
                orders.append(Order(d, sym, "sell", value, f"circuit breaker: equity {equity:,.0f} is {risk['max_drawdown']:.0%} under peak {state['peak_equity']:,.0f}", close=True))
        return orders, state

    stopped = set()
    for sym, (value, price) in positions.items():
        if sym not in prices or value <= 0:
            continue
        high = float(prices[sym].iloc[-STOP_LOOKBACK_DAYS:].max())
        stop = high * (1 - risk["trailing_stop"])
        if price <= stop:
            stopped.add(sym)
            orders.append(Order(d, sym, "sell", value, f"trailing stop: {price:.2f} <= {stop:.2f} ({risk['trailing_stop']:.0%} under {high:.2f} high)", close=True))

    band = risk["rebalance_band"]
    sells, buys = [], []
    for sym in sorted(set(target.index) | set(positions)):
        if sym == CASH or sym in stopped:
            continue
        want = float(target.get(sym, 0.0)) * equity
        have = positions.get(sym, (0.0, 0.0))[0]
        gap = want - have
        if abs(gap) <= band * equity or abs(gap) < MIN_ORDER_DOLLARS:
            continue
        reason = f"rebalance to {float(target.get(sym, 0.0)):.0%} (held {have / equity:.0%})"
        (buys if gap > 0 else sells).append(Order(d, sym, "buy" if gap > 0 else "sell", abs(gap), reason))
    return orders + sells + buys, state


def execute(orders: list[Order], broker, dry_run: bool) -> list[Order]:
    """Send sells before buys so cash is there for the buys."""
    for o in orders:
        if dry_run:
            o.status = "dry-run"
            continue
        try:
            if o.close:
                o.order_id = broker.close_position(o.symbol)
            elif o.side == "sell":
                o.order_id = broker.sell_notional(o.symbol, o.dollars)
            else:
                o.order_id = broker.buy_notional(o.symbol, o.dollars)
            o.status = "submitted"
        except Exception as e:  # keep going; the log shows what failed
            o.status = f"failed: {e}"
    return orders
