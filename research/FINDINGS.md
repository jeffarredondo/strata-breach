# Findings, condensed (updated 2026-10-24)
Full running log with every side test: project doc `pivot_line_findings_2026-10-16.md` (archive). This is the part that matters.

## The system
Long only. Entry: a close above a falling resistance line (swing highs N=3, >=3 touches, wicks count, no close above it since the first anchor), buy next open. Exit: close at or below the highest confirmed swing low since entry (floor: a 1.5 ATR stop-market under the entry, set once), sell the next open. No max hold. One position per symbol, 33% of the pot per trade (was 20%), max 3 open. Vehicle: IAU, PPLT, IBIT (spot BTC ETF) on weekday daily bars.

## What held up
- **Beats random timing.** Swing-low trail, blended take-all, 2015-06..2026-10, vs random entries with the same exit and count (percentile): IAU 98, PPLT 98, BTC 100.
- **Trend exits beat a fixed target.** Fixed 1.5/3.5 ATR is the weakest exit (IAU 40th percentile). Swing-low, 9/21 cross-down and the broken-line exit let winners run; mean is carried by a few big trends, and win rate is 35-55%.
- **BTC edge is not just drift.** Swing-low trail: +67%/yr at 46% exposure vs +7% for random same-exit entries and +33% for exposure-matched buy & hold.

| One position, swing-low trail, 2015-2026 | IAU | PPLT | BTC |
|---|---|---|---|
| CAGR @100% stake / maxDD | +5.1% / -19% | +5.8% / -40% | +67.1% / -61% |
| CAGR @20% stake (the old plan) / maxDD | +1.1% / -4% | +1.4% / -9% | +12.3% / -16% |
| CAGR @33% stake (the plan, intraday 1.5 ATR stop) / maxDD | +1.9% / -6% | +2.5% / -11% | +21.2% / -21% |
| Trades per year | 3.4 | 3.5 | 5.1 |
| Buy & hold CAGR / maxDD | +11.4% / -26% | +2.8% / -51% | +67.4% / -83% |
Three symbols at 20% each is about +15%/yr on the pot, roughly 80% of it BTC; gold plus platinum alone is about +2.5%. At 33% each (2015-2026, 4 bps round trip) the pot is +26.5% / maxDD -24%; on IBIT-hours bars 2018-09..2026-10 it is +23.4% / -22.3% (see the vehicle test). Take about half as the realistic number (11-12%/yr).

## What did not hold up
- **Fresh 9/21 cross as a filter.** Strong on IAU train (+3.2%/trade), but in 2015-2026 it does nothing under fixed/ATR exits and only shows up under trend exits, resting on two trades. Not significant on PPLT; on BTC it helps only under the fixed target. Keep it as a log field, not a gate.
- **Entry filters, all null on IAU train:** closed above last lower high (wrong sign), volume (above-median did worse), volatility/squeeze, fair value gaps, box age, macro state (real rate / USD).
- **Other systems did worse:** vol-scaled momentum and MA crossovers did not beat exposure-matched buy & hold.
- **Regime:** gold's 2006-11 run vs 2012-18 chop flips nearly every result. Nothing here fixes that.

## Limits
- Return is capped by frequency, not trade quality: 3-5 trades a year per symbol on daily bars.
- Backtests are daily. 4H was tested on 2024-11..2026-10 only (Yahoo keeps ~2 years of hourly bars), see below.
- Exploratory, not locked: many cells, no multiple-testing correction. IAU's 2015-2026 window overlaps its training file.

## Open questions
- Do the script's lines match the hand-drawn ones? Scanner touches are confirmed swing highs within 0.5 ATR; hand touches are any wick (any-wick touches double the signals and test worse). The two pots in the paper log answer it.
- Entering on a 9/21 cross within a few bars after the break, while price is still above the line.
- IAU 2019-2026 on its own.
- Vehicle: BTC moved to IBIT (weekday session bars) on 2026-10-24, see the vehicle test below; the real execution account (a Roth funded by conversions is the likely end state) is parked until the 6-month paper run is done. Also parked: 24/7 gold via PAXG-USD (Yahoo history from late 2019) as a test of gold without overnight gaps. Also GC=F (continuous gold futures, Yahoo from ~2000): same scripts, to see whether futures bars (about 23h session, 5pm ET settle) change the gold result; the earlier GC holdout only tested the fresh 9/21 cross on 2000-2005. If the pot ever gets large enough for micro futures (BTC 0.1 BTC, gold 10 oz), the same checks apply, plus rolls and holding full notional in cash for no leverage.
- 1.5 ATR stop vs close-based exits in live fills.

## 4H vs daily (2026-10-19, same window 2024-11-01..2026-10-16)
Swing-low trail, one position, CAGR @100% stake (maxDD). Daily wins on all three; 4H trades 3-6x as often with worse per-trade results.

| | 4H | Daily | Buy & hold |
|---|---|---|---|
| IAU | +8.7% (-17.7%) | +21.9% (-13.8%) | +23.5% (-26.3%) |
| PPLT | -9.4% (-24.2%) | +26.0% (-29.5%) | +28.0% (-44.9%) |
| BTC | -10.4% (-53%) | +11.8% (-20%) | +7.5% (-53%) |

At the 20% stake: IAU 4H +1.8 vs daily +4.3; PPLT 4H -1.7 vs daily +5.6; BTC 4H -1.7 vs daily +2.7. Random-entry percentile for the swing exit: daily 92-96 (IAU, PPLT), 4H 42-62. Small samples (4-20 trades per cell). Decision: all three on daily. In this window buy & hold beat the strategy on raw return for gold and platinum; the value there is drawdown and beating random timing.

## Intraday stop and failed pokes (2026-10-19, `research/stop_poke_test.py`, daily, 2015-06..2026-10)
Swing-low trail, one position at a time. Hard stop at entry - m x ATR as a stop-market (fires on the bar's low, gap fills at the open) vs close-based 1.5 ATR (the earlier tests).

| CAGR @100% / maxDD | close 1.5 ATR | intraday 1.5 | intraday 2 | intraday 3 | no hard stop |
|---|---|---|---|---|---|
| BTC | +67.1 / -61 | +69.7 / -53 | +67.8 / -57 | +63.4 / -62 | +65.6 / -52 |
| PPLT | +5.8 / -40 | +6.7 / -32 | +6.2 / -38 | +6.8 / -35 | +7.1 / -31 |
| IAU (2015-18 train only) | -1.7 / -12 | -1.2 / -12 | -1.2 / -11 | -0.6 / -13 | -1.2 / -15 |

The wick-triggered stop makes no real difference: trades it stops lose about the same as the close rule would have on the same entry (BTC -6.0% vs -5.6% at 1.5 ATR; PPLT -3.0% vs -3.0%). It trims drawdown a little, so keep it as insurance. Not a tuning lever.

Failed pokes (high above the falling line, close back under it) in the 10 or 20 bars before the break: no edge either way. BTC: with pokes +8.0% mean/trade vs +12.6% without (p=0.83 that pokes are better); PPLT: +1.0% vs +1.1%; IAU train: +0.05% vs -1.1% (n=15/10, p=0.13). A failed attempt neither raises nor lowers the odds of the next break. Keep it as a log field only.

Update 2026-10-22 on the full IAU file (2015-2026, 41 trades): >=1 failed poke in the last 10 bars averaged -0.18% per trade vs +2.44% with none (one-sided p~0.03). PPLT null; BTC the same direction, not significant. Still a log field (`Pokes10`), not a gate: it is one cell of many and the filter gives no CAGR lift.

## Marginal breaks (2026-10-20, `research/marginal_break_test.py`, daily, 3-touch lines, swing trail + intraday 1.5 ATR stop)
margin = (signal close - line) / ATR. Per signal, 2015-2026:

| margin (ATR) | BTC n / win / mean | PPLT n / win / mean |
|---|---|---|
| <= 0.10 | 31 / 36% / +3.1% | 11 / 9% / -2.1% |
| 0.10-0.25 | 32 / 56% / +9.2% | 23 / 26% / +1.5% |
| 0.25-0.50 | 37 / 60% / +17.5% | 23 / 35% / +1.6% |
| 0.50-1.00 | 32 / 41% / +10.0% | 22 / 32% / +2.2% |
| > 1.00 | 19 / 63% / +7.0% | 17 / 35% / +0.3% |

Barely-above (<= 0.1 ATR) is the worst bucket on both (>= 0.1 vs below: BTC +11.6% vs +3.1%, p=0.04; PPLT +1.5% vs -2.1%, p=0.045). Beyond 0.1 ATR no further pattern (BTC >= 0.5 ATR is not better). As a hard filter it does little: PPLT @20% +1.7% vs +1.6% with shallower drawdown; BTC +11.4% vs +12.6% (six fewer trades). IAU 2015-18 has too few signals to say. Verdict: a close within 0.1 ATR of the line is a touch, not a break; log the margin, no rule change.

IAU 2015-2026 (75 signals) agrees in direction, not significant: margin <= 0.10 ATR n=19, win 32%, mean +0.24% vs +1.39% for >= 0.10 (p=0.30). Filtering by margin does not lift CAGR at 20% (+1.2% all, +1.2% / +1.1% / +1.0% at >= 0.10 / 0.25 / 0.50 ATR) and deepens maxDD at 0.25 (-5.4% vs -3.5%). Same three-symbol verdict: log the margin, no filter.


## Exit, size and distribution tests (2026-10-21..23; daily, 2015-2026, intraday 1.5 ATR stop + swing-low trail, 33% stake, 4 bps RT unless noted)
`research/trade_dist.py`, `research/swing_n_test.py`, `research/stop_poke_test.py`.

**Trade distribution** (all three over the same window, 2015-06..2026-10; one position at a time, return per trade before stake sizing):

| | BTC | PPLT | IAU |
|---|---|---|---|
| Trades | 62 | 42 | 41 |
| Ended at the stop | 39% | 50% | 54% |
| Avg stopped loss | -6.0% (today's stop about -3.7%) | -3.0% | -1.9% |
| Win rate | 50% | 36% | 37% |
| Avg winner | +34.6% | +10.8% | +8.0% |
| Median trade | +0.1% | -1.8% | -1.2% |
| Best trade | +228% | +32% | +48% |
| Top 3 trades' share of total return | 47% | ~100% | 103% (top 5: 129%) |

(IAU on its 2005-18 training file only, for reference: 52 trades, 60% stopped, avg stop -2.2%, win 31%, avg winner +6.5%, median -1.5%, best +41%, top 3 over 100%. Same shape.)

BTC, 62 trades by return per trade (2015-2026, plan rules):
```
<= -5%     16  ################
-5 to -3   12  ############
-3 to -1    2  ##
-1 to 0     1  #
0 to 2      4  ####
2 to 5      4  ####
5 to 10     4  ####
10 to 20    4  ####
20 to 50   11  ###########
> 50%       4  ####
```
Two clumps: 28 trades (45%) lose 3% or more, and 15 trades (24%) make 20% or more. The middle is thin, which is what a stop plus a trend trail produces. Half the trades lose money (31 of 62) and 8 more make under 5%; the right clump pays for everything.

Holds: stopped trades 7-9 bars, winners about 48 bars, all trades 24-30 bars. Expect about 40% of BTC trades to be small stopped losses; the winners carry it.

**Pot at 33% (2015-2026):** pot +26.5% / maxDD -23.9%; BTC +21.2% / -21.3%; PPLT +2.5% / -11.2%; IAU +1.9% / -5.8%. BTC cost sensitivity at 33%: 4 / 50 / 100 / 150 bps round trip give +21.2 / +20.2 / +19.1 / +18.1%.

**Swing size N** (BTC CAGR @33%): N=1 +14.1, 2 +17.1, 3 +21.2, 4 +25.1, 5 +23.3, 7 +22.7; PPLT and IAU flat across N. N=3 kept (best on all three together, the N=4-7 gain on BTC looks like noise and the first sample takes no parameter changes).

**Exit variants** (BTC CAGR @33% / maxDD, 2015-2026):
- Chandelier 1.5 ATR from the highest close: +9.1% vs +21.7% for the swing trail. Hybrids (swing trail plus chandelier 2.5 / 3 / 4 ATR): +12.9 / +12.9 / +15.0%. Both hurt.
- Exit on a close back under the broken line: BTC +23.7 vs +21.7, PPLT +1.3 vs +2.6, IAU +0.1 vs +1.0. Mixed, no change.
- No trail (1.5 ATR stop, 120-bar cap): BTC +23.9% / -24.2% vs +21.2% / -21.3% for the swing trail, but win rate 30% vs 50% on 43 vs 62 trades and the cap binds. A stop-and-hold is not distinguishable from the swing trail on BTC; the trail gives the better win rate and slightly shallower drawdown. No stop and no trail (120-bar hold): +19.0% / -41.5%.
- IAU: a no-trail hold beat the swing trail (+8.5% vs +5.5% CAGR @100%): gold's drift. No symbol-specific exits; same rules for every symbol.
- The 120-bar cap never fired on BTC or PPLT (identical results) and clipped one IAU trade; removed. Trades open more than 30 bars are flagged by the scan for a manual keep-or-end decision.

**Entry details:**
- Gap at the entry open (open vs prior close in ATR): no effect on IAU or PPLT; skipping gap-downs does not help. (BTC's gaps are about zero on 24/7 bars.)
- Any-wick touches (any bar whose high is near the line, not only confirmed pivots) double the signal count and test worse.
- After a -2.5% IAU day (4-6 per year in the 2005-18 history): no reliable bounce or continuation. IAU overnight +10.2%/yr vs intraday -2.1%/yr (2005-18); intraday-only gold is not a thing here.
- Fresh 9/21 cross holdout, IAU 2019-20: inconclusive (n=7). Stays a log field.

## BTC on a spot-ETF (IBIT hours): vehicle test, 2026-10-24

Question: BTC trades 24/7, but an ETF only has weekday sessions and market-hours stops. Does that break the strategy, and what do exchange fees cost?

Method (`research/build_etf_hours.py`): rebuild BTC as IBIT would have printed it from Bitstamp hourly (2018-05..2026-10): open = BTC at 9:30 ET, close = 16:00 ET (13:00 on early closes), NYSE calendar, high/low from the session's hourly bars, no weekend bars. Same rules run on those bars (signals on the 4pm close, next-open entry, in-session stop-market with gap fills at the open, swing-low trail). Validated against real IBIT 2024-01..2026-10: close-to-close corr 0.9989 (8 bps typical error), overnight/weekend gap distribution matches (mean abs 167 vs 168 bps; 5th pct -3.1% vs -3.0%), intraday range 98% of real. The open is the loosest piece (47 bps typical error, the 9:30 auction print).

BTC alone, 33% stake, 2018-09..2026-10 (`research/stop_poke_test.py`):

| Bars / cost | Stop | CAGR | maxDD |
|---|---|---|---|
| 24/7, 4 bps | intraday | +14.6% | -18.4% |
| 24/7, 150 bps RT (Schwab spot at 75 bps/side) | intraday | +11.7% | -21.3% |
| ETF hours, 4 bps | in-session stop | +16.1% | -17.4% |
| ETF hours, 4 bps | checked at the close only | +16.1% | -18.7% |
| ETF hours, 4 bps | no stop | +12.5% | -29.5% |

- A market-hours stop does as well as a 24h stop; overnight and weekend gaps are already in the bars. The stop itself still matters on ETF bars (no stop: maxDD -29.5%).
- Fees: Coinbase Advanced at the entry tier is 0.90% taker (about 180 bps RT); Schwab spot about 75 bps per transaction. The ETF saves about 4 points a year vs 150 bps. IBIT's 0.25% expense ratio (about 0.1 pt/yr while invested) is not modelled.
- Samples are about 30 trades per row, so ETF vs 24/7 is within noise; the conclusion is "not worse". The +21.2% quoted for 24/7 BTC on 2015-2026 is the longer window (includes 2015-17), not a different strategy.

Whole pot (IAU + PPLT + BTC on IBIT-hours bars, one position per symbol, `research/pot_stake.py`, 2018-09..2026-10, 4 bps):

| Stake per trade | Pot CAGR | maxDD | Since 2024-11 |
|---|---|---|---|
| 20% | +14.0% | -14.0% | +16.1% / -7.0% |
| 33% | +23.4% | -22.3% | +27.3% / -11.5% |

Flat 25% of days; 1 open 43%, 2 open 25%, 3 open 6.5%. PPLT + IBIT alone at 33%: +20.1% / -21.8%, so IAU adds about 3 points. BTC is still most of the return. With the usual half haircut, about 11-12% a year.

Decision (RULES.md, 2026-10-24): the script pot trades IBIT instead of BTC-USD from 2026-10-26; same rules and stake. A Roth is the endgame vehicle (conversions fund it; trades are all short-term).