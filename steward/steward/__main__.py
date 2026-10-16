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
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(text)
    print(text)


def cmd_trade(rules: dict, args) -> None:
    from datetime import date

    prices = load_prices(_tickers(rules), refresh=args.refresh)
    snap, regime, target = _today_target(rules, prices, _macro(args.refresh))
    broker = AlpacaPaper()
    acct = broker.account()
    if acct.blocked:
        raise SystemExit("Alpaca reports the paper account is blocked; no orders sent.")
    if not args.dry_run and not broker.market_open():
        raise SystemExit("Market is closed; run during market hours so orders fill today.")
    positions = {p.symbol: (p.market_value, p.current_price) for p in broker.positions()}
    state = tr.load_state()
    orders, state = tr.plan(target, acct.equity, positions, prices, rules, state, date.today())
    print(f"Paper equity ${acct.equity:,.0f}; economy {regime.name} (cap {regime.exposure_cap:.0%}); {len(orders)} order(s)")
    tr.execute(orders, broker, args.dry_run)
    for o in orders:
        print(f"  {o.side:4} {o.symbol:4} ${o.dollars:>9,.0f}  {o.status:10} {o.reason}")
    if not args.dry_run:
        tr.append_trades(orders)
        tr.save_state(state)


def cmd_brain(rules: dict, args) -> None:
    b = brain_mod.refresh(rules, args.refresh)
    print(f"Brain refreshed {b['updated']}: regime {b['regime']['name']} (cap {b['regime']['equity_cap']:.0%}); "
          f"trend {'on' if b['markets']['trend']['above_10m_average'] else 'off'}, momentum pick {b['markets']['momentum']['pick']}")
    print(f"Wrote {brain_mod.STATE_FILE} and {brain_mod.INDICATORS_FILE}")


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(prog="steward", description="Rules-based, paper-trading-first investing.")
    p.add_argument("--rules", help="Path to rules.toml")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("fetch", help="Download prices and economic data")
    for name in ("regime", "backtest", "report", "trade", "brain"):
        sp = sub.add_parser(name)
        sp.add_argument("--refresh", action="store_true", help="Re-download data first")
    sub.choices["backtest"].add_argument("--start", default="2004-01-01")
    sub.choices["backtest"].add_argument("--no-regime", action="store_true", help="Skip the economic-regime cap")
    sub.choices["report"].add_argument("--out", help="Also write the report to this file")
    sub.choices["trade"].add_argument("--dry-run", action="store_true", help="Plan orders but send nothing")
    args = p.parse_args(argv)
    rules = load_rules(args.rules)
    {"fetch": cmd_fetch, "regime": cmd_regime, "backtest": cmd_backtest, "report": cmd_report, "trade": cmd_trade, "brain": cmd_brain}[args.cmd](rules, args)


if __name__ == "__main__":
    main()
