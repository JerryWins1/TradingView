import numpy as np
import pandas as pd

from steward.data import CASH
from steward.strategies import combine, dual_momentum_weights, month_ends, trend_weights

from .conftest import make_prices

N = 600  # ~28 months of business days


def test_month_ends_are_real_trading_days():
    p = make_prices({"SPY": np.linspace(100, 200, N)})
    m = month_ends(p)
    assert set(m.index) <= set(p.index)
    assert len(m) == len(set(p.index.to_period("M")))


def test_trend_holds_rising_asset_and_exits_falling_one():
    up = trend_weights(make_prices({"SPY": np.linspace(100, 200, N)}), "SPY", 10)
    assert (up["SPY"] == 1).all()
    down = trend_weights(make_prices({"SPY": np.linspace(200, 100, N)}), "SPY", 10)
    assert (down[CASH] == 1).all()


def test_dual_momentum_picks_strongest_or_bonds():
    p = make_prices({"SPY": np.linspace(100, 150, N), "EFA": np.linspace(100, 200, N), "AGG": np.full(N, 100.0)})
    w = dual_momentum_weights(p, "SPY", "EFA", "AGG", 12)
    assert (w["EFA"] == 1).all()

    p = make_prices({"SPY": np.linspace(150, 100, N), "EFA": np.linspace(100, 200, N), "AGG": np.full(N, 100.0)})
    w = dual_momentum_weights(p, "SPY", "EFA", "AGG", 12)
    assert (w["AGG"] == 1).all()  # U.S. stocks below cash -> bonds, even if EFA is up


def test_combine_rows_sum_to_one_and_regime_cap_applies(rules):
    p = make_prices({"SPY": np.linspace(100, 200, N), "EFA": np.linspace(100, 150, N), "AGG": np.full(N, 100.0)})
    w = combine(rules, p)
    assert np.allclose(w.sum(axis=1), 1)
    assert np.allclose(w[["SPY", "EFA"]].sum(axis=1), 1.0)

    capped = combine(rules, p, pd.Series(0.3, index=w.index))
    assert np.allclose(capped.sum(axis=1), 1)
    assert np.allclose(capped[["SPY", "EFA"]].sum(axis=1), 0.3)
    assert np.allclose(capped[CASH], 0.7)
