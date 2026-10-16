import numpy as np
import pandas as pd
import pytest

from steward.backtest import run_backtest, summarize
from steward.data import CASH
from steward.strategies import month_ends

from .conftest import make_prices


def all_in(prices, asset):
    m = month_ends(prices)
    w = pd.DataFrame(0.0, index=m.index, columns=prices.columns)
    w[asset] = 1.0
    return w


def test_growing_asset_grows_account_net_of_costs():
    p = make_prices({"SPY": 100 * 1.0004 ** np.arange(800)})
    r = run_backtest(p, all_in(p, "SPY"), initial=20000, cost_bps=5, max_drawdown=None)
    assert r.equity.iloc[-1] > 20000
    assert r.equity.iloc[-1] < 20000 * p["SPY"].iloc[-1] / p["SPY"].iloc[0]


def test_no_lookahead_signal_day_return_is_not_captured():
    # Price jumps 50% on the first month-end itself; the strategy only buys after.
    prices = np.full(60, 100.0)
    p = make_prices({"SPY": prices})
    first_me = month_ends(p).index[0]
    p.loc[first_me:, "SPY"] = 150.0
    r = run_backtest(p, all_in(p, "SPY"), cost_bps=0, max_drawdown=None)
    assert r.equity.iloc[-1] == pytest.approx(20000)


def test_circuit_breaker_moves_to_cash_in_a_crash():
    path = np.concatenate([np.full(40, 100.0), np.linspace(100, 50, 40), np.full(40, 50.0)])
    p = make_prices({"SPY": path})
    targets = all_in(p, "SPY").iloc[:1]  # One buy signal, then let it ride
    with_breaker = run_backtest(p, targets, cost_bps=0, max_drawdown=0.15)
    without = run_backtest(p, targets, cost_bps=0, max_drawdown=None)
    assert with_breaker.breaker_trips == 1
    assert with_breaker.equity.iloc[-1] > without.equity.iloc[-1]
    assert with_breaker.equity.iloc[-1] == pytest.approx(20000 * 0.85, rel=0.03)


def test_summary_counts_six_month_doubles():
    eq = pd.Series(20000 * 2.01 ** (np.arange(400) / 126), index=pd.bdate_range("2020-01-01", periods=400))
    s = summarize(eq)
    assert s["pct_6m_windows_doubled"] == pytest.approx(1.0)
    assert s["cagr"] == pytest.approx(2.01**2 - 1, rel=0.01)  # Doubling every 6 months is about +300% a year


def test_unknown_target_date_rejected():
    p = make_prices({"SPY": np.full(30, 100.0)})
    bad = pd.DataFrame({"SPY": [1.0], CASH: [0.0]}, index=[pd.Timestamp("1999-01-01")])
    with pytest.raises(ValueError):
        run_backtest(p, bad)
