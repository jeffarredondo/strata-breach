 Findings, condensed (2026-10-18)
Full running log with every side test: project doc `pivot_line_findings_2026-10-16.md` (archive). This is the part that matters.

## The system
Long only. Entry: a close above a falling resistance line (swing highs N=3, >=3 touches, wicks count, no close above it since the first anchor), buy next open. Exit: close at or below the highest confirmed swing low since entry (floor 1.5 ATR below entry). One position at a time.

## What held up
- **Beats random timing.** Swing-low trail, blended take-all, 2015-06..2026-10, vs random entries with the same exit and count (percentile): IAU 98, PPLT 98, BTC 100.
- **Trend exits beat a fixed target.** Fixed 1.5/3.5 ATR is the weakest exit (IAU 40th percentile). Swing-low, 9/21 cross-down and the broken-line exit let winners run; mean is carried by a few big trends, and win rate is 35-55%.
- **BTC edge is not just drift.** Swing-low trail: +67%/yr at 46% exposure vs +7% for random same-exit entries and +33% for exposure-matched buy & hold.

| One position, swing-low trail, 2015-2026 | IAU | PPLT | BTC |
|---|---|---|---|
| CAGR @100% stake / maxDD | +5.1% / -19% | +5.8% / -40% | +67.1% / -61% |
| CAGR @20% stake (the plan) / maxDD | +1.1% / -4% | +1.4% / -9% | +12.3% / -16% |
| Trades per year | 3.4 | 3.5 | 5.1 |
| Buy & hold CAGR / maxDD | +11.4% / -26% | +2.8% / -51% | +67.4% / -83% |
Three symbols at 20% each is about +15%/yr on the pot, roughly 80% of it BTC; gold plus platinum alone is about +2.5%. No fees.

## What did not hold up
- **Fresh 9/21 cross as a filter.** Strong on IAU train (+3.2%/trade), but in 2015-2026 it does nothing under fixed/ATR exits and only shows up under trend exits, resting on two trades. Not significant on PPLT; on BTC it helps only under the fixed target. Keep it as a log field, not a gate.
- **Entry filters, all null on IAU train:** closed above last lower high (wrong sign), volume (above-median did worse), volatility/squeeze, fair value gaps, box age, macro state (real rate / USD).
- **Other systems did worse:** vol-scaled momentum and MA crossovers did not beat exposure-matched buy & hold.
- **Regime:** gold's 2006-11 run vs 2012-18 chop flips nearly every result. Nothing here fixes that.

## Limits
- Return is capped by frequency, not trade quality: 3-5 trades a year per symbol on daily bars.
- All backtests are daily. IAU/PPLT on 4H is untested; the paper log is the test.
- Exploratory, not locked: many cells, no multiple-testing correction. IAU's 2015-2026 window overlaps its training file.

## Open questions
- Marginal breaks (close barely above the line) vs a close >= X ATR above it.
- Entering on a 9/21 cross within a few bars after the break, while price is still above the line.
- 4H vs daily on gold and platinum; IAU 2019-2026 on its own.
- 1.5 ATR stop vs close-based exits in live fills.
