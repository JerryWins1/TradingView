"""Sleeve ledgers and the quarterly scorecard.

One Alpaca paper account, three sleeves. paper/sleeves.json records what each
sleeve owns (cash and shares) so results can be judged per strategy;
paper/equity.csv records each sleeve's value every run.
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

PAPER_DIR = Path(__file__).resolve().parent.parent / "paper"
LEDGER_FILE = PAPER_DIR / "sleeves.json"
EQUITY_FILE = PAPER_DIR / "equity.csv"
WEEKS_PER_YEAR = 52


def load_ledger(rules: dict, path: Path = LEDGER_FILE) -> dict:
    """Each sleeve: {"cash": float, "positions": {symbol: shares}}."""
    if path.exists():
        return json.loads(path.read_text())
    return {name: {"cash": float(s["capital"]), "positions": {}} for name, s in rules["sleeves"].items()}


def save_ledger(ledger: dict, path: Path = LEDGER_FILE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(ledger, indent=2) + "\n")


def sleeve_value(sleeve: dict, prices: dict[str, float]) -> float:
    return float(sleeve["cash"]) + sum(q * prices.get(sym, 0.0) for sym, q in sleeve["positions"].items())


def sleeve_positions(sleeve: dict, prices: dict[str, float]) -> dict[str, tuple[float, float]]:
    """symbol -> (market value, price), the shape trade.plan expects."""
    return {sym: (q * prices.get(sym, 0.0), prices.get(sym, 0.0)) for sym, q in sleeve["positions"].items() if q}


def apply_fill(sleeve: dict, symbol: str, side: str, qty: float, price: float) -> None:
    """Book a fill into the sleeve's ledger."""
    pos = sleeve["positions"]
    if side == "buy":
        sleeve["cash"] -= qty * price
        pos[symbol] = pos.get(symbol, 0.0) + qty
    else:
        sleeve["cash"] += qty * price
        pos[symbol] = pos.get(symbol, 0.0) - qty
        if abs(pos[symbol]) < 1e-9:
            del pos[symbol]


def record_equity(values: dict[str, float], asof: date, path: Path = EQUITY_FILE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    new = not path.exists()
    with open(path, "a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["date", "sleeve", "value"])
        for name, v in values.items():
            w.writerow([asof.isoformat(), name, f"{v:.2f}"])


def load_equity(path: Path = EQUITY_FILE) -> pd.DataFrame:
    """Wide frame: index date, one column per sleeve."""
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path, parse_dates=["date"])
    return df.pivot_table(index="date", columns="sleeve", values="value", aggfunc="last").sort_index()


@dataclass
class Score:
    sleeve: str
    weeks: int
    total_return: float
    max_drawdown: float
    sharpe: float
    vs_core: float  # Return minus core's return over the same window


def score(equity: pd.DataFrame, since: pd.Timestamp | None = None) -> list[Score]:
    if equity.empty or "core" not in equity:
        return []
    eq = equity if since is None else equity[equity.index >= since]
    eq = eq.drop(columns=["total"], errors="ignore").dropna(how="all").ffill()
    if len(eq) < 2:
        return []
    core_ret = float(eq["core"].iloc[-1] / eq["core"].iloc[0] - 1)
    out = []
    for name in eq.columns:
        s = eq[name].dropna()
        if len(s) < 2:
            continue
        rets = s.pct_change().dropna()
        total = float(s.iloc[-1] / s.iloc[0] - 1)
        sharpe = float(rets.mean() / rets.std() * np.sqrt(WEEKS_PER_YEAR)) if rets.std() > 0 else 0.0
        out.append(Score(
            sleeve=name, weeks=len(s), total_return=total,
            max_drawdown=float((s / s.cummax() - 1).min()), sharpe=sharpe, vs_core=total - core_ret,
        ))
    return out


def review_verdict(name: str, history: list[bool], rules: dict) -> str:
    """Promotion rule: two straight reviews beating core (risk-adjusted) earn
    more capital; two straight misses lose it. `history` is oldest-first."""
    sc = rules["scorecard"]
    if name == "core" or len(history) < 2:
        return "hold (need two completed reviews)"
    if history[-1] and history[-2]:
        return f"promote: +{sc['promote_step']:.0%} capital"
    if not history[-1] and not history[-2]:
        return f"demote: -{sc['demote_step']:.0%} capital"
    return "hold"


def scorecard_markdown(scores: list[Score], rules: dict, verdicts: dict[str, str] | None = None) -> str:
    if not scores:
        return "_No sleeve history yet._"
    lines = [
        "| Sleeve | Weeks | Return | Worst drop | Sharpe | vs Core | Review |",
        "|---|---|---|---|---|---|---|",
    ]
    for s in scores:
        v = (verdicts or {}).get(s.sleeve, "")
        lines.append(f"| {s.sleeve} | {s.weeks} | {s.total_return:+.1%} | {s.max_drawdown:.1%} | {s.sharpe:.2f} | {s.vs_core:+.1%} | {v} |")
    lines.append("")
    lines.append(f"_Reviews every {rules['scorecard']['review_every_days']} days. A sleeve beats core when its Sharpe is higher "
                 f"and its worst drop is no deeper. Two straight wins: +{rules['scorecard']['promote_step']:.0%} capital; two straight misses: "
                 f"-{rules['scorecard']['demote_step']:.0%}. No experimental sleeve above {rules['scorecard']['max_experimental_share']:.0%} of the account._")
    return "\n".join(lines)


def beats_core(s: Score, core: Score) -> bool:
    return s.sharpe > core.sharpe and s.max_drawdown >= core.max_drawdown
