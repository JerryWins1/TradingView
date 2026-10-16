# Steward

A rules-based, paper-trading-first investment system for a $20,000 account.
It reads the world economy once a week, sets target holdings from two
well-documented strategies, caps stock exposure when recession signs stack
up, enforces stop-losses and a drawdown circuit breaker, and sends a weekly
check-in as a GitHub issue (which arrives as an email).

> **Educational tool, not financial advice.** Nothing here moves real money.
> Past results, including any backtest, do not guarantee future returns.

## Goal, stated honestly

Doubling every six months compounds to about **+300% a year**, which would turn
$20,000 into about $20 million in five years. No public strategy, fund or
investor has done that repeatably. For comparison, Warren Buffett has
compounded at roughly 20% a year, and Renaissance's closed Medallion fund at
roughly 66% before fees. Steward's job is to **grow steadily and avoid the
large losses that wipe accounts out**. The backtest reports what share of
6-month windows doubled, so this claim is checked against data rather than
assumed.

## How it decides

| Layer | Rule | Source |
|---|---|---|
| Trend (50%) | Hold SPY while it is above its 10-month average, else cash | Meb Faber, *A Quantitative Approach to Tactical Asset Allocation* |
| Momentum (50%) | Each month hold the stronger of U.S. (SPY) or international (EFA) stocks if U.S. stocks beat cash over 12 months, else bonds (AGG) | Gary Antonacci, *Dual Momentum Investing* |
| Economy | Label the regime from the yield curve, credit spreads, jobless claims and the Sahm rule; cap stocks at 100 / 80 / 60 / 30% for Expansion / Recovery / Late-cycle / Contraction | FRED public data |
| Risk | 1% max risk per trade, 25% max position, 10% trailing stops, go to cash at -15% from peak until the next monthly signal | `rules.toml` |

Every number lives in [`rules.toml`](rules.toml).

## Run it

```bash
pip install -r requirements.txt
python -m steward fetch       # download prices (Stooq, or yfinance fallback) and FRED data
python -m steward regime      # today's economic regime and why
python -m steward backtest    # Steward vs buy-and-hold SPY since 2004 (incl. 2008, 2020, 2022)
python -m steward report      # the weekly check-in
python -m pytest              # tests
```

Your paper holdings live in `paper/portfolio.json` (`cash` plus `positions`
as shares). Update it when you place paper trades, and the report will show
the trades still needed and any stop that has been hit.

## Weekly check-in

`.github/workflows/weekly-report.yml` runs every Monday morning. It fetches
fresh data, builds the report and opens it as a GitHub issue, which GitHub
emails to you. You can also run it on demand from the Actions tab.

## Validation checklist, before any real money

1. Backtest: does Steward beat buy-and-hold SPY on risk (worst drop, worst
   6 months, Sharpe) across 2004 to today? Read the numbers, don't assume.
2. Change one rule at a time (e.g. 15% vs 20% breaker) and make sure results
   don't hinge on one lucky setting.
3. Paper-trade the weekly report for 3 to 6 months and follow it exactly.
4. Only then consider a small real-money start, increased gradually.

## Known limits

- Backtests use today's revised economic data, with publication delays applied.
- Trades fill at the close the day after a signal; real fills differ.
- Three liquid funds only, so no single-stock or options risk yet.
- No forecast is reliable; the regime label is a risk dial, not a prediction.

## Roadmap

- **Phase 1 (this):** rules, backtest, economy dashboard, weekly report.
- **Phase 2:** automatic paper trades through the Alpaca paper API, still
  with no real money.
- **Phase 3:** options overlay limited to covered calls and defined-risk
  spreads, paper only first.
- **Phase 4:** real-money mode, gated behind the validation checklist and your
  explicit approval of each order.
