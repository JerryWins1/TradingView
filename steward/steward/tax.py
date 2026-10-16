"""Tax awareness: lots, holding periods, estimated tax, wash sales, deferral.

The paper account owes no tax. This layer exists so the system trades from
day one the way it would have to with real money, and so every sell shows
what it would have cost in tax. Rates and account type live in rules.toml
under [tax]; they are the user's assumptions, not advice. Confirm with a CPA.

Rules of thumb encoded here (U.S. federal):
- Held one year or less: gain taxed as ordinary income. Longer: long-term rate.
- Wash sale: a loss is disallowed if the same security is bought within 30
  days before or after the sale. Not an issue inside an IRA.
- Section 1256 (broad index options such as SPX/XSP): 60% long / 40% short
  regardless of holding period, no wash sales. SPY options do not qualify.
- Inside an IRA or Roth IRA none of this applies to individual trades.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path

from . import trade as tr

PAPER_DIR = Path(__file__).resolve().parent.parent / "paper"
REALIZED_FILE = PAPER_DIR / "realized.csv"
LONG_TERM_DAYS = 366  # Held more than one year
WASH_SALE_DAYS = 30


@dataclass
class Lot:
    symbol: str
    qty: float
    price: float
    date: str  # ISO purchase date

    def days_held(self, today: date) -> int:
        return (today - date.fromisoformat(self.date)).days

    def long_term(self, today: date) -> bool:
        return self.days_held(today) >= LONG_TERM_DAYS


@dataclass
class Realized:
    date: str
    sleeve: str
    symbol: str
    qty: float
    proceeds: float
    cost: float
    gain: float
    long_term: bool
    days_held: int
    est_tax: float
    wash_sale_risk: bool = False


def taxable(rules: dict) -> bool:
    return rules.get("tax", {}).get("account_type", "taxable") == "taxable"


def rate_for(rules: dict, long_term: bool, section_1256: bool = False) -> float:
    t = rules.get("tax", {})
    if not taxable(rules):
        return 0.0
    fed_st = t.get("ordinary_rate", 0.24)
    fed_lt = t.get("long_term_rate", 0.15)
    niit = 0.038 if t.get("niit", False) else 0.0
    state = t.get("state_rate", 0.0)
    if section_1256:
        return 0.6 * fed_lt + 0.4 * fed_st + niit + state
    return (fed_lt if long_term else fed_st) + niit + state


def consume_lots(lots: list[Lot], symbol: str, qty: float, price: float, today: date, method: str = "hifo") -> tuple[list[Lot], list[tuple[Lot, float]]]:
    """Remove `qty` shares of `symbol` from the lots and return (remaining, [(lot, qty_taken)]).

    hifo: highest cost first (smallest gain). fifo: oldest first (most likely long-term).
    """
    mine = [l for l in lots if l.symbol == symbol]
    others = [l for l in lots if l.symbol != symbol]
    if method == "fifo":
        mine.sort(key=lambda l: l.date)
    else:
        mine.sort(key=lambda l: (-l.price, l.date))
    taken, left = [], qty
    remaining = []
    for lot in mine:
        if left <= 1e-9:
            remaining.append(lot)
            continue
        take = min(lot.qty, left)
        taken.append((lot, take))
        left -= take
        if lot.qty - take > 1e-9:
            remaining.append(Lot(lot.symbol, lot.qty - take, lot.price, lot.date))
    return others + remaining, taken


def realize(sleeve: str, taken: list[tuple[Lot, float]], price: float, today: date, rules: dict,
            recent_buys: set[str] = frozenset()) -> list[Realized]:
    out = []
    for lot, q in taken:
        proceeds, cost = q * price, q * lot.price
        gain = proceeds - cost
        lt = lot.long_term(today)
        wash = gain < 0 and lot.symbol in recent_buys and taxable(rules)
        out.append(Realized(today.isoformat(), sleeve, lot.symbol, q, proceeds, cost, gain, lt, lot.days_held(today),
                            est_tax=max(gain, 0.0) * rate_for(rules, lt), wash_sale_risk=wash))
    return out


def defer_rebalance_sells(orders: list[tr.Order], lots: list[Lot], prices: dict[str, float], equity: float,
                          rules: dict, today: date) -> list[tr.Order]:
    """Hold off a routine rebalance sell when waiting a few weeks turns a
    short-term gain into a long-term one. Stops and the circuit breaker are
    never deferred: risk control comes before tax."""
    t = rules.get("tax", {})
    if not taxable(rules) or not t.get("defer_for_long_term", True):
        return orders
    max_wait = t.get("defer_max_days", 45)
    max_drift = t.get("defer_max_drift", 0.10)
    kept = []
    for o in orders:
        if o.side != "sell" or o.close or not o.reason.startswith("rebalance"):
            kept.append(o)
            continue
        px = prices.get(o.symbol, 0.0)
        if px <= 0:
            kept.append(o)
            continue
        _, taken = consume_lots(lots, o.symbol, o.dollars / px, px, today, t.get("lot_method", "hifo"))
        my = [l for l, _ in taken if not l.long_term(today) and px > l.price]  # the gains this sell would realize
        if not my:
            kept.append(o)
            continue
        days_left = max(LONG_TERM_DAYS - l.days_held(today) for l in my)
        if 0 < days_left <= max_wait and o.dollars / equity <= max_drift:
            o.status = f"deferred: long-term in {days_left} days"
            o.dollars = 0.0
        kept.append(o)
    return kept


def append_realized(rows: list[Realized], path: Path = REALIZED_FILE) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    new = not path.exists()
    with open(path, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].__dict__.keys()))
        if new:
            w.writeheader()
        for r in rows:
            w.writerow(r.__dict__)


def year_summary(path: Path, year: int) -> dict:
    out = {"short_term": 0.0, "long_term": 0.0, "est_tax": 0.0, "wash_sales": 0, "trades": 0}
    if not path.exists():
        return out
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            if not r["date"].startswith(str(year)):
                continue
            out["trades"] += 1
            out["long_term" if r["long_term"] == "True" else "short_term"] += float(r["gain"])
            out["est_tax"] += float(r["est_tax"])
            out["wash_sales"] += r["wash_sale_risk"] == "True"
    return out


def unrealized(lots: list[Lot], prices: dict[str, float], today: date, rules: dict) -> list[dict]:
    rows = []
    for l in lots:
        px = prices.get(l.symbol, l.price)
        gain = (px - l.price) * l.qty
        lt = l.long_term(today)
        rows.append({
            "symbol": l.symbol, "qty": l.qty, "cost": l.price, "price": px, "gain": gain,
            "days_held": l.days_held(today), "long_term": lt,
            "days_to_long_term": max(0, LONG_TERM_DAYS - l.days_held(today)),
            "tax_if_sold_now": max(gain, 0) * rate_for(rules, lt),
            "tax_if_long_term": max(gain, 0) * rate_for(rules, True),
        })
    return rows


def markdown(rules: dict, summary: dict, open_lots: list[dict]) -> str:
    t = rules.get("tax", {})
    acct = t.get("account_type", "taxable")
    lines = [f"_Account type assumed: **{acct}**. Rates assumed: ordinary {t.get('ordinary_rate', 0.24):.0%}, "
             f"long-term {t.get('long_term_rate', 0.15):.0%}, state {t.get('state_rate', 0.0):.0%}"
             f"{', NIIT 3.8%' if t.get('niit') else ''}. Edit [tax] in rules.toml; confirm with a CPA._", ""]
    if acct != "taxable":
        lines.append("Inside an IRA, individual trades carry no tax. Nothing to defer, no wash sales.")
        return "\n".join(lines)
    lines += [
        f"**Realized this year:** short-term {summary['short_term']:+,.0f}, long-term {summary['long_term']:+,.0f}, "
        f"estimated tax ${summary['est_tax']:,.0f} across {summary['trades']} closed lots"
        + (f", **{summary['wash_sales']} wash-sale risk(s)**" if summary["wash_sales"] else "") + ".",
        "",
        "| Lot | Held | Gain | Tax if sold now | Tax once long-term | Long-term in |",
        "|---|---|---|---|---|---|",
    ]
    for r in open_lots:
        lines.append(f"| {r['symbol']} {r['qty']:g} @ {r['cost']:,.2f} | {r['days_held']}d | {r['gain']:+,.0f} | "
                     f"${r['tax_if_sold_now']:,.0f} | ${r['tax_if_long_term']:,.0f} | "
                     f"{'now' if r['long_term'] else str(r['days_to_long_term']) + 'd'} |")
    if not open_lots:
        lines.append("| none | | | | | |")
    return "\n".join(lines)


def lots_from(ledger_sleeve: dict) -> list[Lot]:
    return [Lot(**l) for l in ledger_sleeve.get("lots", [])]


def lots_to(lots: list[Lot]) -> list[dict]:
    return [l.__dict__ for l in lots]


def recent_buy_symbols(trades_file: Path, today: date, days: int = WASH_SALE_DAYS) -> set[str]:
    """Symbols bought within the wash-sale window, from the trade log."""
    if not trades_file.exists():
        return set()
    cutoff = today - timedelta(days=days)
    out = set()
    with open(trades_file, newline="") as f:
        for r in csv.DictReader(f):
            if r["side"] == "buy" and r["status"] in ("filled", "partial", "submitted") and date.fromisoformat(r["date"]) >= cutoff:
                out.add(r["symbol"])
    return out
