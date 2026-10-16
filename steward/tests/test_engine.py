import pytest
import json
from datetime import date

import numpy as np
import pandas as pd

from steward import engine
from steward.broker import Position

from .conftest import make_prices
from .test_brain import fake_data


class FakeBroker:
    """Fills every market order instantly at the last known price."""

    def __init__(self, prices):
        self.prices = prices
        self.orders = {}
        self.pos = {}

    def positions(self):
        return [Position(s, q, q * self.prices[s], self.prices[s]) for s, q in self.pos.items() if q]

    def _fill(self, symbol, side, qty):
        oid = f"o{len(self.orders) + 1}"
        self.orders[oid] = {"status": "filled", "filled_qty": str(qty), "filled_avg_price": str(self.prices[symbol])}
        self.pos[symbol] = self.pos.get(symbol, 0) + (qty if side == "buy" else -qty)
        return oid

    def buy_notional(self, symbol, dollars):
        return self._fill(symbol, "buy", dollars / self.prices[symbol])

    def sell_notional(self, symbol, dollars):
        return self._fill(symbol, "sell", dollars / self.prices[symbol])

    def sell_qty(self, symbol, qty):
        return self._fill(symbol, "sell", qty)

    def get_order(self, oid):
        return self.orders[oid]

    def option_contracts(self, *a, **k):
        return [{"symbol": "SPY261120P00720000", "expiration_date": "2026-11-20", "strike_price": "720", "type": "put", "close_price": 3.2},
                {"symbol": "SPY261120P00715000", "expiration_date": "2026-11-20", "strike_price": "715", "type": "put", "close_price": 0.5}]

    def submit_order(self, body):
        return "mleg1"


def setup(rules, monkeypatch):
    fake_data(monkeypatch)
    n = 800
    core = make_prices({"SPY": np.linspace(500, 770, n), "EFA": np.linspace(60, 100, n), "AGG": np.full(n, 100.0)}, start="2023-09-01")
    mom_syms = rules["momentum"]["universe"]
    mom = make_prices({s: np.linspace(100, 100 + 5 * i, n) for i, s in enumerate(mom_syms)}, start="2023-09-01")
    macro = {k: engine.load_fred if False else None for k in []}  # placeholder, replaced below
    from steward import brain
    macro = {k: brain.load_fred(sid) for k, sid in engine.FRED_SERIES.items()}
    prices = {c: float(core[c].iloc[-1]) for c in core.columns if c != "CASH"} | {c: float(mom[c].iloc[-1]) for c in mom.columns if c != "CASH"}
    return core, mom, macro, FakeBroker(prices)


def test_dry_run_plans_but_writes_nothing(rules, monkeypatch, tmp_path):
    core, mom, macro, broker = setup(rules, monkeypatch)
    out = engine.run(rules, broker, core, mom, macro, date(2026, 10, 19), dry_run=True, paper_dir=tmp_path)
    assert out["regime"]["name"] == "Expansion"
    assert out["values"]["total"] == 25000
    assert all(o["status"] == "dry-run" for o in out["orders"])
    assert {o["sleeve"] for o in out["orders"]} == {"core", "momentum"}
    assert out["options"]["new"]["max_loss"] == 230 and out["options"]["mode"] == "watch"
    assert not (tmp_path / "sleeves.json").exists() and not broker.pos


def test_live_run_books_fills_per_sleeve(rules, monkeypatch, tmp_path):
    core, mom, macro, broker = setup(rules, monkeypatch)
    monkeypatch.setattr(engine, "FILL_WAIT_SECONDS", 0)
    out = engine.run(rules, broker, core, mom, macro, date(2026, 10, 19), dry_run=False, paper_dir=tmp_path)
    ledger = json.loads((tmp_path / "sleeves.json").read_text())
    # Core is fully invested in SPY/EFA (Expansion, trend on, EFA momentum); momentum holds 6 names.
    assert set(ledger["core"]["positions"]) <= {"SPY", "EFA"} and ledger["core"]["positions"]
    assert len(ledger["momentum"]["positions"]) == 6
    assert ledger["options"] == {"cash": 5000.0, "positions": {}, "lots": []}
    assert all("date" in l and l["qty"] > 0 for l in ledger["core"]["lots"])  # every buy recorded as a lot
    assert abs(sum(out["values"][k] for k in ("core", "momentum", "options")) - 25000) < 1  # fills at the same price, no cost
    assert (tmp_path / "equity.csv").exists() and (tmp_path / "trades.csv").exists()
    assert (tmp_path / "options_watch.csv").exists()
    assert json.loads((tmp_path / "pending.json").read_text()) == {}
    # Broker's account-wide positions equal the sum of the sleeve ledgers.
    for sym, qty in broker.pos.items():
        assert abs(sum(l["positions"].get(sym, 0) for l in ledger.values()) - qty) < 1e-6


def test_second_run_is_quiet_when_on_target(rules, monkeypatch, tmp_path):
    core, mom, macro, broker = setup(rules, monkeypatch)
    monkeypatch.setattr(engine, "FILL_WAIT_SECONDS", 0)
    engine.run(rules, broker, core, mom, macro, date(2026, 10, 19), dry_run=False, paper_dir=tmp_path)
    out = engine.run(rules, broker, core, mom, macro, date(2026, 10, 26), dry_run=False, paper_dir=tmp_path)
    assert out["orders"] == []
    assert len(pd.read_csv(tmp_path / "equity.csv")) == 8  # 4 rows per run


def test_mirror_to_schwab_preview(rules, tmp_path):
    orders = [
        {"sleeve": "core", "symbol": "SPY", "side": "buy", "dollars": 4500, "qty": 0, "close": False, "status": "filled", "reason": "rebalance"},
        {"sleeve": "core", "symbol": "EFA", "side": "sell", "dollars": 500, "qty": 5.5, "close": True, "status": "filled", "reason": "trailing stop"},
        {"sleeve": "momentum", "symbol": "NVDA", "side": "buy", "dollars": 800, "qty": 0, "close": False, "status": "filled", "reason": "rebalance"},
        {"sleeve": "core", "symbol": "AGG", "side": "sell", "dollars": 0, "qty": 0, "close": False, "status": "deferred: long-term in 20 days", "reason": "rebalance"},
        {"sleeve": "core", "symbol": "AGG", "side": "buy", "dollars": 900, "qty": 0, "close": False, "status": "failed: insufficient buying power", "reason": "rebalance"},
    ]
    prices = {"SPY": 770.0, "EFA": 90.0, "NVDA": 200.0, "AGG": 100.0}
    n = engine.mirror_to_schwab(rules, orders, prices, tmp_path)
    assert n == 2  # momentum not mirrored; deferred and failed orders skipped
    items = json.loads((tmp_path / "schwab_preview.json").read_text())
    assert items[0]["order"]["orderType"] == "MARKET" and items[0]["order"]["orderStrategyType"] == "SINGLE"  # no native stop by default
    assert items[0]["order"]["orderLegCollection"][0]["quantity"] == 5 and items[0]["note"] == "core: rebalance"
    assert items[1]["order"]["orderLegCollection"][0] == {"instruction": "SELL", "quantity": 5, "instrument": {"symbol": "EFA", "assetType": "EQUITY"}}
    assert "check quantity" in items[1]["note"]

    attach = dict(rules) | {"schwab": dict(rules["schwab"]) | {"attach_trailing_stop": True}}
    n = engine.mirror_to_schwab(attach, orders, prices, tmp_path)
    assert n == 1  # the stop sell is left to the native stop
    items = json.loads((tmp_path / "schwab_preview.json").read_text())
    assert [i["status"] for i in items[:2]] == ["superseded", "superseded"]
    assert items[2]["order"]["orderStrategyType"] == "TRIGGER"

    none = dict(rules) | {"schwab": dict(rules["schwab"]) | {"mirror_sleeves": []}}
    assert engine.mirror_to_schwab(none, orders, prices, tmp_path) == 0


def test_live_run_saves_books_even_if_mirror_breaks(rules, monkeypatch, tmp_path):
    core, mom, macro, broker = setup(rules, monkeypatch)
    monkeypatch.setattr(engine, "FILL_WAIT_SECONDS", 0)

    def boom(*a, **k):
        raise RuntimeError("schwab down")

    monkeypatch.setattr(engine, "mirror_to_schwab", boom)
    out = engine.run(rules, broker, core, mom, macro, date(2026, 10, 19), dry_run=False, paper_dir=tmp_path)
    assert out["schwab_preview"].startswith("skipped")
    assert (tmp_path / "sleeves.json").exists() and (tmp_path / "equity.csv").exists() and (tmp_path / "prices.json").exists()


def test_every_subcommand_has_a_handler():
    from steward import __main__ as cli

    for name in cli.SUBCOMMANDS:
        assert callable(cli.command_for(name)), name


def test_partial_fills_book_only_the_new_shares(rules, monkeypatch, tmp_path):
    from steward import trade as tr

    class Slow:
        """Fills 4 of 10 at first, all 10 by the next run; filled_qty is cumulative like Alpaca's."""
        def __init__(self): self.calls = 0
        def get_order(self, oid):
            self.calls += 1
            return {"status": "partially_filled", "filled_qty": "4", "filled_avg_price": "100"} if self.calls == 1 \
                else {"status": "filled", "filled_qty": "10", "filled_avg_price": "100"}

    broker = Slow()
    ledger = {"core": {"cash": 15000.0, "positions": {}, "lots": []}}
    pending, realized = {}, []
    o = tr.Order("2026-10-19", "SPY", "buy", 1000, "rebalance", order_id="o1", status="submitted")
    engine.book_orders(broker, [o], "core", ledger, pending, date(2026, 10, 19), rules, set(), realized)
    assert o.status == "partial" and ledger["core"]["positions"] == {"SPY": 4.0} and pending["o1"]["booked"] == 4.0
    pending = engine.book_pending(broker, ledger, pending, date(2026, 10, 26), rules, set(), realized)
    assert ledger["core"]["positions"] == {"SPY": 10.0} and ledger["core"]["cash"] == 15000 - 1000 and pending == {}


def test_rejected_orders_are_not_left_pending(rules):
    from steward import trade as tr

    class Rejecting:
        def get_order(self, oid): return {"status": "rejected", "filled_qty": "0"}

    ledger = {"core": {"cash": 1.0, "positions": {}, "lots": []}}
    pending = {}
    o = tr.Order("d", "SPY", "buy", 100, "rebalance", order_id="o1", status="submitted")
    engine.book_orders(Rejecting(), [o], "core", ledger, pending, date(2026, 10, 19), rules, set(), [])
    assert o.status == "rejected" and pending == {}


def test_signal_prices_stop_at_last_month_end():
    p = make_prices({"SPY": np.linspace(100, 110, 60)}, start="2026-09-01")
    sig = engine.signal_prices(p, date(2026, 10, 19))
    assert sig.index[-1].month == 9 and (sig.index < pd.Timestamp("2026-10-01")).all()
    assert engine.cash_yield({"tbill_3m": pd.Series([4.0, 4.7])}) == pytest.approx(0.047)
    assert engine.cash_yield({}) == 0.0
