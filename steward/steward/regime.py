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
    "cpi": "CPIAUCSL",          # Consumer prices (for year-over-year inflation)
    "fed_funds": "FEDFUNDS",    # Effective fed funds rate, monthly average
    "tbill_3m": "DGS3MO",       # 3-month T-bill yield: the cash hurdle for dual momentum (not a regime input)
}

# Days between an observation's date and when it is public, so backtests
# never use numbers that were not yet released.
PUBLICATION_LAG_DAYS = {"curve": 1, "hy_spread": 1, "claims": 5, "unrate": 35, "cpi": 45, "fed_funds": 32, "tbill_3m": 1}

SAHM_TRIGGER = 0.5
HY_STRESS_LEVEL = 6.0
HY_STRESS_RISE_6M = 1.5
HY_RECOVERY_FALL_6M = -1.0
CLAIMS_STRESS_RISE = 0.20
INFLATION_HOT = 0.03          # CPI inflation at or above 3%...
FED_HIKING_6M = 0.20          # ...while the Fed has raised rates at least 0.20 pts over 6 months


@dataclass(frozen=True)
class Snapshot:
    asof: pd.Timestamp
    curve: float
    curve_inverted_recently: bool  # Any inversion in the past 24 months
    hy_spread: float
    hy_spread_change_6m: float
    claims_rise: float  # 4-week average vs its 52-week low
    sahm: float  # 3-month avg unemployment minus prior 12-month low of that avg
    cpi_yoy: float = 0.0  # Consumer price inflation, year over year
    fed_change_6m: float = 0.0  # Change in the fed funds rate over 6 months


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
    cpi = _available(series["cpi"], "cpi", asof) if "cpi" in series else None
    ff = _available(series["fed_funds"], "fed_funds", asof) if "fed_funds" in series else None

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
        cpi_yoy=float(cpi.iloc[-1] / cpi.iloc[-13] - 1) if cpi is not None and len(cpi) >= 13 else 0.0,
        fed_change_6m=float(ff.iloc[-1] - ff.iloc[-7]) if ff is not None and len(ff) >= 7 else 0.0,
    )


def classify(snap: Snapshot, caps: dict[str, float]) -> Regime:
    credit_stress = snap.hy_spread >= HY_STRESS_LEVEL or snap.hy_spread_change_6m >= HY_STRESS_RISE_6M
    labor_stress = snap.claims_rise >= CLAIMS_STRESS_RISE
    # A central bank raising rates into hot inflation is a classic late-cycle sign
    # (1973, 1980, 2000, 2007, 2022) even when credit and jobs still look fine.
    inflation_squeeze = snap.cpi_yoy >= INFLATION_HOT and snap.fed_change_6m >= FED_HIKING_6M

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
    elif credit_stress or labor_stress or inflation_squeeze or snap.curve < 0 or snap.curve_inverted_recently:
        name = "Late-cycle"
        if inflation_squeeze:
            reasons.append(f"Fed hiking into hot inflation: CPI {snap.cpi_yoy:.1%}, fed funds {snap.fed_change_6m:+.2f} pts in 6 mo")
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
