"""Run all three sleeves against the one paper account.

Order each run: book last week's fills, value every sleeve, then for each
sleeve plan (breaker, stops, rebalance) and send orders, book fills, and
record the sleeve's value for the scorecard.
"""

from __future__ import annotations

import json
import os
import time
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

from . import momentum, options, sleeves, tax, trade as tr
from .data import CASH, load_price
from .regime import FRED_SERIES, build_snapshot, classify
from .strategies import combine

PAPER_DIR = Path(__file__).resolve().parent.parent / "paper"
PENDING_FILE = PAPER_DIR / "pending.json"
OPEN_SPREADS_FILE = PAPER_DIR / "options_open.json"
FILL_WAIT_SECONDS = 4


def _json(path: Path, default):
    return json.loads(path.read_text()) if path.exists() else default


def _save(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2) + "\n")


def momentum_prices(rules: dict, refresh: bool = False) -> pd.DataFrame:
    """Outer-joined closes so a young stock does not shorten everyone's history."""
    frame = pd.concat([load_price(t, refresh=refresh) for t in rules["momentum"]["universe"]], axis=1)
    frame[CASH] = 1.0
    return frame.sort_index()


def signal_prices(prices: pd.DataFrame, today: date | None = None) -> pd.DataFrame:
    """Prices up to the last completed month-end, so a monthly signal is the
    same all month (as in the backtest) instead of flickering with mid-month closes."""
    today = today or (prices.index[-1].date() if len(prices) else date.today())
    first_of_month = pd.Timestamp(today.replace(day=1))
    return prices[prices.index < first_of_month]


def cash_yield(macro: dict) -> float:
    """Latest 3-month T-bill yield as a fraction, the hurdle U.S. stocks must beat in dual momentum."""
    s = macro.get("tbill_3m")
    return float(s.dropna().iloc[-1]) / 100 if s is not None and s.notna().any() else 0.0


def core_target(rules: dict, prices: pd.DataFrame, macro: dict, today: date | None = None,
                cash_yield: float = 0.0) -> tuple[object, object, pd.Series]:
    snap = build_snapshot(macro)
    regime = classify(snap, rules["regime"]["exposure_caps"])
    hist = signal_prices(prices, today)
    targets = combine(rules, hist, cash_yield=cash_yield)
    caps = pd.Series(regime.exposure_cap, index=targets.index[-1:])
    return snap, regime, combine(rules, hist, caps, cash_yield=cash_yield).iloc[-1]


def _book(ledger: dict, sleeve_name: str, symbol: str, side: str, qty: float, price: float, today: date,
          rules: dict, recent_buys: set[str], realized: list) -> None:
    taken = sleeves.apply_fill(ledger[sleeve_name], symbol, side, qty, price, today.isoformat(),
                               rules.get("tax", {}).get("lot_method", "hifo"))
    if taken:
        realized += tax.realize(sleeve_name, taken, price, today, rules, recent_buys)


TERMINAL = ("filled", "canceled", "expired", "rejected", "replaced")


def _book_delta(broker, oid: str, meta: dict, ledger: dict, today: date, rules: dict, recent_buys: set[str], realized: list) -> dict:
    """Book only the shares filled since we last looked. Alpaca's filled_qty is cumulative."""
    got = broker.get_order(oid)
    filled = float(got.get("filled_qty") or 0)
    new = filled - meta.get("booked", 0.0)
    if new > 1e-9:
        _book(ledger, meta["sleeve"], meta["symbol"], meta["side"], new, float(got["filled_avg_price"]), today, rules, recent_buys, realized)
        meta["booked"] = filled
    return got


def book_pending(broker, ledger: dict, pending: dict, today: date, rules: dict, recent_buys: set[str], realized: list) -> dict:
    """Book fills for orders still open from last run; keep the ones still open."""
    still = {}
    for oid, meta in pending.items():
        got = _book_delta(broker, oid, meta, ledger, today, rules, recent_buys, realized)
        if got.get("status") not in TERMINAL:
            still[oid] = meta
    return still


def book_orders(broker, orders: list[tr.Order], sleeve_name: str, ledger: dict, pending: dict, today: date,
                rules: dict, recent_buys: set[str], realized: list) -> None:
    for o in orders:
        if o.status != "submitted":
            continue
        meta = {"sleeve": sleeve_name, "symbol": o.symbol, "side": o.side, "booked": 0.0}
        got = _book_delta(broker, o.order_id, meta, ledger, today, rules, recent_buys, realized)
        status = got.get("status", "")
        if status == "filled":
            o.status = "filled"
        elif status in TERMINAL:
            o.status = f"{status}" + (" after partial fill" if meta["booked"] > 0 else "")
        else:
            o.status = "partial" if meta["booked"] > 0 else "open"
            pending[o.order_id] = meta  # still working at the broker; book the rest next run


def run(rules: dict, broker, core_prices: pd.DataFrame, mom_prices: pd.DataFrame, macro: dict,
        today: date, dry_run: bool, paper_dir: Path = PAPER_DIR) -> dict:
    """Returns a summary dict for the report. Writes ledger, state, logs unless dry_run."""
    ledger = sleeves.load_ledger(rules, paper_dir / "sleeves.json")
    state_all = _json(paper_dir / "state.json", {})
    pending = _json(paper_dir / "pending.json", {})
    out = {"date": today.isoformat(), "sleeves": {}, "orders": [], "options": None, "realized": []}
    realized: list = []
    recent_buys = tax.recent_buy_symbols(paper_dir / "trades.csv", today)

    if not dry_run:
        pending = book_pending(broker, ledger, pending, today, rules, recent_buys, realized)

    # Prices: broker's live price for anything held, else last cached close.
    broker_positions = broker.positions()
    live = {p.symbol: p.current_price for p in broker_positions}
    prices = {t: float(core_prices[t].iloc[-1]) for t in core_prices.columns if t != CASH}
    prices |= {t: float(mom_prices[t].dropna().iloc[-1]) for t in mom_prices.columns if t != CASH and mom_prices[t].notna().any()}
    prices |= live

    snap, regime, core_t = core_target(rules, core_prices, macro, today, cash_yield(macro))
    out["regime"] = {"name": regime.name, "cap": regime.exposure_cap}
    plans = {
        "core": (core_t, core_prices, rules),
        "momentum": (momentum.target_weights(signal_prices(mom_prices, today), rules), mom_prices, momentum.sleeve_rules(rules)),
    }

    for name, (target, px_frame, sleeve_rules) in plans.items():
        sl = ledger[name]
        equity = sleeves.sleeve_value(sl, prices)
        positions = sleeves.sleeve_positions(sl, prices)
        orders, state = tr.plan(target, equity, positions, px_frame, sleeve_rules, state_all.get(name, {"peak_equity": None, "breaker_until": None, "last_signal_month": None}), today)
        orders = tax.defer_rebalance_sells(orders, tax.lots_from(sl), prices, equity, rules, today)
        live_orders = [o for o in orders if not o.status.startswith("deferred")]
        tr.execute(live_orders, broker, dry_run)
        if not dry_run and any(o.status == "submitted" for o in orders):
            time.sleep(FILL_WAIT_SECONDS)
            book_orders(broker, orders, name, ledger, pending, today, rules, recent_buys, realized)
        state_all[name] = state
        out["sleeves"][name] = {"equity_before": equity, "target": {k: round(float(v), 3) for k, v in target.items() if v > 0}}
        out["orders"] += [{"sleeve": name, **o.__dict__} for o in orders]
        if not dry_run:
            tr.append_trades(orders, paper_dir / "trades.csv")

    out["options"] = run_options(rules, broker, prices, today, dry_run, paper_dir, broker_positions)

    values = {name: sleeves.sleeve_value(sl, prices) for name, sl in ledger.items()}
    values["total"] = sum(values.values())
    out["values"] = values
    out["realized"] = [r.__dict__ for r in realized]
    if not dry_run:
        tax.append_realized(realized, paper_dir / "realized.csv")
        sleeves.save_ledger(ledger, paper_dir / "sleeves.json")
        _save(paper_dir / "state.json", state_all)
        _save(paper_dir / "pending.json", pending)
        sleeves.record_equity(values, today, paper_dir / "equity.csv")
        _save(paper_dir / "prices.json", prices)
        try:  # after the books are saved; a problem here must not cost the run's bookkeeping
            out["schwab_preview"] = mirror_to_schwab(rules, out["orders"], prices, paper_dir)
        except Exception as e:
            out["schwab_preview"] = f"skipped: {e}"
    return out


def run_options(rules: dict, broker, prices: dict, today: date, dry_run: bool, paper_dir: Path,
                broker_positions: list | None = None) -> dict:
    o = rules["options"]
    open_spreads = _json(paper_dir / "options_open.json", [])
    result = {"mode": o["mode"], "open": len(open_spreads), "closed": [], "new": None}

    # Manage what is open using the broker's marks on each leg (same snapshot as the sleeve pricing).
    legs = {p.symbol: p.current_price for p in (broker_positions if broker_positions is not None else broker.positions())}
    marks = {}
    for sp in open_spreads:
        if sp["short_put"] in legs and sp["long_put"] in legs:
            marks[sp["id"]] = legs[sp["short_put"]] - legs[sp["long_put"]]
    for sp, why in options.manage(open_spreads, marks, rules):
        result["closed"].append({"id": sp["id"], "reason": why})
        if not dry_run and o["mode"] == "trade":
            body = options.mleg_order(options.Spread(**{k: sp[k] for k in options.Spread.__dataclass_fields__ if k in sp}))
            for leg in body["legs"]:
                leg["side"] = "buy" if leg["side"] == "sell" else "sell"
                leg["position_intent"] = "buy_to_close" if leg["side"] == "buy" else "sell_to_close"
            body["limit_price"] = f"{marks[sp['id']]:.2f}"
            broker.submit_order(body)
        open_spreads = [s for s in open_spreads if s["id"] != sp["id"]]

    if len(open_spreads) < o["max_open_spreads"] and o["underlying"] in prices:
        lo = (today + timedelta(days=o["days_to_expiry_min"])).isoformat()
        hi = (today + timedelta(days=o["days_to_expiry_max"])).isoformat()
        contracts = broker.option_contracts(o["underlying"], lo, hi, "put")
        spread = options.pick_spread(contracts, prices[o["underlying"]], rules, today)
        if spread:
            spread.note = "watch only" if o["mode"] == "watch" else ""
            if not dry_run and o["mode"] == "trade":
                spread.order_id = broker.submit_order(options.mleg_order(spread))
                open_spreads.append({"id": spread.order_id, **spread.__dict__})
            if not dry_run:
                options.log_spread(spread, paper_dir / "options_watch.csv")
            result["new"] = spread.__dict__
    if not dry_run:
        _save(paper_dir / "options_open.json", open_spreads)
    return result


def mirror_to_schwab(rules: dict, orders: list[dict], prices: dict, paper_dir: Path) -> int:
    """Write the sleeves' executed orders as Schwab order bodies for a person to approve later.

    Whole shares only. Sells are sized from the paper ledger, so the note asks
    the approver to check the quantity against real holdings. With
    attach_trailing_stop = true each buy carries a native GTC trailing stop;
    then Steward's own stop sells are skipped (the native stop covers them)
    and rebalance sells carry a reminder to resize the open stop. Nothing is
    sent: see steward/schwab.py.
    """
    cfg = rules.get("schwab", {})
    mirror = cfg.get("mirror_sleeves", [])
    if not mirror:
        return 0
    from . import schwab

    attach = cfg.get("attach_trailing_stop", False)
    bodies, notes = [], []
    for o in orders:
        if o["sleeve"] not in mirror or o["status"] not in ("filled", "partial", "submitted"):
            continue
        px = prices.get(o["symbol"], 0.0)
        qty = int(o["qty"]) if o.get("close") else schwab.whole_shares(o["dollars"], px)
        if qty < 1:
            continue
        note = f"{o['sleeve']}: {o['reason']}"
        if o["side"] == "buy":
            if attach:
                trail = rules["risk"]["trailing_stop"] if o["sleeve"] == "core" else rules["momentum"]["trailing_stop"]
                bodies.append(schwab.buy_with_stop(o["symbol"], qty, trail))
            else:
                bodies.append(schwab.market(o["symbol"], qty, "buy"))
        else:
            if attach and o["reason"].startswith("trailing stop"):
                continue  # the native stop attached at purchase handles this exit
            note += " | check quantity against Schwab holdings before approving"
            if attach:
                note += " | resize the open trailing stop to the remaining shares"
            bodies.append(schwab.market(o["symbol"], qty, "sell"))
        notes.append(note)
    if bodies:
        # One call so earlier items are superseded once, and these all stay live together.
        items = schwab.preview(bodies, note="", path=paper_dir / "schwab_preview.json")
        all_items = schwab.load_preview(paper_dir / "schwab_preview.json")
        by_id = {it["id"]: it for it in all_items}
        for it, note in zip(items, notes):
            by_id[it["id"]]["note"] = note
        schwab._save_preview(all_items, paper_dir / "schwab_preview.json")
    return len(bodies)
