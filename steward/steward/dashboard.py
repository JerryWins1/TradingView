"""Static financial dashboard: docs/index.html, rebuilt every weekly run.

Everything at a glance: regime, the economy's dials, sleeve values and their
history, the scorecard, recent orders, and the hand-kept notes from the brain.
Plain HTML and inline SVG, no external scripts, so it works on GitHub Pages
and as a file on disk.
"""

from __future__ import annotations

import csv
import html
import json
import re
from pathlib import Path

import pandas as pd

from . import sleeves
from .brain import INDICATORS_FILE, NOTES_END, NOTES_START, STATE_FILE

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "docs" / "index.html"
TRADES_FILE = ROOT / "paper" / "trades.csv"

# Categorical slots from the validated reference palette (light / dark).
SERIES = [("#2a78d6", "#3987e5"), ("#eb6834", "#d95926"), ("#1baf7a", "#199e70"), ("#eda100", "#c98500")]
REGIME_TONE = {"Expansion": "good", "Recovery": "good", "Late-cycle": "warning", "Contraction": "critical"}


def _esc(x) -> str:
    return html.escape(str(x))


def _money(x: float) -> str:
    return f"${x:,.0f}"


def _pct(x: float, signed: bool = False) -> str:
    return f"{x:+.1%}" if signed else f"{x:.1%}"


def line_chart(eq: pd.DataFrame, width: int = 720, height: int = 240) -> str:
    """Indexed sleeve values (start = 100) as an inline SVG with a hover-free table fallback."""
    cols = [c for c in eq.columns if c != "total"][:4]
    if eq.empty or len(eq) < 2 or not cols:
        return "<p class='muted'>Sleeve history starts with the first weekly run.</p>"
    idx = eq[cols].ffill()
    idx = idx / idx.iloc[0] * 100
    lo, hi = float(idx.min().min()), float(idx.max().max())
    pad = max((hi - lo) * 0.1, 1)
    lo, hi = lo - pad, hi + pad
    L, R, T, B = 40, 96, 10, 24
    def x(i): return L + (width - L - R) * i / (len(idx) - 1)
    def y(v): return T + (height - T - B) * (hi - v) / (hi - lo)
    parts = [f"<svg viewBox='0 0 {width} {height}' class='chart' role='img' aria-label='Sleeve values indexed to 100'>"]
    for k in range(5):  # hairline grid
        v = lo + (hi - lo) * k / 4
        parts.append(f"<line x1='{L}' x2='{width - R}' y1='{y(v):.1f}' y2='{y(v):.1f}' class='grid'/>"
                     f"<text x='{L - 6}' y='{y(v) + 4:.1f}' class='tick' text-anchor='end'>{v:.0f}</text>")
    for n, (i0, c) in enumerate(zip(range(len(cols)), cols)):
        pts = " ".join(f"{x(i):.1f},{y(v):.1f}" for i, v in enumerate(idx[c]))
        parts.append(f"<polyline points='{pts}' class='s{n}' fill='none' stroke-width='2' stroke-linejoin='round' stroke-linecap='round'/>")
        xe, ye = x(len(idx) - 1), y(idx[c].iloc[-1])
        parts.append(f"<circle cx='{xe:.1f}' cy='{ye:.1f}' r='4' class='s{n} dot'/>"
                     f"<text x='{xe + 8:.1f}' y='{ye + 4:.1f}' class='lbl'>{_esc(c)} {idx[c].iloc[-1]:.0f}</text>")
    parts.append(f"<text x='{L}' y='{height - 6}' class='tick'>{idx.index[0].date()}</text>"
                 f"<text x='{width - R}' y='{height - 6}' class='tick' text-anchor='end'>{idx.index[-1].date()}</text></svg>")
    legend = "".join(f"<span class='key'><i class='s{n} sw'></i>{_esc(c)}</span>" for n, c in enumerate(cols))
    return "".join(parts) + f"<div class='legend'>{legend}</div>"


def notes_html(state_text: str) -> str:
    """Render the hand-kept notes (simple markdown: headings, bullets) as HTML."""
    if NOTES_START not in state_text:
        return ""
    notes = state_text.split(NOTES_START)[1].split(NOTES_END)[0]
    out, in_list = [], False
    for raw in notes.splitlines():
        line = raw.strip()
        if line.startswith("- "):
            if not in_list:
                out.append("<ul>"); in_list = True
            out.append(f"<li>{_esc(line[2:])}</li>")
            continue
        if in_list:
            out.append("</ul>"); in_list = False
        if m := re.match(r"^(#{2,4})\s+(.*)", line):
            out.append(f"<h{len(m.group(1)) + 1}>{_esc(m.group(2))}</h{len(m.group(1)) + 1}>")
        elif line:
            out.append(f"<p>{_esc(line)}</p>")
    if in_list:
        out.append("</ul>")
    return "".join(out)


def recent_trades(path: Path = TRADES_FILE, n: int = 12) -> list[dict]:
    if not path.exists():
        return []
    with open(path, newline="") as f:
        rows = list(csv.DictReader(f))
    return rows[-n:][::-1]


def build(rules: dict, out: Path = OUTPUT, brain_file: Path = INDICATORS_FILE, state_file: Path = STATE_FILE,
          equity_file: Path | None = None, trades_file: Path = TRADES_FILE, ledger_file: Path | None = None) -> Path:
    brain = json.loads(brain_file.read_text()) if brain_file.exists() else None
    state_text = state_file.read_text() if state_file.exists() else ""
    eq = sleeves.load_equity(equity_file or sleeves.EQUITY_FILE)
    ledger = sleeves.load_ledger(rules, ledger_file or sleeves.LEDGER_FILE)
    scores = sleeves.score(eq)
    capital = sum(s["capital"] for s in rules["sleeves"].values())

    if not eq.empty:
        latest = eq.ffill().iloc[-1]
        total = float(latest.get("total", latest.drop("total", errors="ignore").sum()))
    else:
        latest, total = None, float(capital)
    delta = total / capital - 1

    tiles = []
    if brain:
        i = brain["indicators"]
        r = brain["regime"]
        tiles = [
            ("Yield curve 10y-2y", f"{i['yield_curve_10y2y']['value']:+.2f}", "inverted = warning" if i['yield_curve_10y2y']['value'] < 0 else "positive"),
            ("High-yield spread", f"{i['high_yield_spread']['value']:.2f}", f"{i['high_yield_spread']['change_6m']:+.2f} over 6 mo"),
            ("Jobless claims vs low", f"{i['jobless_claims_4wk_vs_52wk_low']['value']:+.0%}", "4-wk avg vs 52-wk low"),
            ("Unemployment", f"{i['unemployment_rate']['value']:.1f}%", f"Sahm {i['sahm_gauge']['value']:.2f} (trigger 0.50)"),
            ("CPI inflation", f"{i['cpi_yoy']['value']:.1%}", f"core {i['core_cpi_yoy']['value']:.1%}"),
            ("Fed funds", f"{i['fed_funds']['value']:.2f}%", f"3-mo T-bill {i['tbill_3m']['value']:.2f}%"),
            ("10-year Treasury", f"{i['treasury_10y']['value']:.2f}%", ""),
            ("SPY trend", "ON" if brain["markets"]["trend"]["above_10m_average"] else "OFF",
             f"{brain['markets']['trend']['distance']:+.1%} vs 10-mo avg"),
            ("Momentum pick", brain["markets"]["momentum"]["pick"],
             "U.S. beats cash" if brain["markets"]["momentum"]["us_beats_cash"] else "U.S. trails cash"),
        ]
        regime_html = (f"<div class='regime {REGIME_TONE.get(r['name'], 'warning')}'><span class='pill'>Economy</span>"
                       f"<strong>{_esc(r['name'])}</strong> <span>stocks capped at {r['equity_cap']:.0%}</span>"
                       f"<ul>{''.join(f'<li>{_esc(x)}</li>' for x in r['reasons'])}</ul></div>")
        updated = brain["updated"]
    else:
        regime_html = "<div class='regime warning'><strong>No data yet</strong> <span>run <code>python -m steward brain</code></span></div>"
        updated = "never"

    sleeve_rows = []
    for name, s in rules["sleeves"].items():
        val = float(latest[name]) if latest is not None and name in latest else float(s["capital"])
        held = ", ".join(f"{k} {v:g}" for k, v in ledger.get(name, {}).get("positions", {}).items()) or "cash"
        sleeve_rows.append(f"<tr><td>{_esc(name)}</td><td class='num'>{_money(s['capital'])}</td><td class='num'>{_money(val)}</td>"
                           f"<td class='num'>{_pct(val / s['capital'] - 1, True)}</td><td>{_esc(held)}</td></tr>")

    score_rows = "".join(
        f"<tr><td>{_esc(s.sleeve)}</td><td class='num'>{s.weeks}</td><td class='num'>{_pct(s.total_return, True)}</td>"
        f"<td class='num'>{_pct(s.max_drawdown)}</td><td class='num'>{s.sharpe:.2f}</td><td class='num'>{_pct(s.vs_core, True)}</td></tr>"
        for s in scores) or "<tr><td colspan='6' class='muted'>Scorecard fills in after the first weekly runs.</td></tr>"

    trade_rows = "".join(
        f"<tr><td>{_esc(t['date'])}</td><td>{_esc(t.get('sleeve', ''))}</td><td>{_esc(t['side'])}</td><td>{_esc(t['symbol'])}</td>"
        f"<td class='num'>{_money(float(t['dollars']))}</td><td>{_esc(t['status'])}</td><td class='muted'>{_esc(t['reason'])}</td></tr>"
        for t in recent_trades(trades_file)) or "<tr><td colspan='7' class='muted'>No orders yet.</td></tr>"

    tiles_html = "".join(f"<div class='tile'><div class='lab'>{_esc(a)}</div><div class='val'>{_esc(b)}</div><div class='sub'>{_esc(c)}</div></div>"
                         for a, b, c in tiles)
    paper_note = "Paper money only. Educational tool, not financial advice."

    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Steward Dashboard</title>
<style>
:root{{color-scheme:light dark;--page:#f9f9f7;--surface:#fcfcfb;--ink:#0b0b0b;--ink2:#52514e;--muted:#898781;--grid:#e1e0d9;--border:rgba(11,11,11,.10);
--s0:{SERIES[0][0]};--s1:{SERIES[1][0]};--s2:{SERIES[2][0]};--s3:{SERIES[3][0]};--good:#0ca30c;--warning:#fab219;--critical:#d03b3b;--up:#006300}}
@media (prefers-color-scheme:dark){{:root:not([data-theme=light]){{--page:#0d0d0d;--surface:#1a1a19;--ink:#f0efec;--ink2:#c3c2b7;--grid:#2c2c2a;--border:rgba(255,255,255,.10);
--s0:{SERIES[0][1]};--s1:{SERIES[1][1]};--s2:{SERIES[2][1]};--s3:{SERIES[3][1]};--up:#0ca30c}}}}
:root[data-theme=dark]{{--page:#0d0d0d;--surface:#1a1a19;--ink:#f0efec;--ink2:#c3c2b7;--grid:#2c2c2a;--border:rgba(255,255,255,.10);
--s0:{SERIES[0][1]};--s1:{SERIES[1][1]};--s2:{SERIES[2][1]};--s3:{SERIES[3][1]};--up:#0ca30c}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--page);color:var(--ink);font:15px/1.45 system-ui,-apple-system,"Segoe UI",sans-serif}}
main{{max-width:1100px;margin:0 auto;padding:24px 16px 48px}}h1{{font-size:22px;margin:0 0 4px}}h2{{font-size:16px;margin:28px 0 10px}}h3,h4{{margin:14px 0 6px;font-size:15px}}
.muted{{color:var(--muted)}}.sub{{color:var(--ink2);font-size:13px}}.card{{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:16px}}
.hero{{display:flex;flex-wrap:wrap;gap:16px;align-items:flex-end}}.hero .big{{font-size:48px;font-weight:600;line-height:1}}.hero .delta{{font-weight:600}}.hero .delta.up{{color:var(--up)}}.hero .delta.down{{color:var(--critical)}}
.regime{{display:flex;flex-wrap:wrap;gap:8px 12px;align-items:center;border-left:4px solid var(--warning);padding:10px 14px;margin-top:16px;background:var(--surface);border-radius:8px}}
.regime.good{{border-left-color:var(--good)}}.regime.critical{{border-left-color:var(--critical)}}.regime ul{{flex-basis:100%;margin:4px 0 0;padding-left:18px;color:var(--ink2);font-size:13px}}
.pill{{font-size:12px;text-transform:uppercase;letter-spacing:.04em;color:var(--muted)}}
.tiles{{display:grid;grid-template-columns:repeat(auto-fill,minmax(170px,1fr));gap:10px}}.tile{{background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:12px}}
.tile .lab{{font-size:12px;color:var(--ink2)}}.tile .val{{font-size:24px;font-weight:600;margin:2px 0}}.tile .sub{{font-size:12px}}
table{{width:100%;border-collapse:collapse;font-size:14px}}th{{text-align:left;color:var(--ink2);font-weight:500;border-bottom:1px solid var(--grid);padding:6px 8px}}td{{padding:6px 8px;border-bottom:1px solid var(--grid)}}td.num,th.num{{text-align:right;font-variant-numeric:tabular-nums}}
.chart{{width:100%;height:auto;display:block}}.grid{{stroke:var(--grid);stroke-width:1}}.tick{{fill:var(--muted);font-size:11px}}.lbl{{fill:var(--ink2);font-size:12px}}
.s0{{stroke:var(--s0)}}.s1{{stroke:var(--s1)}}.s2{{stroke:var(--s2)}}.s3{{stroke:var(--s3)}}.dot.s0{{fill:var(--s0)}}.dot.s1{{fill:var(--s1)}}.dot.s2{{fill:var(--s2)}}.dot.s3{{fill:var(--s3)}}.dot{{stroke:var(--surface);stroke-width:2}}
.legend{{display:flex;gap:14px;flex-wrap:wrap;font-size:13px;color:var(--ink2);margin-top:6px}}.sw{{display:inline-block;width:14px;height:3px;vertical-align:middle;margin-right:6px;border-radius:2px}}
.sw.s0{{background:var(--s0)}}.sw.s1{{background:var(--s1)}}.sw.s2{{background:var(--s2)}}.sw.s3{{background:var(--s3)}}
.notes{{columns:2;column-gap:28px;font-size:14px}}.notes h3,.notes h4{{break-after:avoid}}.notes ul{{padding-left:18px;margin:4px 0 10px}}@media(max-width:720px){{.notes{{columns:1}}}}
footer{{margin-top:32px;font-size:12px;color:var(--muted)}}
</style></head><body><main>
<h1>Steward</h1><div class="sub">Financial dashboard. Data refreshed {_esc(updated)}. {paper_note}</div>
<section class="card hero" style="margin-top:16px"><div><div class="pill">Paper account</div><div class="big">{_money(total)}</div></div>
<div><div class="pill">Since start ({_money(capital)})</div><div class="delta {'up' if delta >= 0 else 'down'}">{_pct(delta, True)}</div></div></section>
{regime_html}
<h2>The economy's dials</h2><div class="tiles">{tiles_html or "<div class='muted'>Run the brain to fill these.</div>"}</div>
<h2>Sleeves</h2><div class="card">{line_chart(eq)}
<table style="margin-top:14px"><thead><tr><th>Sleeve</th><th class="num">Started with</th><th class="num">Now</th><th class="num">Change</th><th>Holding</th></tr></thead><tbody>{''.join(sleeve_rows)}</tbody></table></div>
<h2>Scorecard</h2><div class="card"><table><thead><tr><th>Sleeve</th><th class="num">Weeks</th><th class="num">Return</th><th class="num">Worst drop</th><th class="num">Sharpe</th><th class="num">vs core</th></tr></thead><tbody>{score_rows}</tbody></table>
<p class="sub">Reviews every {rules['scorecard']['review_every_days']} days. Two straight reviews beating core on risk-adjusted return earn +{rules['scorecard']['promote_step']:.0%} capital; two straight misses lose {rules['scorecard']['demote_step']:.0%}. No experimental sleeve above {rules['scorecard']['max_experimental_share']:.0%} of the account.</p></div>
<h2>Recent orders</h2><div class="card"><table><thead><tr><th>Date</th><th>Sleeve</th><th>Side</th><th>Symbol</th><th class="num">Amount</th><th>Status</th><th>Reason</th></tr></thead><tbody>{trade_rows}</tbody></table></div>
<h2>Notes, dates and decisions</h2><div class="card notes">{notes_html(state_text) or "<p class='muted'>No notes yet.</p>"}</div>
<footer>{paper_note} Rules live in rules.toml; every order is logged with its reason.</footer>
</main></body></html>
"""
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page)
    return out
