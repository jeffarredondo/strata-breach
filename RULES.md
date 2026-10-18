# Rules, paper trading from Mon 2026-10-19 (updated 2026-10-18)

**Symbols / timeframes:** IAU 4H, PPLT 4H, BTCUSD 1D. Long only, no leverage.
**Pots:** two $5k paper pots, tracked by the `Pot` column in `log/trades.csv`: `you` (visual, discretionary) and `script` (whatever `scan.py` says, taken mechanically). $1,000 per trade (20%), max 3 open (one per symbol). Both pots start flat on 10/19; ignore the IAU "model position" that already existed on 10/16.

1. **Lines:** falling lines anchor on wicks, rising lines on candle bodies. Top-down from monthly to the trading timeframe. Marked at the end of a session, never during a trade.
2. **Entry:** a full bar closes above a falling line with >=3 touches; buy at the NEXT bar's open (log the fill versus that open). If the signal is missed, wait for the next one. No late entries (log as "late, not a signal" if taken anyway).
3. **Stop:** entry - 1.5 x ATR(14), stop-market GTC, set after the fill (placeholder until then). It is the loss limit, not the exit plan. BTC: optional wider disaster stop at fill - 2 ATR; the close-based rules do the work.
4. **Exit (script pot):** swing-low trail. Swing low = low below the 3 bars either side, confirmed 3 bars later. Trail = highest confirmed swing low since entry (floor: the 1.5 ATR stop). A bar closes at or below the trail -> sell at the next open. Max hold 120 bars.
5. **Exit (your pot):** your read of structure (HH/HL, LL/LH, lines). Log why when you differ from the script.
6. **Chart:** falling lines, 9/21, stop and trail levels, LL/LH levels. Supertrend removed. 9/21 fresh cross (EMA9 above EMA21 within the last 5 bars) is a log field only, not a gate.
7. **Log (`log/trades.csv`):** Pot, Symbol, TF, LineType, EntryTime, EntryPx, StopPx, Fresh921, ExitTime, ExitPx, ExitReason, RetPct, Label (up/down/chop), Notes. A signal you skip gets a row with ExitReason=SKIPPED and the reason in Notes. When your exit differs from the script's, put the script's exit date/price in Notes.
8. **Routine:** run `python3 scan.py` (or the GitHub Action) after the 4H close (~16:00 ET) for IAU/PPLT and after 00:00 UTC for BTC. Save the output. `--wicks` prints the touch points of a line; `--positions log/trades.csv` adds the readout for your own open trades.
9. **No parameter changes in the first sample.** If one changes, add a dated line below.

## Changes
- 2026-10-18: added PPLT and BTC; two pots; 1.5 ATR stop replaces the 1% stop (tighter than the tested floor on IAU 4H); swing-low trail is the script exit; scanner added.

## What is and isn't tested
- All backtests are on DAILY bars (IAU/PPLT 2015-2026, BTC 2015-2026). The scanner uses 4H for IAU/PPLT with the same parameters; that is untested and is what the paper log measures.
- Swing-low trail beat random entries with the same exit at the 98th percentile or better on all three. At a 20% stake: IAU +1.1%, PPLT +1.4%, BTC +12.3% a year on the pot (about +15% combined, ~80% of it BTC), max drawdowns -4%, -9%, -16%. Details in `research/FINDINGS.md`.
- Nulls on IAU train: volume, volatility, lower-high clear, fair value gaps add nothing as entry filters. The fresh 9/21 cross helped gold in training but did not hold under the fixed/ATR exits in 2015-2026.
