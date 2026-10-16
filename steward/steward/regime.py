"""Classify the economy into a regime from public FRED indicators.

Nobody forecasts the economy reliably; this labels the current backdrop so
stock exposure can be dialed down when recession warning signs stack up.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

# Indicator -> FRED series id.
FRED_SERIES = {
    "curve": "T10Y2Y",          # 10-year minus 2-year Treasury yield
    "hy_spread": "BAMLH0A0HYM2",  # High-yield corporate bond spread
    "claims": "ICSA",           # Weekly initial jobless claims
    "unrate": "UNRATE",         # Unemployment rate
}

# Days between an observation's date and when it is public, so backtests
# never use numbers that were not yet released.
PUBLICATION_LAG_DAYS = {"curve": 1, "hy_spread": 1, "claims": 5, "unrate": 35}

SAHM_TRIGGER = 0.5
HY_STRESS_LEVEL = 6.0
HY_STRESS_RISE_6M = 1.5
HY_RECOVERY_FALL_6M = -1.0
CLAIMS_STRESS_RISE = 0.20


@dataclass(frozen=True)
class Snapshot:
    asof: pd.Timestamp
    curve: float
    curve_inverted_recently: bool  # Any inversion in the past 24 months
    hy_spread: float
    hy_spread_change_6m: float
    claims_rise: float  # 4-week average vs its 52-week low
    sahm: float  # 3-month avg unemployment minus prior 12-month low of that avg


@dataclass(frozen=True)
class Regime:
    name: str
    exposure_cap: float
    reasons: tuple[str, ...]


def _available(s: pd.Series, key: str, asof: pd.Timestamp | None) -> pd.Series:
    s = s.dropna().copy()
    s.index = s.index + pd.Timedelta(days=PUBLICATION_LAG_DAYS[key])
    if asof is not None:
        s = s[s.index <= asof]
    if s.empty:
        raise ValueError(f"No {key} data available as of {asof}")
    return s


def build_snapshot(series: dict[str, pd.Series], asof: pd.Timestamp | None = None) -> Snapshot:
    curve = _available(series["curve"], "curve", asof)
    hy = _available(series["hy_spread"], "hy_spread", asof)
    claims = _available(series["claims"], "claims", asof)
    unrate = _available(series["unrate"], "unrate", asof)
    asof = asof or max(s.index[-1] for s in (curve, hy, claims, unrate))

    recent_curve = curve[curve.index > asof - pd.DateOffset(months=24)]
    hy_6m_ago = hy.asof(asof - pd.DateOffset(months=6))

    claims_ma = claims.rolling(4).mean().dropna()
    claims_low = claims_ma[claims_ma.index > asof - pd.DateOffset(weeks=52)].min()

    unrate_ma = unrate.rolling(3).mean().dropna()
    sahm = unrate_ma.iloc[-1] - unrate_ma.iloc[-13:-1].min() if len(unrate_ma) >= 13 else 0.0

    return Snapshot(
        asof=pd.Timestamp(asof),
        curve=float(curve.iloc[-1]),
        curve_inverted_recently=bool((recent_curve < 0).any()),
        hy_spread=float(hy.iloc[-1]),
        hy_spread_change_6m=float(hy.iloc[-1] - hy_6m_ago) if pd.notna(hy_6m_ago) else 0.0,
        claims_rise=float(claims_ma.iloc[-1] / claims_low - 1),
        sahm=float(sahm),
    )


def classify(snap: Snapshot, caps: dict[str, float]) -> Regime:
    credit_stress = snap.hy_spread >= HY_STRESS_LEVEL or snap.hy_spread_change_6m >= HY_STRESS_RISE_6M
    labor_stress = snap.claims_rise >= CLAIMS_STRESS_RISE

    reasons = []
    if snap.sahm >= SAHM_TRIGGER:
        reasons.append(f"Sahm recession rule triggered ({snap.sahm:.2f} >= {SAHM_TRIGGER})")
    if credit_stress:
        reasons.append(f"Credit stress: high-yield spread {snap.hy_spread:.2f} ({snap.hy_spread_change_6m:+.2f} in 6 mo)")
    if labor_stress:
        reasons.append(f"Jobless claims up {snap.claims_rise:.0%} from their 52-week low")

    if snap.sahm >= SAHM_TRIGGER or (credit_stress and labor_stress):
        name = "Contraction"
    elif snap.hy_spread_change_6m <= HY_RECOVERY_FALL_6M:
        name = "Recovery"
        reasons.append(f"Credit spreads healing ({snap.hy_spread_change_6m:+.2f} in 6 mo)")
    elif credit_stress or labor_stress or snap.curve < 0 or snap.curve_inverted_recently:
        name = "Late-cycle"
        if snap.curve < 0:
            reasons.append(f"Yield curve inverted ({snap.curve:+.2f})")
        elif snap.curve_inverted_recently:
            reasons.append("Yield curve un-inverting after an inversion (historical late-cycle sign)")
    else:
        name = "Expansion"
        reasons.append("No recession warning signs active")
    return Regime(name=name, exposure_cap=caps[name], reasons=tuple(reasons))


def regime_history(series: dict[str, pd.Series], dates: pd.DatetimeIndex, caps: dict[str, float]) -> pd.Series:
    """Equity exposure cap at each date, using only data public by then."""
    out = {}
    for d in dates:
        try:
            out[d] = classify(build_snapshot(series, d), caps).exposure_cap
        except ValueError:
            out[d] = 1.0  # Before indicator history begins, no cap.
    return pd.Series(out)
