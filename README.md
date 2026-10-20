# strata-breach

Long-only structural breakout system: enter when price closes above a falling resistance line with >=3 swing-high touches, exit when a close breaks the highest confirmed swing low since entry. Paper trading IAU, PPLT and BTC (1D) from 2026-10-19.

```
scan.py                 daily scanner: ENTRY / WATCH / MODEL position (HOLD or EXIT) per symbol, suggested 1.5 ATR stop
RULES.md                the rules being paper traded, change log
log/trades.csv          trade log, one row per trade, Pot = you | script
research/               backtests: line3_explore.py, pivot_line_breakouts.py, FINDINGS.md
data/download.py        pulls daily OHLC from Yahoo into data/*.csv (not committed)
.github/workflows/scan.yml   run scan.py on demand from the Actions tab
```

## Use
```
pip install yfinance pandas numpy #or pip install -r requirements.txt
python3 scan.py                      # IAU 1D, PPLT 1D, BTC-USD 1D
python3 scan.py --wicks              # also print the wicks each signal line goes through
python3 scan.py --symbols IAU:4h,PPLT:4h,BTC-USD:1d,IAU:1d,PPLT:1d    # add daily shadows
python3 scan.py --positions log/trades.csv   # readout for your own open trades (rows with no ExitTime)

python3 data/download.py             # refresh the CSVs for the backtests
python3 research/line3_explore.py data/btc.csv --atr true --from 2015-06-01
```
`scan.py` was checked against `line3_explore.py`: identical signals (BTC 156/156, IAU 83/83) and identical swing-trail exits.
