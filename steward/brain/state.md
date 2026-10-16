# Steward brain

_Data section pending first automatic refresh (`python -m steward brain`). The hand-entered readings below are from research on 2026-10-16 and will be replaced by live FRED and market data on the first run._

## Regime: Expansion by the current rules, Late-cycle by judgment (see notes)

## Indicators (hand-entered 2026-10-16)

| Indicator | Reading | As of |
|---|---|---|
| Yield curve (10y-2y) | +0.33 pts | 2026-10-15 |
| High-yield spread | 3.25 pts | 2026-10-14 |
| Initial jobless claims | 199,000 (4-wk avg 198,500) | week of 2026-10-10 |
| Unemployment rate | 4.2% | Sept 2026 |
| CPI inflation (yoy) | 3.7% (core 2.6%) | Sept 2026 |
| Fed funds target | 3.75% to 4.00% | hiked +0.25 on 2026-09-16 |
| 3-month T-bill | about 4.7% | 2026-10-15 |
| 10-year Treasury | 5.10% | 2026-10-15 |

## Markets (hand-entered 2026-10-16)

- SPY about $770; up about 14% year to date, about 17% over 12 months with dividends.
- S&P 500 above its 200-day average since 2026-04-08.
- International developed stocks (EFA and peers) ahead of the S&P 500 for most of 2026.

<!-- NOTES:START -->

## Hand-kept notes (update each session)

### Current read, 2026-10-16

- Three of four model warning lights are green: curve positive, credit calm, jobs steady. The model says Expansion, 100% stock cap.
- The model's blind spot: inflation re-accelerated to 3.7% and the Fed is hiking into it (first hike since 2023). That is a classic late-cycle sign. Working judgment: treat as Late-cycle, 60% stock cap, until the model has an inflation/Fed rule.
- Market odds of another hike at the 2026-10-28 FOMC were about 40% after the September CPI print.
- Fed Chair Kevin Warsh declined to signal direction at the IMF meetings; defended the September hike.
- Gasoline prices tied to the Middle East conflict are the main driver of headline inflation.

### Upcoming dates to watch

- 2026-10-22: weekly jobless claims
- 2026-10-28: FOMC decision
- Early Nov 2026: October jobs report
- Mid Nov 2026: October CPI
- 2026-12-09: FOMC decision

### Rules of the game that changed

- The $25,000 pattern-day-trader minimum was eliminated (SEC approved 2026-04-14, effective 2026-06-04; brokers have until 2027-10-20 to implement). Not a constraint on this account anymore.

### Decisions log

- 2026-10-16: Starting capital set to $25,000 (was $20,000).
- 2026-10-16: DECIDED: start at the Late-cycle setting, 60% stocks. For the core sleeve that is about $4,500 SPY, $4,500 EFA, $6,000 cash/T-bills; momentum and options sleeves run their own rules.
- 2026-10-16: DECIDED and BUILT: inflation/Fed rule added to the regime model. CPI at or above 3% while the fed funds rate is up 0.20+ points over 6 months reads as Late-cycle. With today's data (CPI 3.7%, September hike) the model itself now says Late-cycle, so the 60% is a rule, not a judgment call.
- 2026-10-16: DECIDED: three sleeves, $15,000 core / $5,000 momentum stocks / $5,000 options (watch mode first). Quarterly scorecard moves capital; no switching on recent performance.
- 2026-10-16: Tax layer added. Ledger tracks lots and holding periods; every sell logs its estimated tax; routine rebalance sells wait up to 45 days for long-term status; stops never wait. Account type, brackets and lot method live in [tax] in rules.toml (placeholders until Jerry fills them in).
- Target return expectation on record: 12 to 25% a year with smaller drawdowns than buy-and-hold. Doubling every six months was judged unrealistic and is tracked only as a backtest statistic.

### Tax facts on file (2026, verified 2026-10-16)

- Long-term capital gains (held over 1 year): 0% up to $49,450 single / $98,900 joint taxable income; 15% to $545,500 / $613,700; 20% above. Short-term gains taxed as ordinary income.
- 3.8% Net Investment Income Tax above $200,000 single / $250,000 joint MAGI (not inflation-indexed).
- Standard deduction 2026: $16,100 single / $32,200 joint.
- IRA contribution limit 2026: $7,500, plus $1,100 catch-up at 50+. Roth phase-out: $153k to $168k single, $242k to $252k joint.
- Wash sale: loss disallowed if the same security is bought within 30 days either side. Does not apply in an IRA.
- Index options (SPX, XSP) are Section 1256: 60% long / 40% short regardless of holding period, no wash sales. SPY options are not. For real money the options sleeve should use XSP (one-tenth the size of SPX) instead of SPY.
- Open question for Jerry: which account type will hold real money (taxable, traditional IRA, Roth IRA)? This decides how much of the tax layer matters.

### Open items

- Create the private `steward` GitHub repo (user), then move the code from the TradingView backup branch.
- Open an Alpaca paper account, set to $25,000, add the two keys as repo secrets (user).
- First real-data backtest once data can be fetched (GitHub Actions can; the build sandbox cannot).

### Sources used on 2026-10-16

- FRED T10Y2Y, BAMLH0A0HYM2, ICSA, UNRATE
- FXStreet, Trading Economics (claims); The Hill, Kiplinger, Forbes (CPI and Fed); Schwab (FOMC vote)
- Advisor Perspectives (S&P trend); CNBC, Motley Fool (international vs U.S.)
- Federal Register 2026-07485 (pattern day trader rule)

<!-- NOTES:END -->
