# Findings

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

**Trade distribution, the plan's vehicle** (all three over the same window, 2018-09..2026-10, BTC on IBIT-hours bars; one position at a time, return per trade before stake sizing):

| | BTC (IBIT hours) | PPLT | IAU |
|---|---|---|---|
| Trades | 32 | 30 | 29 |
| Ended at the stop | 47% | 47% | 55% |
| Avg stopped loss | -6.2% | -3.4% | -2.0% |
| Win rate | 44% | 37% | 41% |
| Avg winner | +51.6% (median +17.5%) | +12.9% | +9.5% |
| Median trade | -3.1% | -2.1% | -1.2% |
| Best trade | +346% | +32% | +48% |
| Top 3 trades' share of total return | 87% | 104% | 94% |
| Top 5 | 109% | 141% | 117% |

BTC on IBIT-hours bars, 32 trades by return per trade:
```
<= -5%     12  ############
-5 to -3    4  ####
-3 to -1    2  ##
-1 to 0     0
0 to 2      2  ##
2 to 5      2  ##
5 to 10     1  #
10 to 20    2  ##
20 to 50    4  ####
> 50%       3  ###
```
18 of 32 trades lose money, 16 lose 3% or more, and 7 make 20% or more. In all three symbols the top 3 trades are about 90-100% of the total return, so the result rests on a handful of trends; with 30 trades per symbol, a different draw of 3 winners would move the pot a lot. The BTC stopped average is wide because 2018-2022 BTC had much larger ATRs; at today's ATR (about 2.6%) a 1.5 ATR stop is about -3.9%.

**Longer window for reference** (2015-06..2026-10, BTC on 24/7 bars, the earlier backtests):

| | BTC (24/7) | PPLT | IAU |
|---|---|---|---|
| Trades | 62 | 42 | 41 |
| Ended at the stop | 39% | 50% | 54% |
| Avg stopped loss | -6.0% | -3.0% | -1.9% |
| Win rate | 50% | 36% | 37% |
| Avg winner | +34.6% | +10.8% | +8.0% |
| Median trade | +0.1% | -1.8% | -1.2% |
| Best trade | +228% | +32% | +48% |
| Top 3 trades' share of total return | 47% | ~100% | 103% (top 5: 129%) |

BTC (24/7), 62 trades by return per trade:
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
(IAU on its 2005-18 training file only: 52 trades, 60% stopped, avg stop -2.2%, win 31%, avg winner +6.5%, median -1.5%, best +41%, top 3 over 100%. Same shape.) The 24/7 sample has twice the trades and a less concentrated top 3 (47%); the 2018+ ETF-hours sample is the harder, more concentrated one, and the one the plan trades.

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

Flat 25% of days; 1 open 43%, 2 open 25%, 3 open 6.5%. Run `pot_stake.py` with `--from 2018-09-01` for the ETF-hours file: with the default 2015-06 start BTC has no data for three years and the CAGR is diluted (+16.1% at 33% over 2015-06..2026-10, same -22.3% drawdown); that number is a window artifact, not a result. On the 24/7 BTC file the 2015-2026 pot is +26.5% / -23.9% at 33%. PPLT + IBIT alone at 33%: +20.1% / -21.8%, so IAU adds about 3 points. BTC is still most of the return. With the usual half haircut, about 11-12% a year.

Decision (RULES.md, 2026-10-24): the script pot trades IBIT instead of BTC-USD from 2026-10-26; same rules and stake. A Roth is the endgame vehicle (conversions fund it; trades are all short-term).


## Dollar P&L at the plan's sizing, bootstrap, and the third-symbol test (2026-10-24)
`research/dollar_sim.py`, `research/trade_bootstrap.py`. IAU + PPLT + IBIT-hours BTC, 2018-09..2026-10, 4 bps RT, $5,000 start, one position per symbol, marked to market daily.

| | Fixed $1,667 per trade | 1/3 of the pot at each entry, never trimmed (the plan) |
|---|---|---|
| Ends at | $18,011 (+17.0%/yr) | $36,416 (+27.6%/yr) |
| Max drawdown | -21.4% (-$1,961) | -23.6% (-$5,347) |
| IBIT (BTC) / IAU / PPLT P&L | +$10,270 / +$1,319 / +$1,422 | +$20,433 / +$6,116 / +$4,867 |

The plan sizes each trade at 1/3 of the pot's value at entry (capped at the cash on hand, no leverage) and never rebalances while held. That adds about 4 points a year over `pot_stake.py`'s daily rebalance to 1/3 (+27.6% vs +23.4%), because trimming sells the runners that carry the return. The cost is bigger single-day swings: worst day -13.9% on 2019-06-27, when the BTC runner (a $1,667 stake worth about $6,000 after a 250% run) lost 21.8% in a session. Planning number after a half haircut: about 13-14% a year.

**Bootstrap** (resample each symbol's trades with replacement, 20,000 redraws; preview on PPLT + IBIT-hours BTC, 33% per trade): plain replay +24.5%/yr; 5th / 25th / median / 75th / 95th percentile of an 8-year stretch +6.4% / +15.1% / +23.2% / +33.1% / +51.1%; 94% of redraws at or above +7%. Remove the best k trades in every symbol: k=1 +12.0%, k=2 +5.5%, k=3 +2.4%. The result rests on a handful of trends. The interval covers trade-draw luck only, not selection of the rules.

**Third-symbol test** (IAU + IBIT-hours BTC + one more, 1/3 at entry, ending value from $5,000): VGT $44,330 (+30.7%), SCHG $38,399, QQQ $37,056, PPLT $36,416 (+27.6%), VOO $32,458, IWM $32,330, TLT $28,995, none $29,335. Drawdowns -22% to -25% in all (BTC drives them). Differences among the top four are within noise (18-26 trades each) and VGT's 73% win rate is tech's 2019-2025 run. PPLT is gold's twin (daily correlation 0.61 with IAU vs 0.12-0.14 for the equity candidates), but the equity candidates are about 0.3 correlated with BTC; on the worst 5% IAU/BTC days PPLT averaged -1.6%, equities -0.9% to -1.2%, and only TLT held up (+0.1%) but the strategy loses money on TLT (-$1,112). Expense ratios: PPLT 0.60%, IAU 0.25%, QQQM 0.15%, VGT 0.09% (already in the ETF prices; a few hundredths of a point on the pot). Decision: keep PPLT for the first sample (no changes); a watch-only VGT or QQQM shadow symbol is an option later.

Oil (USO, BNO, Brent and WTI futures) and energy stocks (XLE) were also run, +0.3% to +3.4% a year at 33% on their own, and oil fell on the selloff days too (average -1.1% to -1.5%, up on 36-40%). Not trading it.


## Symbol screen in R, wider quiver, retest/bounce/dip side tests (2026-10-29)

**Trades in R** (`research/symbol_screen.py`; same breakout signals and plan exit, one position at a time, 2018-09..2026-10, R = trade return / (1.5 ATR at entry / entry open); null = random entries with the same exit and count, independent single trades, 300 draws):

| | n | /yr | Win | Mean R (5-95% bootstrap) | Median R | >=3R | >=5R | >=10R | Best R | Top-3 share | Skew | Null mean R (real pct) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| IBIT | 32 | 3.9 | 44% | +4.62 (+0.59..+9.79) | -0.75 | 25% | 12% | 9% | +88 | 83% | +4.2 | +3.38 (74th) |
| IAU | 29 | 3.6 | 41% | +2.16 (+0.18..+4.56) | -1.02 | 24% | 10% | 10% | +37 | 73% | +3.6 | +1.08 (90th) |
| PPLT | 30 | 3.7 | 37% | +0.93 (-0.06..+1.94) | -0.75 | 20% | 10% | 3% | +14 | 62% | +2.2 | +0.37 (88th) |
| VGT | 22 | 2.7 | 73% | +1.76 (+0.92..+2.65) | +1.56 | 27% | 18% | 0% | +6 | 39% | +0.4 | +0.45 (99th) |
| SCHG | 20 | 2.5 | 65% | +1.56 (+0.61..+2.54) | +0.83 | 30% | 10% | 0% | +8 | 50% | +0.9 | +0.46 (96th) |
| QQQ | 26 | 3.2 | 46% | +0.92 (+0.20..+1.70) | -0.21 | 23% | 12% | 0% | +6 | 48% | +1.0 | +0.53 (80th) |
| VOO | 18 | 2.2 | 56% | +0.57 (-0.09..+1.32) | +0.08 | 11% | 0% | 0% | +5 | 56% | +0.7 | +0.35 (67th) |
| VTI | 21 | 2.6 | 52% | +1.01 (+0.21..+1.82) | +0.03 | 24% | 0% | 0% | +5 | 46% | +0.6 | +0.25 (95th) |
| IWM | 25 | 3.1 | 52% | +0.31 (-0.19..+0.85) | +0.61 | 8% | 0% | 0% | +5 | 45% | +0.6 | +0.07 (75th) |
| TLT | 47 | 5.8 | 30% | -0.05 (-0.52..+0.52) | -1.02 | 9% | 4% | 2% | +12 | 69% | +3.6 | -0.17 (70th) |
| USO | 35 | 4.3 | 31% | +0.90 (-0.12..+2.14) | -1.01 | 14% | 9% | 3% | +22 | 67% | +3.5 | +0.58 (74th) |
| BNO | 30 | 3.7 | 40% | +1.37 (+0.09..+3.02) | -1.01 | 20% | 10% | 3% | +23 | 65% | +3.2 | +0.73 (87th) |
| XLE | 35 | 4.3 | 37% | +0.30 (-0.27..+0.90) | -1.01 | 9% | 3% | 0% | +8 | 54% | +1.9 | +0.00 (79th) |

- Two shapes. IBIT, IAU, PPLT and the oil names: median trade about -1R, skew +2 to +4, 10R+ trades exist; the mean sits in the right tail. VGT, SCHG, VTI, VOO, IWM: win 52-73%, median at or above 0, best trade 4.5-8R, skew under 1.
- The null here (independent random entries) includes the symbol's drift, so IBIT's real mean (+4.62R) is at the 74th percentile of a +3.38R null. It is a different null from the 98th-percentile figure earlier in this file (`pivot_line_breakouts.py`: same-count random entries in a one-position series), so the two percentiles are not comparable.

**Wider quiver at 1/N** (`research/dollar_sim.py`, 2018-09..2026-10, $5,000, stake = 1/N of the pot at entry, never trimmed, idle cash at 0%; the 13 are IAU, PPLT, IBIT, QQQ, VOO, VTI, VGT, SCHG, IWM, TLT, USO, BNO, XLE):

| Pot | Ends | CAGR | maxDD | ~Trades/yr |
|---|---|---|---|---|
| IAU + PPLT + IBIT, 33% (the plan) | $36,416 | +27.6% | -23.6% | |
| All 13, 1/13 each | $15,370 | +14.8% | -11.2% | 46 |
| 10 without oil, 1/10 | $14,935 | +14.4% | -12.3% | 33 |
| 12 without BTC, 1/12 | $10,732 | +9.8% | -7.5% | 42 |
| 12 without BTC, 1/6 / 1/4 | $16,461 / $17,102 | +15.8% / +16.3% | -13.6% / -14.6% | |
| IBIT alone, 33% / 50% / 100% of its pool | $22,793 / $39,584 / $130,751 | +20.5% / +28.9% / +49.3% | -26.2% / -33.2% / -46.9% | |
| IBIT + IAU + PPLT + VGT, 25% (4 slots) | $33,598 | +26.4% | -18.2% | |
| IBIT + IAU + PPLT + VGT, 33% (3 slots, first signal takes a free slot, order IBIT, IAU, PPLT, VGT) | $52,876 | +33.6% | -22.0% | |
| IAU + PPLT + VGT (no BTC), 33% / 25% | $12,795 / $10,263 | +12.2% / +9.2% | -14.0% / -11.4% | |

2022 P&L ($5,000 pot): plan -$3,429; all 13 -$534; 12 without BTC -$168 (1/12), -$34 (1/6), -$239 (1/4).

**Long history, 8 ETFs (QQQ, IWM, XLE, VTI, TLT, VGT, IAU, USO), 25% stake, 2000-01..2026-10:** +4.2% a year, maxDD -26.7% (12.5% stake: +3.3%, -17.0%). 2000-2018 total P&L +$108; 2019-2026 +$10,150. Bear years (stake 25%): 2000 -$598 (QQQ -36%), 2001 -$182 (-33%), 2002 -$394 (-37%), 2008 -$206 (-42%). Fewer symbols were listed in the early years.

**Entry-timing and other-strategy tests (all daily; tested, not adopted, scripts not kept):**
- Break-and-retest entry (wait up to K bars for a bar within 0.25-1 ATR of the line that closes above it, buy the next open; 189 signals, 2018-09+): a retest happens on 44-70% of signals; entry price vs immediate is about +0.1 ATR; stop rate on retest entries 53-63%; paired retest-minus-immediate mean -0.8% to -2.2% per trade (median about 0). Signals that never retest, bought immediately, average 2.5 to 10.6 pts per trade more (stratified permutation p 0.34 / 0.11 / 0.03 for bands 0.25 / 0.5 / 1.0 ATR; not corrected for the 9 variants).
- Support-bounce long (buy the confirmed 3rd touch of a rising support line, plan exit; 2015-06+): QQQ, VOO, VGT, SCHG, IWM, PPLT mean per trade +0.9% to -0.6%, below random entries with the same exit (5th-29th pct); TLT even (79th); IAU +1.8% (79th); BTC +32.7% from one +428% trade (94th), pot +5.6% a year.
- RSI(2) pullback in an uptrend (close > SMA200, RSI(2) < 10, buy next open, sell on the first close above SMA5 or after 10 bars, 2015-06+): VOO 99 trades, 72% win, +0.31% per trade, in market 15% of days, +2.6% a year, 98th pct of random uptrend days; QQQ 80th, VGT 91st, SCHG 96th, IWM 93rd; IAU 82nd (2005-15: 87th); PPLT 30th. VOO 2015-20 57th pct, 2021+ 99th. A 1.5 ATR stop lowers it.
- Daily return correlation 2018-09+: IAU-PPLT 0.61, IAU-IBIT 0.14, PPLT-IBIT 0.19.

## Monthly trend rule vs the daily breakout, two-pot blend, side tests (2026-11-01)

**Monthly rule** (`monthly_trend.py`): at each month-end close a symbol is ON if its close is above the mean of its last 10 month-end closes, else OFF; changes trade at the next open; ON symbols held at equal weight (1/N of the pot each, no leverage, no stop), OFF = cash at 0%; 2 bps per side. One spec, run once, nothing tuned. Daily breakout figures below are `dollar_sim`-style (stake = same weight, sized at entry, never trimmed, 4 bps RT, cash-capped). Same weights for both within each row.

| Sample | Weight each | Monthly rule CAGR / maxDD | Daily breakout CAGR / maxDD | Monthly state changes per year (round trips) |
|---|---|---|---|---|
| IBIT IAU PPLT, 2018-09..2026-10 | 33% | +22.3% / -25.4% | +27.6% / -23.6% | 2.9 |
| + VGT | 25% | +21.6% / -18.7% | +26.4% / -18.2% | 3.5 |
| + BNO (5 symbols) | 20% | +20.4% / -14.2% | +25.0% / -17.6% | 4.9 |
| 8 ETFs (QQQ IWM VTI XLE TLT VGT USO IAU), 2018-09..2026-10 | 12.5% | +9.7% / -11.0% | not run | 7.7 |
| 8 ETFs, 2000-01..2018-08 | 12.5% | +4.7% / -13.8% (+134% total) | +0.9% / -17.0% (+19% total) | |
| IAU VGT PPLT BNO (IBIT n/a), 2004-01..2018-08 | 25% | +2.3% / -22.8% | +1.2% / -17.3% | |
| 8 ETFs, 2000-01..2026-10 | 12.5% | +6.2% / -13.8% | +2.4% / -16.8% | 6.5 |

The 8-ETF long-history daily figure here (+2.4% at 12.5%) is from this run's simulation and differs slightly from the +3.3% in the long-history paragraph above, which came from an earlier run.

**Two $5,000 pots over 2018-09..2026-10** (A: daily breakout, 33%, 5 symbols; B: monthly rule, 1/5 each):

| | Ends | P&L | CAGR | maxDD | Worst day |
|---|---|---|---|---|---|
| A | $62,417 | +$57,417 | +36.4% | -24.5% | -13.4% |
| B | $22,662 | +$17,662 | +20.4% | -14.2% | -6.1% |
| A + B ($10,000) | $85,079 | +$75,079 | +30.1% | -20.5% | -10.0% |

Daily-return correlation A vs B 0.59. Combined drawdown peak 2021-11, trough 2023-03. 2022 P&L: A -$5,187, B +$264, combined -$4,923. P&L by symbol (A / B / combined): IBIT +$26.3k / +$7.2k / +$33.5k, VGT +$12.0k / +$3.0k / +$14.9k, IAU +$9.9k / +$2.2k / +$12.1k, BNO +$2.9k / +$4.4k / +$7.3k, PPLT +$6.3k / +$0.9k / +$7.2k. IBIT + IAU = 61% of combined P&L.

**Stake sweep and edge shrinkage** (5 symbols, 143 signals, `dollar_sim` mechanics, cash-capped):

| Stake | CAGR | maxDD | ln-growth/yr | Worst day |
|---|---|---|---|---|
| 20% | +25.0% | -17.6% | 0.247 | -10.1% |
| 25% | +29.5% | -20.8% | 0.287 | -11.5% |
| 33% | +36.3% | -24.5% | 0.343 | -13.4% |
| 50% | +49.5% | -30.1% | 0.446 | -16.5% |
| 60% | +49.7% | -29.9% | 0.447 | -18.0% |
| 100% | +44.9% | -38.3% | 0.411 | -21.8% |

Log growth peaks near 50-60% (cash-capped: above 33% the pot holds fewer, larger positions). With winning trades halved in size (losers unchanged): 33% +10.9% / -25.2%, 50% +16.6% / -30.6%; with winners at 30%: 33% +2.1% / -26.4%. Max drawdown moves little with stake or edge. Bootstrap (iid trades, ~18 a year, 33%): P(end below start) 6.3% at 1 year, 1.1% at 2, 0.3% at 3; the stake barely changes it between 25% and 50%.

**After a failed breakout** (previous trade on the same symbol ended in a stop-out vs a trail exit; R at 1.5 ATR; each trade tagged by the previous trade's exit type):

| Sample | After stop-out: n, mean R, win | After trail exit: n, mean R, win |
|---|---|---|
| 8 ETFs 2000-2026 (696 trades) | 351, +0.72, 40% | 337, +0.19, 34% |
| 5 symbols 2018-2026 (143 trades) | 68, +2.09, 44% | 70, +2.57, 49% |

Long-history difference +0.53R, permutation p = 0.005, positive on all 8 symbols (IAU +1.33, USO +0.81, QQQ +0.75, IWM +0.50, VTI +0.44, XLE +0.29, TLT +0.24, VGT +0.13). Not seen in the 2018-2026 set. One cell of many splits; not used in the rules, no log column added.

**Features of failed trades** (13 signal-bar features: touches, line length, slope, entry gap, breakout bar size, close and open above the line, ATR % of price, trend vs SMA50, 20-day momentum, distance from 252-day high, vol expansion, close position in bar; rank-normalised per symbol; discovery QQQ XLE TLT, 315 trades; validated on IWM VTI VGT USO IAU, 358 trades, and on the 2018-2026 five-symbol set): nothing predicts a stop-out (rate 49-51% in each sample). One feature, ATR % of price, relates to R (Spearman +0.15 discovery p 0.009, +0.17 held-out p 0.001, +0.11 five-symbol p 0.19), not to the stop-out rate. A first-pass hit on "distance above the line" was a look-ahead (it used the next day's open) and disappears when computed at the entry open.

**Tested, not adopted** (daily; scripts not kept): sweep-and-engulf long (a bar undercuts the prior 20-bar low and closes back above it, bullish engulfing within 2 bars, 1.5 ATR stop, swing-low trail): 5 symbols 2018-2026 n=32, win 22%, mean +0.16R, 21st percentile of random entries with the same exit; 8 ETFs 2000-2026 n=277, win 35%, mean +0.33R, PF 1.54, 87th percentile (random +0.17R).

**Update 2026-11-01: monthly pot held without rebalancing.** The monthly-rule rows above reset every ON symbol to a constant weight each day. The paper pot sizes each entry at 1/N of the pot and never trims, which gives different results on the same signals (5 symbols, 2018-09..2026-10, states through the September month-end):

| Monthly rule, 5 symbols | CAGR | maxDD | Worst day | Rebalance orders |
|---|---|---|---|---|
| 20% at entry, held, never trimmed | +25.1% | -30.3% | -9.1% | 0 |
| constant 20% (reset daily; table above) | +20.4% | -14.2% | -6.1% | |
| reset to 20% at each month-end open | +20.4% | -16.7% | | 286 |
| 33% at entry, ignoring collisions (avg 116% invested, max 186%) | +37.4% | -37.1% | -12.6% | 0 |
| 33% at entry, cash-capped (3 fill, priority IAU PPLT IBIT VGT BNO) | +30.4% | -38.9% | -9.8% | 0 |

Four or more symbols are ON on 54% of days. 8 ETFs at 12.5% at entry, never trimmed: 2018-09..2026-10 +10.9% / -14.4%; 2000..2026-10 +6.7% / -17.0%. Two $5,000 pots, A (daily breakout, 33%) + B (monthly, 20% at entry, never trimmed): $93,379, +31.6% a year, maxDD -22.9%, worst day -11.5%, daily correlation 0.62; P&L by year 2018 -$484, 2019 +$3,896, 2020 +$9,108, 2021 +$17,716, 2022 -$4,799, 2023 +$8,110, 2024 +$13,555, 2025 +$21,895, 2026 +$14,380.

Per round trip, 5 symbols 2018-09+, monthly rule vs daily breakout: trips 37 (4.5 a year) vs 143 (17.6); win 38% vs 45%; average win / loss +88% / -6.0% vs +21.4% / -3.7%; profit factor 9.0 vs 4.8; mean +29.7% vs +7.7%; median -3.0% vs -1.2%; top-3 trades' share of wins 68% vs 40%; best +432% vs +346%. Monthly rule on the 8 ETFs since 2000: 171 trips, win 42%, average win / loss +26% / -5.8%, PF 3.3, mean +7.7%, median -1.8%, top-3 share 17%.

**Early exits added to the monthly rule** (sell at the next open, re-enter only at the next month-end signal; constant-weight basis, CAGR / maxDD): daily close below the 10-month level, 5 symbols +16.9% / -16.0% (baseline +20.4% / -14.2%), 8 ETFs +5.2% / -12.6% (baseline +6.2% / -13.8%); 15% trailing stop +15.3% / -17.7% and +5.4% / -13.5%; 20% trailing stop +20.1% / -14.8% and +6.1% / -13.9%. Short round trips (two months or less, within +-3%) are 8% of trips.