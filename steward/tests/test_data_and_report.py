import numpy as np
import pandas as pd

from steward.data import parse_fred, parse_stooq
from steward.regime import classify
from steward.report import build_report
from steward.strategies import combine

from .conftest import make_prices
from .test_regime import CAPS, snap


def test_parse_stooq():
    s = parse_stooq("Date,Open,High,Low,Close,Volume\n2024-01-03,1,1,1,101.5,10\n2024-01-02,1,1,1,100,10\n")
    assert s.tolist() == [100.0, 101.5]


def test_parse_fred_skips_missing_values():
    s = parse_fred("observation_date,T10Y2Y\n2024-01-01,.\n2024-01-02,0.25\n")
    assert s.tolist() == [0.25]
    old_format = parse_fred("DATE,UNRATE\n2024-01-01,3.7\n")
    assert old_format.iloc[0] == 3.7


def test_report_flags_trades_and_stops(rules):
    n = 400
    spy = np.concatenate([np.linspace(100, 200, n - 20), np.linspace(200, 170, 20)])
    p = make_prices({"SPY": spy, "EFA": np.linspace(100, 150, n), "AGG": np.full(n, 100.0)})
    target = combine(rules, p).iloc[-1]
    portfolio = {"cash": 20000 - 50 * 170, "positions": {"SPY": 50}}
    s = snap()
    text = build_report(rules, p, s, classify(s, CAPS), target, portfolio)
    assert "Economy: Expansion" in text
    assert "STOP HIT" in text  # 170 is below 10% under the 200 high
    assert "Not financial advice" in text
    assert "Buy about $" in text or "Sell about $" in text
