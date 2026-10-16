from datetime import date

import numpy as np
import pandas as pd
import pytest

from steward.broker import AlpacaPaper, BrokerError
from steward.data import CASH
from steward.trade import Order, append_trades, execute, load_state, plan, save_state

from .conftest import make_prices

TODAY = date(2026, 10, 19)


class FakeBroker:
    def __init__(self):
        self.calls = []

    def buy_notional(self, symbol, dollars):
        self.calls.append(("buy", symbol, round(dollars, 2)))
        return f"buy-{symbol}"

    def sell_notional(self, symbol, dollars):
        self.calls.append(("sell", symbol, round(dollars, 2)))
        return f"sell-{symbol}"

    def close_position(self, symbol):
        self.calls.append(("close", symbol, None))
        return f"close-{symbol}"


def flat_prices():
    return make_prices({"SPY": np.full(100, 100.0), "EFA": np.full(100, 50.0), "AGG": np.full(100, 100.0)})


def target(**w):
    t = pd.Series(0.0, index=["SPY", "EFA", "AGG", CASH])
    for k, v in w.items():
        t[k] = v
    t[CASH] = 1 - t.drop(CASH).sum()
    return t


def test_plan_rebalances_sells_before_buys(rules):
    positions = {"AGG": (10000.0, 100.0)}
    orders, state = plan(target(SPY=0.5, EFA=0.5), 20000, positions, flat_prices(), rules, load_state(), TODAY)
    assert [(o.side, o.symbol, o.dollars) for o in orders] == [
        ("sell", "AGG", 10000.0), ("buy", "EFA", 10000.0), ("buy", "SPY", 10000.0),
    ]
    assert state["peak_equity"] == 20000
    assert state["last_signal_month"] == "2026-10"


def test_plan_ignores_small_gaps(rules):
    positions = {"SPY": (9400.0, 100.0), "EFA": (10600.0, 50.0)}  # 47% / 53%, inside the 5% band
    orders, _ = plan(target(SPY=0.5, EFA=0.5), 20000, positions, flat_prices(), rules, load_state(), TODAY)
    assert orders == []


def test_trailing_stop_closes_position(rules):
    prices = flat_prices()
    prices.loc[prices.index[-30:], "SPY"] = 120.0  # Recent high 120, stop at 108
    positions = {"SPY": (10000.0, 105.0)}
    orders, _ = plan(target(SPY=0.5, EFA=0.5), 20000, positions, prices, rules, load_state(), TODAY)
    stop = [o for o in orders if o.reason.startswith("trailing stop")]
    assert len(stop) == 1 and stop[0].close and stop[0].symbol == "SPY"
    assert not any(o.symbol == "SPY" and o.side == "buy" for o in orders)  # no re-buy same day


def test_circuit_breaker_sells_everything_once(rules):
    state = {"peak_equity": 20000, "breaker_until": None, "last_signal_month": "2026-10"}
    positions = {"SPY": (8000.0, 100.0), "EFA": (8500.0, 50.0)}
    orders, state = plan(target(SPY=0.5, EFA=0.5), 16500, positions, flat_prices(), rules, state, TODAY)
    assert sorted(o.symbol for o in orders) == ["EFA", "SPY"]
    assert all(o.close and "circuit breaker" in o.reason for o in orders)
    assert state["breaker_until"] == "2026-10"

    again, _ = plan(target(SPY=0.5), 16500, {}, flat_prices(), rules, state, TODAY)
    assert again == []  # Stays in cash for the rest of the month

    nxt, state2 = plan(target(SPY=0.5), 16500, {}, flat_prices(), rules, state, date(2026, 11, 2))
    assert state2["breaker_until"] is None and state2["peak_equity"] == 16500
    assert [o.side for o in nxt] == ["buy"]


def test_execute_routes_orders_and_dry_run():
    b = FakeBroker()
    orders = [
        Order("2026-10-19", "SPY", "sell", 1000, "trailing stop", close=True),
        Order("2026-10-19", "AGG", "sell", 500, "rebalance"),
        Order("2026-10-19", "EFA", "buy", 1500, "rebalance"),
    ]
    execute(orders, b, dry_run=True)
    assert b.calls == [] and all(o.status == "dry-run" for o in orders)
    execute(orders, b, dry_run=False)
    assert b.calls == [("close", "SPY", None), ("sell", "AGG", 500), ("buy", "EFA", 1500)]
    assert [o.order_id for o in orders] == ["close-SPY", "sell-AGG", "buy-EFA"]
    assert all(o.status == "submitted" for o in orders)


def test_trade_log_and_state_roundtrip(tmp_path):
    f = tmp_path / "trades.csv"
    append_trades([Order("2026-10-19", "SPY", "buy", 100, "r", status="submitted")], f)
    append_trades([Order("2026-10-26", "SPY", "sell", 50, "r", close=True)], f)
    rows = f.read_text().splitlines()
    assert rows[0].startswith("date,symbol,side,dollars,reason,close")
    assert len(rows) == 3

    s = tmp_path / "state.json"
    save_state({"peak_equity": 1, "breaker_until": None, "last_signal_month": "2026-10"}, s)
    assert load_state(s)["peak_equity"] == 1


def test_broker_refuses_live_endpoint(monkeypatch):
    monkeypatch.setenv("ALPACA_API_KEY", "k")
    monkeypatch.setenv("ALPACA_SECRET_KEY", "s")
    with pytest.raises(BrokerError):
        AlpacaPaper(base_url="https://api.alpaca.markets")
    assert AlpacaPaper().base_url == "https://paper-api.alpaca.markets"
    monkeypatch.delenv("ALPACA_SECRET_KEY")
    assert not AlpacaPaper.configured()
    with pytest.raises(BrokerError):
        AlpacaPaper()
