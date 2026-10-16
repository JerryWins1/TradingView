import json

import numpy as np
import pandas as pd

from steward import brain

from .conftest import make_prices


def _series(values, freq, start="2015-01-01"):
    return pd.Series(values, index=pd.date_range(start, periods=len(values), freq=freq))


def fake_data(monkeypatch):
    n = 3000
    daily = {
        "T10Y2Y": _series(np.full(n, 0.33), "D"),
        "BAMLH0A0HYM2": _series(np.full(n, 3.25), "D"),
        "DGS3MO": _series(np.full(n, 4.7), "D"),
        "DGS10": _series(np.full(n, 5.1), "D"),
    }
    weekly = {"ICSA": _series(np.full(400, 199000.0), "W")}
    monthly = {
        "UNRATE": _series(np.full(100, 4.2), "MS"),
        "CPIAUCSL": _series(300 * 1.003 ** np.arange(100), "MS"),
        "CPILFESL": _series(300 * 1.002 ** np.arange(100), "MS"),
        "FEDFUNDS": _series(np.full(100, 3.9), "MS"),
    }
    series = daily | weekly | monthly

    def load_fred(sid, refresh=False):
        return series[sid].rename(sid)

    prices = make_prices({
        "SPY": np.linspace(500, 770, 800),
        "EFA": np.linspace(60, 100, 800),
        "AGG": np.full(800, 100.0),
    }, start="2023-09-01")

    monkeypatch.setattr(brain, "load_fred", load_fred)
    monkeypatch.setattr(brain, "load_prices", lambda tickers, refresh=False: prices)


def test_gather_reports_regime_trend_and_momentum(rules, monkeypatch):
    fake_data(monkeypatch)
    b = brain.gather(rules)
    assert b["regime"]["name"] == "Expansion"
    assert b["markets"]["trend"]["above_10m_average"] is True
    assert b["markets"]["momentum"]["us_beats_cash"] is True
    assert b["markets"]["momentum"]["pick"] == "EFA"  # EFA's 12-month gain is larger
    assert abs(b["indicators"]["cpi_yoy"]["value"] - (1.003**12 - 1)) < 1e-9
    assert b["indicators"]["tbill_3m"]["value"] == 4.7


def test_refresh_preserves_hand_notes(rules, monkeypatch, tmp_path):
    fake_data(monkeypatch)
    notes = "\n\n## Hand-kept notes\n\n- Keep me.\n\n"
    (tmp_path / "state.md").write_text(f"# old\n\nstale data\n\n{brain.NOTES_START}{notes}{brain.NOTES_END}\n")
    brain.refresh(rules, brain_dir=tmp_path)
    text = (tmp_path / "state.md").read_text()
    assert "- Keep me." in text
    assert "stale data" not in text
    assert "## Regime: Expansion" in text
    data = json.loads((tmp_path / "indicators.json").read_text())
    assert data["regime"]["name"] == "Expansion"


def test_refresh_without_existing_state(rules, monkeypatch, tmp_path):
    fake_data(monkeypatch)
    brain.refresh(rules, brain_dir=tmp_path)
    text = (tmp_path / "state.md").read_text()
    assert brain.NOTES_START in text and brain.NOTES_END in text
