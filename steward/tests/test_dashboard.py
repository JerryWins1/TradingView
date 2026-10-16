import json
from datetime import date, timedelta

from steward import dashboard, sleeves
from steward.brain import NOTES_END, NOTES_START


def test_dashboard_builds_with_and_without_data(rules, tmp_path):
    out = dashboard.build(rules, tmp_path / "index.html", brain_file=tmp_path / "none.json", state_file=tmp_path / "none.md",
                          equity_file=tmp_path / "none.csv", trades_file=tmp_path / "none.csv", ledger_file=tmp_path / "none.json")
    html = out.read_text()
    assert "<!doctype html>" in html and "$25,000" in html and "No data yet" in html

    brain = {
        "updated": "2026-10-16", "regime": {"name": "Late-cycle", "equity_cap": 0.6, "reasons": ["Fed hiking into 3.7% inflation"]},
        "indicators": {
            "yield_curve_10y2y": {"value": 0.33}, "high_yield_spread": {"value": 3.25, "change_6m": 0.1},
            "jobless_claims_4wk_vs_52wk_low": {"value": 0.05}, "unemployment_rate": {"value": 4.2}, "sahm_gauge": {"value": 0.1},
            "cpi_yoy": {"value": 0.037}, "core_cpi_yoy": {"value": 0.026}, "fed_funds": {"value": 3.9}, "tbill_3m": {"value": 4.7},
            "treasury_10y": {"value": 5.1},
        },
        "markets": {"trend": {"above_10m_average": True, "distance": 0.08}, "momentum": {"pick": "EFA", "us_beats_cash": True}},
    }
    (tmp_path / "b.json").write_text(json.dumps(brain))
    (tmp_path / "s.md").write_text(f"# x\n\n{NOTES_START}\n## Hand-kept notes\n\n- Fed decision 2026-10-28 <b>\n{NOTES_END}\n")
    eq = tmp_path / "eq.csv"
    for i, (c, m, o) in enumerate([(15000, 5000, 5000), (15300, 5200, 5010), (15100, 5400, 5020)]):
        sleeves.record_equity({"core": c, "momentum": m, "options": o, "total": c + m + o}, date(2026, 10, 19) + timedelta(weeks=i), eq)
    (tmp_path / "t.csv").write_text("date,symbol,side,dollars,reason,close,qty,order_id,status,sleeve\n2026-10-19,SPY,buy,7500,rebalance,False,0,o1,filled,core\n")

    out = dashboard.build(rules, tmp_path / "index.html", brain_file=tmp_path / "b.json", state_file=tmp_path / "s.md",
                          equity_file=eq, trades_file=tmp_path / "t.csv", ledger_file=tmp_path / "none.json")
    html = out.read_text()
    assert "Late-cycle" in html and "$25,520" in html and "+2.1%" in html
    assert "<polyline" in html and "Fed decision 2026-10-28 &lt;b&gt;" in html  # notes are escaped
    assert "3.7%" in html and "rebalance" in html
