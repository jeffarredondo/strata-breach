# strata-breach

Long-only structural breakout system, daily bars, no leverage. Paper trading IAU, PPLT and IBIT (spot BTC ETF; BTC-USD until 2026-10-24) from 2026-10-19 for at least six months; VGT and BNO are also scanned and paper-traded when a slot is free. Learning project, not advice.

**The idea.** A falling resistance line drawn through at least three swing highs. A daily close above it is the entry (buy the next open). The exit is the first close at or below the highest confirmed swing low since entry, with a hard 1.5 ATR stop under the entry. Most trades are small stopped losses; a few runners pay for them.

## Rules in one screen
(full version and change log: `RULES.md`)

| | |
|---|---|
| Line | two confirmed N=3 swing highs in a 150-bar window, falling; touches = swing highs within 0.5 ATR of the line, at least 5 bars apart; no close above it since the first anchor; wick poke at most 1 ATR; >= 3 touches. The scanner picks the line with the most touches (ties: longest span) |
| Entry | first daily close above the line, buy the next open. A close within 0.1 ATR of the line is a touch, not a break (own pot only; the script pot takes every signal) |
| Stop | stop-market at fill - 1.5 ATR(14), set once, never moved |
| Exit | close at or below the highest confirmed swing low since entry (floor = the stop), sell the next open. No max hold; the scan flags a trade open more than 30 bars |
| Size | $1,667 per trade (33% of a $5k pot), max 3 open, one per symbol |
| Log fields | failed pokes and fresh 9/21 cross are logged, never gates |

Two paper pots: `you` (hand-drawn lines on TradingView) and `script` (whatever `scan.py` says, taken mechanically).

## Backtest headline
Swing-low trail + intraday 1.5 ATR stop, 33% stake, 4 bps round trip (details and caveats in `research/FINDINGS.md`):

| | CAGR | max DD |
|---|---|---|
| Pot at the plan's sizing (1/3 of the pot per trade, never trimmed), IAU + PPLT + IBIT-hours BTC, 2018-09..2026-10, $5,000 start | +27.6% (ends $36,416) | -23.6% |
| Same with the stake rebalanced to 1/3 every day (more cautious) | +23.4% | -22.3% |
| BTC alone, IBIT hours / 24-7 bars / spot at 150 bps | +16.1% / +14.6% / +11.7% | -17.4% / -18.4% / -21.3% |

BTC is most of the return; IAU and PPLT smooth it. Take about half of these as the realistic expectation (about 13-14% a year for the pot at the plan's sizing). 24/7 BTC over 2015-2026 at 33%: +21.2%.

## Layout
```
scan.py                 daily scanner: ENTRY / WATCH / MODEL position (HOLD or EXIT) per symbol, suggested 1.5 ATR stop
monthly_trend.py        separate parallel paper pot: month-end close vs 10-month average, ON/OFF per symbol, equal weight, trim guidance above 30% (see MONTHLY.md)
MONTHLY.md              rules and routine for monthly_trend.py
month_check.py          read-only monthly review: both pots replayed since their start dates, fills vs the model (--trades), each pot inside the backtest bootstrap cone
RULES.md                the rules being paper traded, change log
log/trades.csv          your trade log, one row per trade, Pot = you | script
log/scan_log.md         scanner output, one dated section per change (written by the Action)
my_trades.csv           open-trade file the Action reads (Symbol,TF,EntryTime,EntryPx[,ExitTime])
requirements.txt        pandas, numpy, yfinance
data/download.py        pulls daily OHLC from Yahoo into data/*.csv (not committed); download_4h.py for the 4H tests
.github/workflows/scan.yml   run scan.py on demand from the Actions tab
research/
  FINDINGS.md           everything tested, with numbers
  pivot_line_breakouts.py   the line finder + exit variants + random-entry null
  line3_explore.py          line>=3 breakout with the swing-low trail
  stop_poke_test.py         intraday stop variants, failed pokes, entry gap
  pot_stake.py              combines symbols into one pot at a given stake
  trade_dist.py             per-trade return distribution, top-3 share
  swing_n_test.py           swing size sweep (N = 1..7)
  marginal_break_test.py    closes within 0.1 ATR of the line
  build_etf_hours.py        rebuild BTC on IBIT trading hours from 24/7 hourly data
  backtest_trades.csv       the 143 backtest trades (5 symbols, 2018-09 to 2026-10) the cone is drawn from; backtest_monthly.csv is the monthly pot's backtest months (trim rule; the never-trimmed version is kept alongside)
  symbol_screen.py          trades in R per symbol: mean/median R, share reaching 3R/5R/10R, top-3 share, skew, random-entry null
```

## Use
```
pip install -r requirements.txt
python3 scan.py                                  # IAU, PPLT, IBIT, VGT, BNO, all daily; run after the 16:00 ET close
python3 scan.py --positions log/my_trades.csv    # also read your own open trades (rows with no ExitTime)
python3 scan.py --wicks                          # print the wicks each signal line goes through
python3 scan.py --log log/scan_log.csv           # append to a CSV log (no duplicates on re-run)
python3 scan.py --symbols IAU:1d,PPLT:1d,IBIT:1d,BTC-USD:1d    # add a symbol
python3 scan.py --csv data/btc.csv --label BTCUSD --tf 1d      # run on a local Date,Open,High,Low,Close file
python3 monthly_trend.py [--log log/monthly_log.csv]           # parallel monthly rule; run after the last close of each month
python3 month_check.py [--trades log/trades.csv --pot script]   # monthly review, read-only
```
The scan keeps no state. Every run replays the rules from `--flat-from 2026-10-19` over the last 400 bars (one position per symbol, entries at the next bar's open), which is how it knows the script's own position. `log/scan_log.md` is the record of what it said at the time; a rerun on revised data can rewrite past decisions by a cent.

Yahoo quirks the scanner handles: the newest daily bar is often missing or NaN after the close (rebuilt from hourly bars; the closes can differ from the official print by a few cents), and crypto hourly feeds can miss hours (bridged with the next bar's open).

Backtests:
```
python3 data/download.py
python3 research/stop_poke_test.py data/btc.csv --from 2015-06-01 --stake 0.33
python3 research/pot_stake.py data/iau.csv data/pplt.csv data/ibit_hours_2018_2026.csv --from 2018-09-01 --stakes 0.2,0.33
python3 research/build_etf_hours.py Bitstamp_BTCUSD_1h.csv data/ibit.csv   # writes btc_etfhours.csv
```
`scan.py` was checked against `line3_explore.py`: identical signals (BTC 156/156, IAU 83/83) and identical swing-trail exits.

## Monthly review
`python3 month_check.py [--trades your_export.csv --pot script]`, run at month-end after the scan and `monthly_trend.py`. Read-only.
- It replays both pots as if every signal were taken (daily pot from `--flat-from`, default 2026-10-19; monthly pot from `--monthly-from`, default 2026-10-31) and prints value, drawdown, closed and open trades, pending entries and exits, and win rate / average win / average loss / payoff / profit factor, cumulative since the start. The daily pot's backtest figures are printed beside its own.
- `--trades` takes your trade sheet exported as CSV (needs Symbol, EntryTime, EntryPx, ExitTime, ExitPx; a Pot column is optional, filter it with `--pot`). It prints the same metrics for your closed trades next to the model's, entries taken and missed, and fill slippage vs the model's next open in bps.
- Each pot's return is placed in a cone of bootstrap paths drawn from `research/backtest_trades.csv` and `research/backtest_monthly.csv`. Those two files are snapshots of the backtest (2018-09 to 2026-10) and are not updated; a new baseline gets a new file name and date. (`backtest_monthly.csv` was regenerated on 2026-11-03, before any monthly exit or trim, to match the monthly pot with its trim rule; the 2026-11-01 never-trimmed file is kept as `backtest_monthly_nottrimmed_2026-11-01.csv`.)
- The cone starts after about 3 months. Model fills are the next open at 2 bps per side, and the scan's trail is close-based, so intraday stop fills are not modeled.

## Status
Paper run in progress; no parameter changes in the first sample (RULES item 9). Execution vehicle (Roth IRA with IBIT is the likely end state) is parked until the six months are up.