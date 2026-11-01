# Monthly trend rule (parallel paper pot)

Separate from RULES.md and the daily scan. Own pot, own log, nothing shared with the line-breakout trades.

## Rule
- Symbols: IAU, PPLT, IBIT, VGT, BNO (same quiver as the scan).
- At each month-end close: a symbol is ON if its close is above the average of its last 10 month-end closes, otherwise OFF.
- A change takes effect at the next open: OFF to ON is a buy, ON to OFF is a sell. No other exits.
- Weight: each entry is sized at 1/N of the pot's value on the entry date (20% for 5 symbols) and held until that symbol's own exit. No trimming, no rebalancing, no leverage; if cash is short the entry is smaller. OFF symbols are cash.
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

## Backtest (same rule, sized at 1/N of the pot at entry and never rebalanced, 2 bps per side)
| Sample | Weight at entry | CAGR | Max DD | Round trips per year |
|---|---|---|---|---|
| 5 symbols, 2018-09 to 2026-10 | 20% | +25.1% | -30.3% | ~4.5 |
| 8 ETFs (QQQ IWM VTI XLE TLT VGT USO IAU), 2018-09 to 2026-10 | 12.5% | +10.9% | -14.4% | |
| same 8 ETFs, 2000 to 2026-10 | 12.5% | +6.7% | -17.0% | ~6.4 |

For reference (not used): the same 5-symbol rule reset to a constant 20% each every day gave +20.4% / -14.2%; reset to 20% at each month-end open, +20.4% / -16.7% with 286 trim and top-up orders. `research/backtest_monthly.csv` (the cone's baseline) was regenerated on 2026-11-01, before any paper results, under the never-rebalanced rule above.