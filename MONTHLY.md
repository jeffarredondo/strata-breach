# Monthly trend rule (parallel paper pot)

Separate from RULES.md and the daily scan. Own pot, own log, nothing shared with the line-breakout trades.

## Rule
- Symbols: IAU, PPLT, IBIT, VGT, BNO (same quiver as the scan).
- At each month-end close: a symbol is ON if its close is above the average of its last 10 month-end closes, otherwise OFF.
- A change takes effect at the next open: OFF to ON is a buy, ON to OFF is a sell. No other exits.
- Weight: equal, 1/N of the pot per symbol (20% each for 5 symbols). ON symbols are held, OFF symbols are cash. No leverage, no rebalancing between month-ends.
- Start: the pot is flat from 2026-10-31 (`--flat-from`) and buys every symbol that is ON at the last month-end before that date (2026-10-30), at the next open (2026-11-02), the same way the backtest holds them. After that only state changes trade.
- Paper pot: $5,000 (same as the scan pot). Costs: 2 bps per side when logging paper fills.
- Rules are fixed for the same six-month sample as RULES.md (no parameter changes).

## Running it
```
python3 monthly_trend.py --log log/monthly_log.csv
```
Run after the close of the last trading day of the month. It uses completed months only, so on any other day it repeats the last month-end. Output is one line per symbol (month-end close, 10-month average, % gap, ON/OFF) and its pot status: ENTER at next open, HOLD since (entry open), EXIT at next open, or cash. ACTIONS lists the pending ENTER and EXIT. Place the orders at the next open. `--asof YYYY-MM-DD` shows the state at an earlier month-end.

## Log
`log/monthly_log.csv` gets one row per symbol per month-end: Date, Symbol, Close, Avg, State. Re-runs do not duplicate rows. Paper fills (open price of the next trading day) and pot value are tracked in the sheet.

## What gets compared at six months
Pot value and drawdown, number of state changes, and fills vs the next open, side by side with the daily-scan pot over the same dates.

## Backtest (same rule, 1/N, no leverage, 2 bps per side)
| Sample | Weight each | CAGR | Max DD | State changes (round trips) per year |
|---|---|---|---|---|
| 5 symbols, 2018-09 to 2026-10 | 20% | +20.4% | -14.2% | ~4.9 |
| 8 ETFs (QQQ IWM VTI XLE TLT VGT USO IAU), 2000 to 2026-10 | 12.5% | +6.2% | -13.8% | ~6.5 |