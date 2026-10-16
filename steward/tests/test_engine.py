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
