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
- 2026-10-16: Proposed first allocation at the Late-cycle setting: about $7,500 SPY, $7,500 EFA, $10,000 T-bills. Awaiting decision between 60% (recommended) and the model's 100%.
- 2026-10-16: Proposed adding an inflation/Fed-hiking rule to the regime model. Not yet built; awaiting decision.
- Target return expectation on record: 12 to 25% a year with smaller drawdowns than buy-and-hold. Doubling every six months was judged unrealistic and is tracked only as a backtest statistic.

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
