"""The weekly check-in: economy, targets, trades to consider and stop alerts."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .data import CASH
from .regime import Regime, Snapshot

PORTFOLIO_FILE = Path(__file__).resolve().parent.parent / "paper" / "portfolio.json"
STOP_LOOKBACK_DAYS = 63  # Trailing stop measured from the highest close in ~3 months

DISCLAIMER = (
    "_Educational paper-trading output from a rules-based model. Not financial advice. "
    "Past results do not guarantee future returns. You make every real-money decision._"
)


def load_portfolio(path: Path = PORTFOLIO_FILE, starting_capital: float = 20000.0) -> dict:
    if path.exists():
        return json.loads(path.read_text())
    return {"cash": starting_capital, "positions": {}}


def current_weights(portfolio: dict, last_prices: pd.Series) -> tuple[pd.Series, float]:
    values = {t: shares * float(last_prices[t]) for t, shares in portfolio["positions"].items()}
    values[CASH] = float(portfolio["cash"])
    values = pd.Series(values)
    total = float(values.sum())
    return values / total, total


def build_report(
    rules: dict,
    prices: pd.DataFrame,
    snap: Snapshot,
    regime: Regime,
    target: pd.Series,
    portfolio: dict,
) -> str:
    last = prices.iloc[-1]
    asof = prices.index[-1].date()
    weights, total = current_weights(portfolio, last)
    band = rules["risk"]["rebalance_band"]
    trail = rules["risk"]["trailing_stop"]

    lines = [
        f"# Steward weekly check-in, {asof}",
        "",
        f"**Paper account value:** ${total:,.0f}",
        "",
        f"## Economy: {regime.name} (stocks capped at {regime.exposure_cap:.0%})",
        "",
    ]
    lines += [f"- {r}" for r in regime.reasons]
    lines += [
        "",
        "| Indicator | Reading |",
        "|---|---|",
        f"| Yield curve (10y-2y) | {snap.curve:+.2f} pts |",
        f"| High-yield credit spread | {snap.hy_spread:.2f} pts ({snap.hy_spread_change_6m:+.2f} over 6 mo) |",
        f"| Jobless claims vs 52-week low | {snap.claims_rise:+.0%} |",
        f"| Sahm recession gauge | {snap.sahm:.2f} (trigger 0.50) |",
        "",
        "## Target vs. current",
        "",
        "| Holding | Target | Current | Action |",
        "|---|---|---|---|",
    ]
    for t in sorted(set(target.index) | set(weights.index)):
        tw, cw = float(target.get(t, 0.0)), float(weights.get(t, 0.0))
        if tw == 0 and cw == 0:
            continue
        gap = tw - cw
        action = "Hold"
        if abs(gap) > band and t != CASH:
            action = f"{'Buy' if gap > 0 else 'Sell'} about ${abs(gap) * total:,.0f}"
        lines.append(f"| {t} | {tw:.0%} | {cw:.0%} | {action} |")

    lines += ["", "## Stop-loss check", ""]
    held = {t: s for t, s in portfolio["positions"].items() if s}
    if not held:
        lines.append("- No open positions.")
    for t, shares in held.items():
        high = float(prices[t].iloc[-STOP_LOOKBACK_DAYS:].max())
        stop = high * (1 - trail)
        price = float(last[t])
        status = "**STOP HIT, exit per rules**" if price <= stop else "OK"
        lines.append(f"- {t}: {shares:g} sh at ${price:,.2f}, trailing stop ${stop:,.2f} ({status})")

    lines += ["", DISCLAIMER, ""]
    return "\n".join(lines)
