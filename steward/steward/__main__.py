"""Command line: python -m steward {fetch,regime,backtest,report}."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from . import backtest as bt
from .config import load_rules
from .data import load_fred, load_prices
from .regime import FRED_SERIES, build_snapshot, classify, regime_history
from .report import build_report, load_portfolio
from .strategies import combine
from . import trade as tr
from . import brain as brain_mod
from .broker import AlpacaPaper


def _tickers(rules: dict) -> list[str]:
    u = rules["universe"]
    return [u["us_equity"], u["intl_equity"], u["bonds"]]


def _macro(refresh: bool) -> dict[str, pd.Series]:
    return {k: load_fred(sid, refresh=refresh) for k, sid in FRED_SERIES.items()}


def cmd_fetch(rules: dict, args) -> None:
    prices = load_prices(_tickers(rules), refresh=True)
    _macro(refresh=True)
    print(f"Prices {prices.index[0].date()} to {prices.index[-1].date()}; FRED series cached.")


def cmd_regime(rules: dict, args) -> None:
    snap = build_snapshot(_macro(args.refresh))
    regime = classify(snap, rules["regime"]["exposure_caps"])
    print(f"{regime.name} (stocks capped at {regime.exposure_cap:.0%}) as of {snap.asof.date()}")
    for r in regime.reasons:
        print(f"  - {r}")


def cmd_backtest(rules: dict, args) -> None:
    prices = load_prices(_tickers(rules), refresh=args.refresh)
    prices = prices[prices.index >= pd.Timestamp(args.start)]
    caps = None
    if not args.no_regime:
        targets_raw = combine(rules, prices)
        caps = regime_history(_macro(args.refresh), targets_raw.index, rules["regime"]["exposure_caps"])
    targets = combine(rules, prices, caps)
    risk = rules["risk"]
    initial = rules["account"]["starting_capital"]
    result = bt.run_backtest(prices, targets, initial, risk["cost_bps"], risk["max_drawdown"])
    spy = rules["universe"]["us_equity"]
    bench = bt.summarize(bt.buy_and_hold(prices.loc[result.equity.index, spy], initial))

    rows = [
        ("Ending value", "end_value", "${:,.0f}"),
        ("Yearly growth (CAGR)", "cagr", "{:.1%}"),
        ("Volatility", "volatility", "{:.1%}"),
        ("Sharpe ratio", "sharpe", "{:.2f}"),
        ("Worst drop from peak", "max_drawdown", "{:.1%}"),
        ("Best 6 months", "best_6m", "{:.1%}"),
        ("Worst 6 months", "worst_6m", "{:.1%}"),
        ("6-month periods that doubled", "pct_6m_windows_doubled", "{:.1%}"),
    ]
    m = result.metrics()
    print(f"Backtest {result.equity.index[0].date()} to {result.equity.index[-1].date()}, ${initial:,.0f} start\n")
    print(f"{'':32}{'Steward':>14}{'Buy & hold ' + spy:>18}")
    for label, key, fmt in rows:
        print(f"{label:32}{fmt.format(m[key]):>14}{fmt.format(bench[key]):>18}")
    print(f"\nCircuit-breaker trips: {m['breaker_trips']}")


def _today_target(rules: dict, prices: pd.DataFrame, macro: dict):
    snap = build_snapshot(macro)
    regime = classify(snap, rules["regime"]["exposure_caps"])
    targets = combine(rules, prices)
    caps = pd.Series(regime.exposure_cap, index=targets.index[-1:])
    return snap, regime, combine(rules, prices, caps).iloc[-1]


def _portfolio(rules: dict) -> dict:
    """Live paper account when Alpaca keys are set, else paper/portfolio.json."""
    if AlpacaPaper.configured():
        b = AlpacaPaper()
        pos = b.positions()
        return {
            "cash": b.account().cash,
            "positions": {p.symbol: p.qty for p in pos},
            "prices": {p.symbol: p.current_price for p in pos},  # broker prices beat cached ones
        }
    return load_portfolio(starting_capital=rules["account"]["starting_capital"])


def cmd_report(rules: dict, args) -> None:
    prices = load_prices(_tickers(rules), refresh=args.refresh)
    snap, regime, target = _today_target(rules, prices, _macro(args.refresh))
    portfolio = _portfolio(rules)
    text = build_report(rules, prices, snap, regime, target, portfolio)
    from . import sleeves

    eq = sleeves.load_equity()
    if not eq.empty:
        latest = eq.ffill().iloc[-1]
        text += "\n## Sleeves\n\n| Sleeve | Value |\n|---|---|\n"
        text += "".join(f"| {k} | ${v:,.0f} |\n" for k, v in latest.items())
        text += "\n## Scorecard\n\n" + sleeves.scorecard_markdown(sleeves.score(eq), rules) + "\n"
    from datetime import date

    text += "\n## Taxes (if this were real money)\n\n" + tax_markdown(rules, date.today()) + "\n"
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(text)
    print(text)


def cmd_trade(rules: dict, args) -> None:
    from datetime import date

    from . import engine

    prices = load_prices(_tickers(rules), refresh=args.refresh)
    mom = engine.momentum_prices(rules, refresh=args.refresh)
    broker = AlpacaPaper()
    acct = broker.account()
    if acct.blocked:
        raise SystemExit("Alpaca reports the paper account is blocked; no orders sent.")
    if not args.dry_run and not broker.market_open():
        raise SystemExit("Market is closed; run during market hours so orders fill today.")
    out = engine.run(rules, broker, prices, mom, _macro(args.refresh), date.today(), args.dry_run)
    print(f"Account ${acct.equity:,.0f}; economy {out['regime']['name']} (cap {out['regime']['cap']:.0%}); "
          f"{'DRY RUN, ' if args.dry_run else ''}{len(out['orders'])} order(s)")
    for name, v in out["values"].items():
        print(f"  {name:9} ${v:>10,.0f}")
    for o in out["orders"]:
        print(f"  [{o['sleeve']}] {o['side']:4} {o['symbol']:5} ${o['dollars']:>9,.0f}  {o['status']:10} {o['reason']}")
    opt = out["options"]
    if opt and opt["new"]:
        n = opt["new"]
        print(f"  [options/{opt['mode']}] {n['underlying']} put spread {n['short_strike']:.0f}/{n['long_strike']:.0f} exp {n['expiry']}, "
              f"credit ${n['credit'] * 100:,.0f}, max loss ${n['max_loss']:,.0f}")
    for c in (opt or {}).get("closed", []):
        print(f"  [options] close {c['id']}: {c['reason']}")
    for r in out["realized"]:
        print(f"  [tax] {r['sleeve']} sold {r['qty']:g} {r['symbol']}: gain {r['gain']:+,.0f} "
              f"({'long' if r['long_term'] else 'short'}-term, {r['days_held']}d), est. tax ${r['est_tax']:,.0f}"
              + (" WASH-SALE RISK" if r['wash_sale_risk'] else ""))


def cmd_tax(rules: dict, args) -> None:
    from datetime import date

    from . import sleeves, tax

    print(tax_markdown(rules, date.today()))


def tax_markdown(rules: dict, today) -> str:
    from . import sleeves, tax

    ledger = sleeves.load_ledger(rules)
    prices = {}
    try:
        prices = {t: float(load_prices([t])[t].iloc[-1]) for sl in ledger.values() for t in sl["positions"]}
    except Exception:
        pass
    lots = [l for sl in ledger.values() for l in tax.lots_from(sl)]
    rows = tax.unrealized(lots, prices, today, rules)
    return tax.markdown(rules, tax.year_summary(tax.REALIZED_FILE, today.year), rows)


def cmd_scorecard(rules: dict, args) -> None:
    from . import sleeves

    eq = sleeves.load_equity()
    print(sleeves.scorecard_markdown(sleeves.score(eq), rules))


def cmd_dashboard(rules: dict, args) -> None:
    from . import dashboard

    path = dashboard.build(rules, Path(args.out) if args.out else dashboard.OUTPUT)
    print(f"Wrote {path}")


def cmd_schwab(rules: dict, args) -> None:
    """Weekly login, order preview from the latest plan, and approve-then-send."""
    import json

    from . import schwab

    cfg = rules.get("schwab", {})
    if args.action == "preview":
        pending = [i for i in schwab.load_preview() if i["status"] == "preview"]
        print(f"{len(pending)} order(s) awaiting approval in {schwab.PREVIEW_FILE}")
        for i in pending:
            print("  " + schwab.describe(i))
        return
    if args.action in ("login", "send") and not args.value:
        raise SystemExit(f"steward schwab {args.action} needs a value: "
                         + ("the URL you were redirected to" if args.action == "login" else "comma-separated preview ids"))
    client = schwab.Schwab(live=cfg.get("live", False), callback_url=cfg.get("callback_url", "https://127.0.0.1:8182"),
                           account_last4=str(cfg["account_last4"]) if cfg.get("account_last4") else None)
    if args.action == "login-url":
        print("Open this in a browser, approve, then run: steward schwab login <the URL you were redirected to>")
        print(client.login_url())
    elif args.action == "login":
        tok = client.exchange_code(args.value)
        print(f"Logged in. Refresh token good for {tok.refresh_days_left():.1f} days.")
    elif args.action == "status":
        tok = client._load_tokens()
        print(f"Token OK, {tok.refresh_days_left():.1f} days until the weekly login is needed.")
        a = client.account()
        print(f"Account equity ${a['equity']:,.0f}, cash ${a['cash']:,.0f}, positions {a['positions']}")
    elif args.action == "send":
        sent = client.send_approved([x.strip() for x in args.value.split(",")])
        print(f"Sent {len(sent)} order(s): {[x['id'] for x in sent]}")


def cmd_review(rules: dict, args) -> None:
    """Quarterly scorecard review: record who beat core and what the rules say."""
    from datetime import date

    from . import sleeves

    print(sleeves.run_review(rules, date.today()))


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(prog="steward", description="Rules-based, paper-trading-first investing.")
    p.add_argument("--rules", help="Path to rules.toml")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("fetch", help="Download prices and economic data")
    for name in ("regime", "backtest", "report", "trade", "brain", "scorecard", "dashboard", "tax", "review"):
        sp = sub.add_parser(name)
        sp.add_argument("--refresh", action="store_true", help="Re-download data first")
    sub.choices["backtest"].add_argument("--start", default="2004-01-01")
    sub.choices["backtest"].add_argument("--no-regime", action="store_true", help="Skip the economic-regime cap")
    sub.choices["report"].add_argument("--out", help="Also write the report to this file")
    sub.choices["trade"].add_argument("--dry-run", action="store_true", help="Plan orders but send nothing")
    sub.choices["dashboard"].add_argument("--out", help="Write the dashboard HTML here (default docs/index.html)")
    sw = sub.add_parser("schwab", help="Real-money path (preview mode by default)")
    sw.add_argument("action", choices=["login-url", "login", "status", "preview", "send"])
    sw.add_argument("value", nargs="?", help="Redirected URL for login; comma-separated preview ids for send")
    args = p.parse_args(argv)
    rules = load_rules(args.rules)
    {"fetch": cmd_fetch, "regime": cmd_regime, "backtest": cmd_backtest, "report": cmd_report, "trade": cmd_trade, "brain": cmd_brain,
     "scorecard": cmd_scorecard, "dashboard": cmd_dashboard, "tax": cmd_tax, "schwab": cmd_schwab,
     "review": cmd_review}[args.cmd](rules, args)


if __name__ == "__main__":
    main()
