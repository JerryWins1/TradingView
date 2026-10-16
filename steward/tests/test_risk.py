import pandas as pd
import pytest

from steward.risk import drawdown, portfolio_heat, position_size, trailing_stop


def test_position_size_limits_loss_to_one_percent():
    # $20k account, 1% risk = $200; $5 between entry and stop -> 40 shares.
    assert position_size(20000, entry=100, stop=95) == 40


def test_position_size_respects_max_position():
    # Risk allows 400 shares, but 25% of $20k at $100 caps it at 50.
    assert position_size(20000, entry=100, stop=99.5) == 50


def test_position_size_rejects_stop_above_entry():
    with pytest.raises(ValueError):
        position_size(20000, entry=100, stop=101)


def test_trailing_stop_only_moves_up():
    s = trailing_stop(None, 100, 0.10)
    assert s == pytest.approx(90)
    assert trailing_stop(s, 120, 0.10) == pytest.approx(108)
    assert trailing_stop(108, 100, 0.10) == 108


def test_portfolio_heat():
    assert portfolio_heat([(40, 100, 95), (10, 200, 180)], 20000) == pytest.approx(0.02)


def test_drawdown():
    dd = drawdown(pd.Series([100, 120, 90, 130]))
    assert dd.tolist() == pytest.approx([0, 0, -0.25, 0])
