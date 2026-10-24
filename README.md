# strata-breach

Long-only structural breakout system, daily bars, no leverage. Paper trading IAU, PPLT and IBIT (spot BTC ETF; BTC-USD until 2026-10-24) from 2026-10-19 for at least six months. Learning project, not advice.

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
| Pot (IAU + PPLT + BTC on IBIT-hours bars), 2018-09..2026-10 | +23.4% | -22.3% |
| Same, since 2024-11 | +27.3% | -11.5% |
| BTC alone, IBIT hours / 24-7 bars / spot at 150 bps | +16.1% / +14.6% / +11.7% | -17.4% / -18.4% / -21.3% |

BTC is most of the return; IAU and PPLT smooth it. Take about half of these as the realistic expectation (11-12% a year for the pot). 24/7 BTC over 2015-2026 at 33%: +21.2%.

## Layout
```
scan.py                 daily scanner: ENTRY / WATCH / MODEL position (HOLD or EXIT) per symbol, suggested 1.5 ATR stop
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
```

## Use
```
pip install -r requirements.txt
python3 scan.py                                  # IAU, PPLT, IBIT, all daily; run after the 16:00 ET close
python3 scan.py --positions log/my_trades.csv    # also read your own open trades (rows with no ExitTime)
python3 scan.py --wicks                          # print the wicks each signal line goes through
python3 scan.py --log log/scan_log.csv           # append to a CSV log (no duplicates on re-run)
python3 scan.py --symbols IAU:1d,PPLT:1d,IBIT:1d,BTC-USD:1d    # add a symbol
python3 scan.py --csv data/btc.csv --label BTCUSD --tf 1d      # run on a local Date,Open,High,Low,Close file
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

## Status
Paper run in progress; no parameter changes in the first sample (RULES item 9). Execution vehicle (Roth IRA with IBIT is the likely end state) is parked until the six months are up.