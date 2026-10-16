"""Options income sleeve: defined-risk put credit spreads on SPY.

tastytrade-style mechanics: sell a put about 6% under the market with 30 to
45 days to expiry, buy a put $5 lower to cap the loss, take profit at half
the credit, cut the loss at twice the credit. In "watch" mode it only logs
what it would do; "trade" mode sends the order. Max loss per spread is
capped by rules, so this sleeve can never lose more than its own capital.

The 6%-below-spot strike is a stand-in for the ~16-delta put the method
calls for; Alpaca's contract list does not include delta.
"""

from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from datetime import date, timedelta
from pathlib import Path

PAPER_DIR = Path(__file__).resolve().parent.parent / "paper"
WATCH_FILE = PAPER_DIR / "options_watch.csv"
MULTIPLIER = 100


@dataclass
class Spread:
    date: str
    underlying: str
    expiry: str
    short_put: str
    short_strike: float
    long_put: str
    long_strike: float
    credit: float      # Per share; x100 per spread
    max_loss: float    # Dollars per spread, after credit
    mode: str
    order_id: str = ""
    note: str = ""


def pick_spread(contracts: list[dict], spot: float, rules: dict, today: date) -> Spread | None:
    """Choose the short and long puts from Alpaca's contract list.

    Each contract dict needs: symbol, expiration_date, strike_price, type,
    close_price (may be None).
    """
    o = rules["options"]
    lo = today + timedelta(days=o["days_to_expiry_min"])
    hi = today + timedelta(days=o["days_to_expiry_max"])
    puts = [
        c for c in contracts
        if c.get("type") == "put" and c.get("close_price") is not None
        and lo <= date.fromisoformat(c["expiration_date"]) <= hi
    ]
    if not puts:
        return None

    target_short = spot * (1 - o["short_strike_pct_below"])
    # Nearest expiry inside the window with a strike at or below the target.
    by_expiry: dict[str, list[dict]] = {}
    for c in puts:
        by_expiry.setdefault(c["expiration_date"], []).append(c)
    for expiry in sorted(by_expiry):
        chain = {float(c["strike_price"]): c for c in by_expiry[expiry]}
        shorts = [k for k in chain if k <= target_short]
        if not shorts:
            continue
        ks = max(shorts)
        kl = ks - o["spread_width"]
        if kl not in chain:
            continue
        credit = float(chain[ks]["close_price"]) - float(chain[kl]["close_price"])
        if credit <= 0:
            continue
        max_loss = (ks - kl - credit) * MULTIPLIER
        if max_loss > o["max_risk_per_spread"]:
            continue
        return Spread(
            date=today.isoformat(), underlying=o["underlying"], expiry=expiry,
            short_put=chain[ks]["symbol"], short_strike=ks, long_put=chain[kl]["symbol"], long_strike=kl,
            credit=round(credit, 2), max_loss=round(max_loss, 2), mode=o["mode"],
        )
    return None


def mleg_order(spread: Spread, qty: int = 1) -> dict:
    """Alpaca multi-leg order body: sell the short put, buy the long put, for a net credit."""
    return {
        "order_class": "mleg",
        "qty": str(qty),
        "type": "limit",
        "limit_price": f"{spread.credit:.2f}",
        "time_in_force": "day",
        "legs": [
            {"symbol": spread.short_put, "ratio_qty": "1", "side": "sell", "position_intent": "sell_to_open"},
            {"symbol": spread.long_put, "ratio_qty": "1", "side": "buy", "position_intent": "buy_to_open"},
        ],
    }


def manage(open_spreads: list[dict], marks: dict[str, float], rules: dict) -> list[tuple[dict, str]]:
    """Which open spreads to close and why. `marks` maps spread id -> current cost to close (per share)."""
    o = rules["options"]
    out = []
    for sp in open_spreads:
        cost = marks.get(sp["id"])
        if cost is None:
            continue
        if cost <= sp["credit"] * (1 - o["take_profit"]):
            out.append((sp, f"take profit: close at {cost:.2f} vs {sp['credit']:.2f} credit"))
        elif cost >= sp["credit"] * o["stop_multiple"]:
            out.append((sp, f"stop: close at {cost:.2f}, {o['stop_multiple']:.0f}x the {sp['credit']:.2f} credit"))
    return out


def log_spread(spread: Spread, path: Path = WATCH_FILE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    new = not path.exists()
    with open(path, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(asdict(spread).keys()))
        if new:
            w.writeheader()
        w.writerow(asdict(spread))
