from datetime import date, timedelta

import pytest

from steward import sleeves, tax
from steward.trade import Order

TODAY = date(2026, 10, 19)


def lot(sym, qty, price, days_ago):
    return tax.Lot(sym, qty, price, (TODAY - timedelta(days=days_ago)).isoformat())


def test_rates_by_account_and_holding(rules):
    assert tax.rate_for(rules, long_term=False) == pytest.approx(0.24)
    assert tax.rate_for(rules, long_term=True) == pytest.approx(0.15)
    assert tax.rate_for(rules, long_term=False, section_1256=True) == pytest.approx(0.6 * 0.15 + 0.4 * 0.24)
    ira = dict(rules) | {"tax": dict(rules["tax"]) | {"account_type": "roth"}}
    assert tax.rate_for(ira, long_term=False) == 0.0
    niit = dict(rules) | {"tax": dict(rules["tax"]) | {"niit": True, "state_rate": 0.05}}
    assert tax.rate_for(niit, long_term=True) == pytest.approx(0.15 + 0.038 + 0.05)


def test_hifo_sells_highest_cost_first_and_fifo_oldest():
    lots = [lot("SPY", 10, 100, 400), lot("SPY", 10, 120, 30), lot("EFA", 5, 80, 10)]
    left, taken = tax.consume_lots(lots, "SPY", 12, 130, TODAY, "hifo")
    assert [(l.price, q) for l, q in taken] == [(120, 10), (100, 2)]
    assert sum(l.qty for l in left if l.symbol == "SPY") == 8 and any(l.symbol == "EFA" for l in left)
    _, taken = tax.consume_lots(lots, "SPY", 12, 130, TODAY, "fifo")
    assert [(l.price, q) for l, q in taken] == [(100, 10), (120, 2)]


def test_realize_classifies_and_flags_wash_sales(rules):
    taken = [(lot("SPY", 10, 100, 400), 10), (lot("SPY", 5, 150, 20), 5)]
    rows = tax.realize("core", taken, 130, TODAY, rules, recent_buys={"SPY"})
    lt, st = rows
    assert lt.long_term and lt.gain == pytest.approx(300) and lt.est_tax == pytest.approx(45)
    assert not st.long_term and st.gain == pytest.approx(-100) and st.est_tax == 0
    assert st.wash_sale_risk and not lt.wash_sale_risk


def test_defer_only_routine_sells_close_to_long_term(rules):
    lots = [lot("SPY", 10, 100, 340)]  # long-term in 26 days, sitting on a gain
    prices = {"SPY": 130}
    orders = [
        Order("2026-10-19", "SPY", "sell", 500, "rebalance to 30% (held 35%)"),
        Order("2026-10-19", "SPY", "sell", 1300, "trailing stop: 130 <= 135", close=True, qty=10),
    ]
    out = tax.defer_rebalance_sells(orders, lots, prices, 10000, rules, TODAY)
    assert out[0].status.startswith("deferred") and out[0].dollars == 0
    assert out[1].status == "planned"  # stops are never deferred

    # Too far from long-term, or too far off target, or inside an IRA: sell as planned.
    far = tax.defer_rebalance_sells([Order("d", "SPY", "sell", 500, "rebalance")], [lot("SPY", 10, 100, 200)], prices, 10000, rules, TODAY)
    assert far[0].status == "planned"
    big = tax.defer_rebalance_sells([Order("d", "SPY", "sell", 2000, "rebalance")], lots, prices, 10000, rules, TODAY)
    assert big[0].status == "planned"
    ira = dict(rules) | {"tax": dict(rules["tax"]) | {"account_type": "ira"}}
    assert tax.defer_rebalance_sells([Order("d", "SPY", "sell", 500, "rebalance")], lots, prices, 10000, ira, TODAY)[0].status == "planned"


def test_ledger_tracks_lots_and_realized_log(rules, tmp_path):
    led = sleeves.load_ledger(rules, tmp_path / "none.json")
    core = led["core"]
    sleeves.apply_fill(core, "SPY", "buy", 10, 100.0, "2025-01-10")
    sleeves.apply_fill(core, "SPY", "buy", 5, 120.0, "2026-09-01")
    taken = sleeves.apply_fill(core, "SPY", "sell", 7, 130.0, TODAY.isoformat(), "hifo")
    assert core["positions"] == {"SPY": 8}
    assert [(l.price, q) for l, q in taken] == [(120.0, 5), (100.0, 2)]
    assert sorted((l["price"], l["qty"]) for l in core["lots"]) == [(100.0, 8)]

    rows = tax.realize("core", taken, 130.0, TODAY, rules)
    f = tmp_path / "realized.csv"
    tax.append_realized(rows, f)
    summary = tax.year_summary(f, 2026)
    assert summary["trades"] == 2
    assert summary["short_term"] == pytest.approx(50) and summary["long_term"] == pytest.approx(60)
    assert summary["est_tax"] == pytest.approx(50 * 0.24 + 60 * 0.15)

    rows = tax.unrealized(tax.lots_from(core), {"SPY": 130.0}, TODAY, rules)
    assert rows[0]["long_term"] and rows[0]["gain"] == pytest.approx(240)
    md = tax.markdown(rules, summary, rows)
    assert "Realized this year" in md and "SPY 8 @ 100.00" in md


def test_recent_buys_from_trade_log(tmp_path):
    f = tmp_path / "trades.csv"
    f.write_text("date,symbol,side,dollars,reason,close,qty,order_id,status\n"
                 "2026-10-01,SPY,buy,100,r,False,0,a,filled\n2026-08-01,EFA,buy,100,r,False,0,b,filled\n2026-10-10,AGG,sell,100,r,False,0,c,filled\n")
    assert tax.recent_buy_symbols(f, TODAY) == {"SPY"}


def test_deferral_looks_at_the_lots_that_would_sell(rules):
    # HIFO sells the 120-cost lot (bought 350 days ago) first; the fresh 100-cost lot is not touched.
    lots = [lot("SPY", 100, 120, 350), lot("SPY", 5, 100, 7)]
    orders = [Order("2026-10-19", "SPY", "sell", 2600, "rebalance to 30% (held 35%)")]  # ~20 shares at 130
    out = tax.defer_rebalance_sells(orders, lots, {"SPY": 130}, 100000, rules, TODAY)
    assert out[0].status.startswith("deferred") and "16 days" in out[0].status
    # FIFO would sell the old lot too; a sale big enough to reach the fresh lot still defers on the old lot's clock.
    fifo = dict(rules) | {"tax": dict(rules["tax"]) | {"lot_method": "fifo"}}
    out = tax.defer_rebalance_sells([Order("d", "SPY", "sell", 2600, "rebalance")], lots, {"SPY": 130}, 100000, fifo, TODAY)
    assert out[0].status.startswith("deferred")
