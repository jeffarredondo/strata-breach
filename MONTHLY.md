# Monthly trend rule (parallel paper pot)

Separate from RULES.md and the daily scan. Own pot, own log, nothing shared with the line-breakout trades.

## Rule
- Symbols: IAU, PPLT, IBIT, VGT, BNO (same quiver as the scan).
- At each month-end close: a symbol is ON if its close is above the average of its last 10 month-end closes, otherwise OFF.
- A change takes effect at the next open: OFF to ON is a buy, ON to OFF is a sell. No other exits.
- Weight: each entry is sized at 1/N of the pot's value on the entry date (20% for 5 symbols) and held until that symbol's own exit. No leverage; if cash is short the entry is smaller. OFF symbols are cash. No rebalancing: a position is never added to.
- Trim: at each month-end close, if a held position is worth more than 30% of the pot, sell the excess at the next open to bring it back to 20% of the pot. The proceeds stay in cash (0% idle) until the next entry. A trim never closes the position and never changes its exit, which is still the symbol's own OFF signal.
- Start: the pot is flat from 2026-10-31 (`--flat-from`) and buys every symbol that is ON at the last month-end before that date (2026-10-30), at the next open (2026-11-02), the same way the backtest holds them. After that only state changes trade.
- Paper pot: $5,000 (same as the scan pot). Costs: 2 bps per side when logging paper fills.
- Rules are fixed (trim included, from 2026-11-03) for the same six-month sample as RULES.md (no parameter changes).

## Running it
```
python3 monthly_trend.py --log log/monthly_log.csv
```
Run after the close of the last trading day of the month. It uses completed months only, so on any other day it repeats the last month-end. Output is one line per symbol (month-end close, 10-month average, % gap, ON/OFF) and its pot status: ENTER at next open, HOLD since (entry open), EXIT at next open, or cash. WEIGHTS shows each held position's share of the model pot at that close. ACTIONS lists the pending ENTER, EXIT and TRIM (a TRIM line gives the share of the position to sell). The weights come from the model pot (every signal taken, 1/5 of the pot per entry), so they are close to your sheet but not identical; sell the percentage shown, rounded to whole shares. `--trim-above 0` turns the guidance off. Place the orders at the next open. `--asof YYYY-MM-DD` shows the state at an earlier month-end.

## Log
`log/monthly_log.csv` gets one row per symbol per month-end: Date, Symbol, Close, Avg, State. Re-runs do not duplicate rows. Paper fills (open price of the next trading day) and pot value are tracked in the sheet.

## What gets compared at six months
Pot value and drawdown, number of state changes, and fills vs the next open, side by side with the daily-scan pot over the same dates.

## Backtest (same rule, sized at 1/N of the pot at entry, 2 bps per side)
| Sample | Weight at entry | CAGR | Max DD | Round trips per year |
|---|---|---|---|---|
| 5 symbols, 2018-09 to 2026-10, with the trim rule (8 trims) | 20% | +22.5% | -18.4% | ~4.5 |
| same, never trimmed | 20% | +25.1% | -30.3% | ~4.5 |
| 8 ETFs (QQQ IWM VTI XLE TLT VGT USO IAU), 2018-09 to 2026-10 | 12.5% | +10.9% | -14.4% | |
| same 8 ETFs, 2000 to 2026-10 | 12.5% | +6.7% | -17.0% | ~6.4 |

The 8-ETF rows are the never-trimmed rule. For reference (not used): the same 5-symbol rule reset to a constant 20% each every day gave +20.4% / -14.2%; reset to 20% at each month-end open (trim and top up), +20.4% / -16.7% with 286 orders. The trim rule's other variants are in research/FINDINGS.md (2026-11-03). `research/backtest_monthly.csv` (the cone's baseline) was regenerated on 2026-11-03 under the trim rule; the never-trimmed version from 2026-11-01 is kept as `backtest_monthly_nottrimmed_2026-11-01.csv`.

Trim added 2026-11-03 at the user's decision, before any monthly exit or trim had occurred; the pot's three entries (IBIT, VGT, BNO, 2026-11-02) are unchanged.