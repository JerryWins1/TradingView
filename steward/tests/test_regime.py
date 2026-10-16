import pandas as pd
import pytest

from steward.regime import Snapshot, build_snapshot, classify

CAPS = {"Expansion": 1.0, "Recovery": 0.8, "Late-cycle": 0.6, "Contraction": 0.3}


def snap(**kw):
    base = dict(
        asof=pd.Timestamp("2024-01-01"), curve=1.0, curve_inverted_recently=False,
        hy_spread=3.5, hy_spread_change_6m=0.0, claims_rise=0.05, sahm=0.1,
    )
    return Snapshot(**(base | kw))


@pytest.mark.parametrize(
    "kw, expected",
    [
        ({}, "Expansion"),
        ({"curve": -0.5, "curve_inverted_recently": True}, "Late-cycle"),
        ({"curve_inverted_recently": True}, "Late-cycle"),
        ({"hy_spread": 6.5}, "Late-cycle"),
        ({"sahm": 0.6}, "Contraction"),
        ({"hy_spread": 7.0, "claims_rise": 0.3}, "Contraction"),
        ({"hy_spread_change_6m": -1.5}, "Recovery"),
    ],
)
def test_classify(kw, expected):
    r = classify(snap(**kw), CAPS)
    assert r.name == expected
    assert r.exposure_cap == CAPS[expected]
    assert r.reasons


def _series(values, freq, start="2020-01-01"):
    return pd.Series(values, index=pd.date_range(start, periods=len(values), freq=freq))


def test_build_snapshot_math_and_publication_lag():
    unrate = _series([3.5] * 12 + [3.6, 4.0, 4.4, 4.8], "MS")  # Rising unemployment
    series = {
        "curve": _series([0.5] * 600, "D"),
        "hy_spread": _series([4.0] * 300 + [6.0] * 300, "D"),
        "claims": _series([200_000] * 60 + [260_000] * 10, "W"),
        "unrate": unrate,
    }
    s = build_snapshot(series, pd.Timestamp("2021-06-01"))
    assert s.curve == 0.5
    assert s.hy_spread == 6.0
    assert s.claims_rise == pytest.approx(0.30)
    # 3-mo avg now (4.0+4.4+4.8)/3 = 4.4 vs prior-12-mo low 3.5 -> 0.9
    # Observation dated 2021-04-01 is published ~2021-05-06, so it is included by June 1.
    assert s.sahm == pytest.approx(0.9)

    # A month earlier, April's number was not public yet.
    early = build_snapshot(series, pd.Timestamp("2021-05-01"))
    assert early.sahm == pytest.approx((3.6 + 4.0 + 4.4) / 3 - 3.5)
