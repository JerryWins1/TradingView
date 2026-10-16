"""Run all three sleeves against the one paper account.

Order each run: book last week's fills, value every sleeve, then for each
sleeve plan (breaker, stops, rebalance) and send orders, book fills, and
record the sleeve's value for the scorecard.
"""

from __future__ import annotations

import json
import time
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

from . import momentum, options, sleeves, trade as tr
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


def core_target(rules: dict, prices: pd.DataFrame, macro: dict) -> tuple[object, object, pd.Series]:
    snap = build_snapshot(macro)
    regime = classify(snap, rules["regime"]["exposure_caps"])
    targets = combine(rules, prices)
    caps = pd.Series(regime.exposure_cap, index=targets.index[-1:])
    return snap, regime, combine(rules, prices, caps).iloc[-1]


def book_pending(broker, ledger: dict, pending: dict) -> dict:
    """Book fills for orders submitted last run; keep the ones still open."""
    still = {}
    for oid, meta in pending.items():
        o = broker.get_order(oid)
        qty = float(o.get("filled_qty") or 0)
        if qty > 0:
            sleeves.apply_fill(ledger[meta["sleeve"]], meta["symbol"], meta["side"], qty, float(o["filled_avg_price"]))
        if o.get("status") not in ("filled", "canceled", "expired", "rejected", "replaced"):
            still[oid] = meta
    return still


def book_orders(broker, orders: list[tr.Order], sleeve_name: str, ledger: dict, pending: dict) -> None:
    for o in orders:
        if o.status != "submitted":
            continue
        got = broker.get_order(o.order_id)
        qty = float(got.get("filled_qty") or 0)
        if qty > 0:
            sleeves.apply_fill(ledger[sleeve_name], o.symbol, o.side, qty, float(got["filled_avg_price"]))
            o.status = "filled" if got.get("status") == "filled" else "partial"
        if got.get("status") != "filled":
            pending[o.order_id] = {"sleeve": sleeve_name, "symbol": o.symbol, "side": o.side}


def run(rules: dict, broker, core_prices: pd.DataFrame, mom_prices: pd.DataFrame, macro: dict,
        today: date, dry_run: bool, paper_dir: Path = PAPER_DIR) -> dict:
    """Returns a summary dict for the report. Writes ledger, state, logs unless dry_run."""
    ledger = sleeves.load_ledger(rules, paper_dir / "sleeves.json")
    state_all = _json(paper_dir / "state.json", {})
    pending = _json(paper_dir / "pending.json", {})
    out = {"date": today.isoformat(), "sleeves": {}, "orders": [], "options": None}

    if not dry_run:
        pending = book_pending(broker, ledger, pending)

    # Prices: broker's live price for anything held, else last cached close.
    live = {p.symbol: p.current_price for p in broker.positions()}
    prices = {t: float(core_prices[t].iloc[-1]) for t in core_prices.columns if t != CASH}
    prices |= {t: float(mom_prices[t].dropna().iloc[-1]) for t in mom_prices.columns if t != CASH and mom_prices[t].notna().any()}
    prices |= live

    snap, regime, core_t = core_target(rules, core_prices, macro)
    out["regime"] = {"name": regime.name, "cap": regime.exposure_cap}
    plans = {
        "core": (core_t, core_prices, rules),
        "momentum": (momentum.target_weights(mom_prices, rules), mom_prices, momentum.sleeve_rules(rules)),
    }

    for name, (target, px_frame, sleeve_rules) in plans.items():
        sl = ledger[name]
        equity = sleeves.sleeve_value(sl, prices)
        positions = sleeves.sleeve_positions(sl, prices)
        orders, state = tr.plan(target, equity, positions, px_frame, sleeve_rules, state_all.get(name, {"peak_equity": None, "breaker_until": None, "last_signal_month": None}), today)
        tr.execute(orders, broker, dry_run)
        if not dry_run and any(o.status == "submitted" for o in orders):
            time.sleep(FILL_WAIT_SECONDS)
            book_orders(broker, orders, name, ledger, pending)
        state_all[name] = state
        out["sleeves"][name] = {"equity_before": equity, "target": {k: round(float(v), 3) for k, v in target.items() if v > 0}}
        out["orders"] += [{"sleeve": name, **o.__dict__} for o in orders]
        if not dry_run:
            tr.append_trades(orders, paper_dir / "trades.csv")

    out["options"] = run_options(rules, broker, prices, today, dry_run, paper_dir)

    values = {name: sleeves.sleeve_value(sl, prices) for name, sl in ledger.items()}
    values["total"] = sum(values.values())
    out["values"] = values
    if not dry_run:
        sleeves.save_ledger(ledger, paper_dir / "sleeves.json")
        _save(paper_dir / "state.json", state_all)
        _save(paper_dir / "pending.json", pending)
        sleeves.record_equity(values, today, paper_dir / "equity.csv")
    return out


def run_options(rules: dict, broker, prices: dict, today: date, dry_run: bool, paper_dir: Path) -> dict:
    o = rules["options"]
    open_spreads = _json(paper_dir / "options_open.json", [])
    result = {"mode": o["mode"], "open": len(open_spreads), "closed": [], "new": None}

    # Manage what is open using the broker's marks on each leg.
    legs = {p.symbol: p.current_price for p in broker.positions()}
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
