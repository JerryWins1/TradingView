from datetime import date, timedelta

import numpy as np
import pandas as pd
import pytest

from steward import momentum, options, sleeves
from steward.data import CASH

from .conftest import make_prices


def test_ledger_defaults_and_fills(rules, tmp_path):
    led = sleeves.load_ledger(rules, tmp_path / "x.json")
    assert led["core"]["cash"] == 15000 and led["momentum"]["cash"] == 5000 and led["options"]["cash"] == 5000
    sleeves.apply_fill(led["core"], "SPY", "buy", 10, 700.0)
    assert led["core"]["cash"] == 8000 and led["core"]["positions"] == {"SPY": 10}
    sleeves.apply_fill(led["core"], "SPY", "sell", 10, 710.0)
    assert led["core"]["cash"] == 15100 and led["core"]["positions"] == {}
    assert sleeves.sleeve_value(led["core"], {}) == 15100
    sleeves.save_ledger(led, tmp_path / "x.json")
    assert sleeves.load_ledger(rules, tmp_path / "x.json") == led


def test_equity_history_and_score(tmp_path):
    f = tmp_path / "eq.csv"
    vals = [(100, 100, 100), (102, 105, 99), (101, 104, 101), (104, 110, 102)]
    for i, (c, m, o) in enumerate(vals):
        sleeves.record_equity({"core": c, "momentum": m, "options": o}, date(2026, 10, 19) + timedelta(weeks=i), f)
    eq = sleeves.load_equity(f)
    assert list(eq.columns) == ["core", "momentum", "options"] and len(eq) == 4
    scores = {s.sleeve: s for s in sleeves.score(eq)}
    assert scores["core"].total_return == pytest.approx(0.04)
    assert scores["momentum"].vs_core == pytest.approx(0.06)
    assert scores["options"].max_drawdown == pytest.approx(-0.01)
    assert sleeves.beats_core(scores["momentum"], scores["core"]) is True


def test_review_verdicts(rules):
    assert sleeves.review_verdict("momentum", [True, True], rules).startswith("promote")
    assert sleeves.review_verdict("momentum", [False, False], rules).startswith("demote")
    assert sleeves.review_verdict("momentum", [True, False], rules) == "hold"
    assert "need two" in sleeves.review_verdict("momentum", [True], rules)
    assert "need two" in sleeves.review_verdict("core", [True, True], rules)


def test_momentum_ranks_and_targets(rules):
    n = 300
    p = make_prices({
        "AAA": np.linspace(100, 200, n),            # strongest
        "BBB": np.linspace(100, 150, n),
        "CCC": np.linspace(100, 90, n),             # negative, excluded
        "DDD": np.concatenate([np.full(n - 50, np.nan), np.linspace(100, 300, 50)]),  # too young
    })
    r = momentum.rank(p, 12, 1)
    assert list(r.index[:2]) == ["AAA", "BBB"] and "DDD" not in r.index
    small = dict(rules) | {"momentum": dict(rules["momentum"]) | {"holdings": 2}}
    w = momentum.target_weights(p, small)
    assert w["AAA"] == w["BBB"] == 0.5 and w["CCC"] == 0 and w[CASH] == pytest.approx(0)
    only_one = dict(rules) | {"momentum": dict(rules["momentum"]) | {"holdings": 6}}
    w = momentum.target_weights(p, only_one)
    assert w["AAA"] == pytest.approx(1 / 6) and w[CASH] == pytest.approx(4 / 6)  # unfilled slots stay in cash


def test_momentum_sleeve_rules_override_risk(rules):
    sr = momentum.sleeve_rules(rules)
    assert sr["risk"]["trailing_stop"] == rules["momentum"]["trailing_stop"]
    assert sr["risk"]["risk_per_trade"] == rules["risk"]["risk_per_trade"]


def _contracts(expiry, strikes_prices):
    return [{"symbol": f"SPY{expiry}P{int(k * 1000):08d}", "expiration_date": expiry, "strike_price": str(k),
             "type": "put", "close_price": p} for k, p in strikes_prices]


def test_pick_spread_and_order(rules):
    today = date(2026, 10, 19)
    good = _contracts("2026-11-20", [(725, 4.00), (720, 3.20), (715, 0.50), (710, 0.30)])
    too_soon = _contracts("2026-11-05", [(720, 3.0), (715, 0.5)])
    sp = options.pick_spread(good + too_soon, spot=770.0, rules=rules, today=today)
    assert sp is not None
    assert sp.expiry == "2026-11-20"  # 17 days out is too soon; 32 days is inside the window
    assert sp.short_strike == 720 and sp.long_strike == 715  # 6% under 770 is 723.8 -> 720
    assert sp.credit == pytest.approx(2.70) and sp.max_loss == pytest.approx(230)  # (5 - 2.7) x 100

    body = options.mleg_order(sp)
    assert body["order_class"] == "mleg" and body["limit_price"] == "2.70"
    assert [l["side"] for l in body["legs"]] == ["sell", "buy"]
    assert body["legs"][0]["symbol"] == sp.short_put


def test_pick_spread_respects_risk_cap(rules):
    today = date(2026, 10, 19)
    cheap = _contracts("2026-11-20", [(720, 3.20), (715, 0.50)])  # credit 2.70, max loss 230
    sp = options.pick_spread(cheap, 770.0, rules, today)
    assert sp is not None and sp.max_loss == pytest.approx(230)
    rich = _contracts("2026-11-20", [(720, 1.00), (715, 0.50)])   # credit 0.50, max loss 450
    assert options.pick_spread(rich, 770.0, rules, today) is None


def test_manage_spreads(rules):
    open_ = [{"id": "a", "credit": 1.0}, {"id": "b", "credit": 1.0}, {"id": "c", "credit": 1.0}]
    out = options.manage(open_, {"a": 0.45, "b": 2.2, "c": 1.0}, rules)
    assert [(sp["id"], why.split(":")[0]) for sp, why in out] == [("a", "take profit"), ("b", "stop")]
