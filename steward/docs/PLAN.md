# The Steward Investment Plan

*Version 2, October 17, 2026. Prepared for Jerry Winslow. Educational framework, not financial advice; every real-money decision is yours, and a CPA should see the tax parts.*

---

## 1. The ask, and what I changed about it

Your original request, in your words: research every online investing program and technique; find the top two for stocks, the top two for options, and the best overall system, platform and videos; build a dynamic plan to invest $20,000 and double it every six months; forecast the world economy; buy and sell when needed; stop-loss protection; weekly contact; study Charles Payne and the big investors; act like a top firm; be a pro.

Here is what a top firm would keep, and what it would change.

**Kept, and built:**
- Rules-based buying and selling, driven by a weekly read of the economy.
- Hard stop-losses on every position and a circuit breaker on the whole account.
- A weekly check-in, plus alerts whenever a stop fires or the economy label changes.
- Techniques copied from investors with public, audited track records.
- The most active, cheapest-to-trade markets: U.S. large caps, the big index funds, and index options.

**Changed:**
1. **The target.** Doubling every six months is +300% a year. No one with a public record has done it repeatedly: Warren Buffett compounded at about 20% a year for six decades; Renaissance's Medallion fund, the best record ever measured, did about 66% a year before fees and is closed to outsiders. Strategies that aim for 300% (short-dated options, heavy leverage) usually end in a wiped-out account. The target on record is **12% to 25% a year with smaller losses than the market**, and the system reports what share of six-month windows actually doubled so the original goal is measured, not assumed.
2. **The capital.** You later set it at **$25,000**; everything below uses that.
3. **"Forecast the economy."** Nobody forecasts the world economy reliably, including the Federal Reserve. What professionals do instead is read the backdrop and size risk to it. Steward labels the economy each week (Expansion, Recovery, Late-cycle, Contraction) from public data and dials stock exposure up or down accordingly.
4. **"Switch when we see a trend."** Chasing last month's winner is the single most reliable way retail investors lose. Steward runs three strategies side by side and moves money between them only by a quarterly rule.
5. **Taxes and the real account.** The original plan ignored them. Your real money will sit in a taxable Schwab account, so the system now tracks every lot, estimates the tax on every sale, and avoids short-term gains when waiting a few weeks turns them long-term.

Proverbs 21:5: "The plans of the diligent lead surely to abundance, but everyone who is hasty comes only to poverty." That verse is the design brief.

---

## 2. Research: what the best do, and what we take from each

### Stocks: the top two rules-based approaches

| Approach | Who | The rule | Public record | What we took |
|---|---|---|---|---|
| **Trend following** | Meb Faber, *A Quantitative Approach to Tactical Asset Allocation* (2007, updated 2013) | Hold an asset while it is above its 10-month moving average; otherwise hold cash | Across 100+ years and five asset classes it matched buy-and-hold returns with roughly half the worst drawdown | The core sleeve's trend half |
| **Dual momentum** | Gary Antonacci, *Dual Momentum Investing* (2014) | Each month, if U.S. stocks beat T-bills over 12 months, hold the stronger of U.S. or international stocks; otherwise hold bonds | 1974 to 2013: about 17% a year versus 12% for the S&P 500, with a worst drawdown of about 23% versus 51% | The core sleeve's momentum half |

Why these two: both are simple enough to write in one sentence, both are published with decades of out-of-sample data, and both make their money by **avoiding the big declines**, which is where compounding is won.

### Options: the top two defined-risk techniques

| Technique | Who | The rule | What we took |
|---|---|---|---|
| **Put credit spreads** | tastytrade (Tom Sosnoff) research, "trade small, trade often" | Sell a put about one standard deviation below the market, 30 to 45 days out, buy a cheaper put below it to cap the loss; take profit at 50% of the credit; cut at twice the credit | The options sleeve, exactly as written, in watch mode first |
| **Covered calls** | Standard institutional overlay (CBOE BXM index since 1986) | Sell calls against shares you already own for income | Deferred: with $25,000 you cannot own 100 shares of SPY (about $77,000). Revisit if the account grows or on cheaper underlyings |

### The top overall system

The strongest publicly documented system for an individual is **trend plus momentum with a risk dial**, which is what the core sleeve is. It appears in Faber's and Antonacci's work, in Ray Dalio's "All Weather" thinking (size to risk, not to conviction), and in the academic literature on time-series momentum (Moskowitz, Ooi and Pedersen, 2012). Nothing published beats it on the combination of simplicity, evidence and survivability.

### The big investors, and what each contributes

- **Warren Buffett:** "Rule one, never lose money." The circuit breaker and position limits come from him. His returns also set the honest ceiling: about 20% a year.
- **Ray Dalio:** economic regimes and sizing by risk. The four-regime dial is a simplified version of Bridgewater's framework.
- **Stanley Druckenmiller:** concentrate when the evidence is strongest, cut fast when wrong. The trailing stops and the momentum sleeve's "only positive momentum" rule.
- **Jim Simons (Renaissance):** rules over opinions, every decision logged and measured. The reason everything here is in `rules.toml` and every order carries its reason.
- **Charles Payne (Fox Business, *Making Money*):** a growth-oriented stock picker who focuses on catalysts and sentiment. He is a commentator, not a systematic manager, and publishes no audited record. We take his instinct for strong stocks and make it a rule: the momentum sleeve buys the strongest large caps by 12-month performance, refreshed monthly, with stops. That is "hot stocks" with discipline.
- **Peter Lynch:** know what you own. The dashboard shows every holding and the reason it was bought.

### Platforms

| Role | Choice | Why |
|---|---|---|
| Automated test lab | **Alpaca paper account** | Free, built for code, real market prices, stocks and options, fractional shares. Runs the three sleeves every Monday with no hand on the wheel |
| Real money (later) | **thinkorswim / Schwab**, which you already have | Best options tools of the group, trades XSP (tax-favored index options), offers IRAs, has an API for approve-then-send automation |
| Charts (optional) | TradingView | Beautiful charts, no execution path for our code |
| Skip | Robinhood | Weakest research and risk tools, nothing Schwab lacks |

### Education worth your time

Process-first sources, not prediction shows:

- **Meb Faber**, the original paper (free online) and his podcast on trend following.
- **Gary Antonacci**, *Dual Momentum Investing* (book) and his blog's monthly updates.
- **tastylive** (tastytrade's free education site): the "Options Crash Course" and their research segments on 45-day spreads and 50% profit-taking.
- **Schwab/thinkorswim Learning Center:** platform tutorials, paperMoney, trailing stops, OCO orders.
- **Ben Felix, "Common Sense Investing"** (YouTube): the clearest explanations of what the evidence does and does not support.
- **Charles Payne, *Making Money*** (Fox Business, weekdays): useful for market mood and catalysts; treat as input, never as a signal.

---

## 3. How the plan works

### 3.1 Three test beds in one paper account

| Sleeve | Capital | Strategy | Stops |
|---|---|---|---|
| **Core** | $15,000 | Faber trend (50%) + Antonacci dual momentum (50%) on SPY, EFA and AGG, capped by the economy dial | 10% trailing stops; account-wide 15% circuit breaker |
| **Momentum stocks** | $5,000 | The six strongest of 49 liquid large caps by 12-month return (skipping the latest month, per the research), equal weight, refreshed monthly, only if momentum is positive | 10% trailing stops; own 15% breaker |
| **Options income** | $5,000 | SPY put credit spreads, 30 to 45 days out, about 6% below the market, $5 wide, max loss $250 per spread, at most 3 open; profit at 50%, cut at 2x | Defined-risk by construction; starts in watch mode (logs, does not trade) |

**Capital moves only by rule.** Every 91 days each sleeve is scored on return, worst drop, Sharpe ratio and "versus core." A sleeve must beat core on risk-adjusted terms for two straight reviews to earn +25% capital; two straight misses cost 25%. No experimental sleeve ever exceeds half the account.

### 3.2 The economy dial (the "forecast")

Every Monday Steward reads five public series from the Federal Reserve's FRED database and labels the regime:

| Signal | Series | Warning when |
|---|---|---|
| Yield curve | 10-year minus 2-year Treasury | Inverted, or inverted within 24 months |
| Credit stress | High-yield bond spread | Above 6 points, or up 1.5 points in six months |
| Labor | Initial jobless claims | 4-week average up 20% from its 52-week low |
| Recession rule | Unemployment (Sahm rule) | 3-month average up 0.5 points from its 12-month low |
| Inflation squeeze | CPI and fed funds rate | Inflation at 3%+ while the Fed has raised rates 0.20+ points in six months |

| Regime | Stock cap | Today (Oct 17, 2026) |
|---|---|---|
| Expansion | 100% | |
| Recovery | 80% | |
| **Late-cycle** | **60%** | **Yes: CPI 3.7%, Fed hiked in September** |
| Contraction | 30% | |

So the first month's core allocation is about **$4,500 SPY, $4,500 EFA, $6,000 in cash earning T-bill rates (about 4.7%)**. Cash is not idle money this year.

### 3.3 Buying and selling

- Signals are computed from the last completed month-end and held all month, exactly as in the backtest.
- Trades happen on Mondays during market hours: circuit breaker first, then stops, then rebalancing, sells before buys, and only when a position is more than 5 points off target.
- Every order is logged with its reason. Nothing is ever placed without a reason you can read.

### 3.4 Protection

1. **Per position:** 10% trailing stop under the recent high.
2. **Per trade:** never more than 1% of the account at risk.
3. **Per sleeve:** at 15% below its peak, everything goes to cash until the next monthly signal.
4. **Per account:** no experimental sleeve above 50%; options max loss capped at $250 per spread.
5. **Structural:** the paper broker connection physically cannot reach a live account; the real-money adapter sends nothing until you approve each order by id.

### 3.5 Your weekly five minutes

Every Monday morning GitHub emails you the check-in: account value, the economy's dials and label, each sleeve's value and holdings, the orders placed and why, tax effects, and the brain's notes and upcoming dates. The dashboard shows the same at a glance on your phone. You also get word immediately when a stop fires, the breaker trips, or the regime changes.

When real money is involved, the Monday email becomes: log in to Schwab (their 7-day rule), review the preview orders, approve the ones you want. Five to ten minutes.

### 3.6 Taxes, because the account is taxable

- Every purchase is a tracked lot; every sale shows short- or long-term and estimated tax.
- Sales pick the highest-cost shares first to keep gains small.
- A routine rebalance sale waits up to 45 days if the shares are about to pass one year. **Stops never wait.**
- Buying back a losing position within 30 days is flagged (wash sale).
- For real money the options sleeve moves to **XSP** index options: 60% of gains taxed at the long-term rate regardless of holding period, no wash-sale rule.
- Standing recommendation: fund a **Roth IRA** at Schwab ($7,500 a year each, $8,600 at 50+) and run the most active sleeve inside it, where none of this tax friction exists.

---

## 4. What to expect, honestly

Projected outcomes for $25,000, based on the published records of the component strategies, not a promise:

| Scenario | Yearly return | Value after 1 year | After 3 years | Worst drop to expect |
|---|---|---|---|---|
| Bad year (2022-style) | -8% | $23,000 | | 15% (breaker) |
| Base case | +12% | $28,000 | $35,100 | 10% to 15% |
| Good case | +25% | $31,250 | $48,800 | 10% to 15% |
| Buy-and-hold S&P 500, for comparison | +10% average | $27,500 | $33,300 | 34% (2020), 51% (2008) |
| The original target | +300% | $100,000 | $6.4 million | Account wipe-out is the usual result |

The system's edge over simply holding the market is **smaller losses**, which compounds powerfully over years: a 50% loss needs a 100% gain to recover; a 15% loss needs 18%.

---

## 5. Validation: how we prove it before trusting it

1. **Backtest, 2004 to today,** on real data the first Monday the repo runs. Pass: Steward beats buy-and-hold SPY on worst drop, worst six months and Sharpe ratio across 2008, 2020 and 2022.
2. **Robustness:** change one rule at a time (10 vs 12-month lookback, 15 vs 20% breaker). Results must not hinge on one lucky number.
3. **Paper trading, three to six months,** all three sleeves, graded quarterly.
4. **Options:** at least one month watch-only, then paper trading, at least 40 completed spreads before judging.
5. **Real money only after all of the above,** starting small, through the approve-then-send path, with a $1-size test order first.

---

## 6. Roadmap

| Phase | Status | What |
|---|---|---|
| 1. Rules, backtest, economy dial, weekly report | Built | |
| 2. Automated paper trading, three sleeves, scorecard, dashboard, brain | Built | Starts the first Monday after Alpaca keys are in |
| 3. Options sleeve | Built, watch mode | Flip to trade after a month of sensible logs |
| 4. Tax layer | Built | Fill in your brackets privately |
| 5. Schwab adapter, preview mode | Built | Needs your developer-API approval, then a $1 test |
| 6. Quarterly reviews | Built | First one due 91 days after the first run |
| 7. Real money, approve-then-send | Not started | Gated on sections 5 and 6 |
| 8. Roth IRA sleeve, XSP options | Proposed | After real-money go-ahead |

---

## 7. What Jerry does (one-time, about 25 minutes total)

1. Give the Claude GitHub app access to the `steward` repo, so the code can move in.
2. Open the Alpaca paper account, set to $25,000, add the two keys as repo secrets.
3. Apply for Schwab developer API access (free; 1 to 3 business days).
4. Fill in `[tax]` in `rules.toml`.
5. Turn on GitHub Pages for the dashboard.

Full steps: `docs/SETUP.md`.

---

*Sources: Faber (2013), "A Quantitative Approach to Tactical Asset Allocation"; Antonacci (2014), Dual Momentum Investing; Moskowitz, Ooi & Pedersen (2012), "Time Series Momentum"; tastylive research on 45-DTE credit spreads; CBOE BXM methodology; FRED series T10Y2Y, BAMLH0A0HYM2, ICSA, UNRATE, CPIAUCSL, FEDFUNDS, DGS3MO; IRS Rev. Proc. 2025-32 and Notice 2025-67 (2026 tax figures); SEC approval of FINRA's pattern-day-trader rule change (2026). Berkshire Hathaway and Medallion figures from public reporting.*
