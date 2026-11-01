#!/usr/bin/env python3
"""Monthly trend rule, run in parallel with scan.py (separate paper pot, not part of RULES.md).

RULE: at each month-end close, a symbol is ON if its close is above the average of its last 10 month-end closes, otherwise OFF.
      A change takes effect at the next open (buy or sell).  Each entry is sized at 1/N of the pot's value on the entry date and held until that symbol's own exit (no trimming, no rebalancing, no leverage); OFF symbols are cash.

    python3 monthly_trend.py                          # IAU, PPLT, IBIT, VGT, BNO, as of the last completed month-end
    python3 monthly_trend.py --log log/monthly_log.csv    # append one row per symbol per month-end (re-runs never duplicate)
    python3 monthly_trend.py --csv-dir data           # read SYMBOL.csv (Date,Open,High,Low,Close) from a folder instead of Yahoo
    python3 monthly_trend.py --flat-from 2026-10-31   # paper pot starts flat on this date (default) and buys what is ON at the last month-end before it
    python3 monthly_trend.py --asof 2026-09-30        # state as of an earlier month-end

Only completed months count.  The state changes once a month; running it on other days just repeats the last month-end.
"""
import argparse, os
import numpy as np, pandas as pd

ET = "America/New_York"
SYMBOLS = "IAU,PPLT,IBIT,VGT,BNO"
POT = 5000


def load(sym, csv_dir):
    if csv_dir:
        return pd.read_csv(os.path.join(csv_dir, f"{sym.lower()}.csv"), parse_dates=["Date"]).set_index("Date")[["Open", "Close"]].dropna()
    import yfinance as yf
    d = yf.Ticker(sym).history(period="max", interval="1d", auto_adjust=False)[["Open", "Close"]].dropna()
    if d.empty: raise SystemExit(f"{sym}: no data from Yahoo")
    d.index = d.index.tz_convert(ET).normalize().tz_localize(None)
    return d


def month_ends(c, now):
    """Month-end closes of completed months only: the latest month counts once we are in a later month, or its last weekday has closed."""
    ne = now.tz_convert(ET); closed_today = ne.hour >= 16 and ne.weekday() < 5
    if not closed_today and c.index[-1].date() == ne.date(): c = c[:-1]            # drop today's unfinished bar
    me = c.groupby([c.index.year, c.index.month]).tail(1)
    L = me.index[-1]; last_wd = (L + pd.offsets.MonthEnd(0)); last_wd = last_wd - pd.offsets.BDay(1) if last_wd.weekday() >= 5 else last_wd
    if (ne.year, ne.month) == (L.year, L.month) and L.date() < last_wd.date(): me = me[:-1]
    return me


def events(d, me, sma, flat_from):
    """Model pot, flat on flat_from: the first month-end on/before flat_from sets the starting state; after that every flip trades.
    Returns [(kind, bar index or None)] in order; kind is ENTER or EXIT, the bar is the first one after the month-end and on/after flat_from (None = not traded yet)."""
    on = (me > sma) & sma.notna(); dates = list(d.index); ev = []
    k0 = max([i for i, t in enumerate(me.index) if t <= flat_from] or [0]); prev = False
    for i in range(k0, len(me)):
        cur = bool(on.iloc[i])
        if cur != prev:
            j = next((j for j, t in enumerate(dates) if t > me.index[i] and t >= flat_from), None); ev.append(("ENTER" if cur else "EXIT", j)); prev = cur
    return ev


def replay(d, me, sma, flat_from):
    """Returns (ON now, status text, entry bar date or None)."""
    on = (me > sma) & sma.notna(); dates = list(d.index); ev = events(d, me, sma, flat_from)
    if not ev: return bool(on.iloc[-1]), "cash", None
    kind, j = ev[-1]
    if j is None: return bool(on.iloc[-1]), f"{kind} at next open", None
    if kind == "ENTER": return True, f"HOLD since {dates[j].date()} open {d['Open'].iloc[j]:,.2f}", dates[j]
    return False, f"cash (exited {dates[j].date()} open {d['Open'].iloc[j]:,.2f})", dates[j]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbols", default=SYMBOLS); ap.add_argument("--months", type=int, default=10)
    ap.add_argument("--csv-dir", default=None); ap.add_argument("--asof", default=None, help="state as of this month-end (YYYY-MM-DD)")
    ap.add_argument("--flat-from", default="2026-10-31", help="paper pot starts flat on this date and buys what is ON at the last month-end before it")
    ap.add_argument("--log", default=None, help="append one row per symbol per month-end to this CSV")
    a = ap.parse_args()
    syms = [x.strip().upper() for x in a.symbols.split(",")]; now = pd.Timestamp.now(tz="UTC"); w = 1 / len(syms); ff = pd.Timestamp(a.flat_from)
    rows = []
    for s in syms:
        d = load(s, a.csv_dir); c = d["Close"]
        if a.asof: c = c[c.index <= pd.Timestamp(a.asof)]; d = d.loc[c.index]; me = c.groupby([c.index.year, c.index.month]).tail(1)
        else: me = month_ends(c, now)
        sma = me.rolling(a.months).mean()
        if len(me) < a.months + 1: rows.append(dict(sym=s, note=f"needs {a.months + 1} month-ends, has {len(me)}")); continue
        on, status, _ = replay(d, me, sma, ff)
        rows.append(dict(sym=s, date=me.index[-1].date(), close=float(me.iloc[-1]), sma=float(sma.iloc[-1]), on=bool(me.iloc[-1] > sma.iloc[-1]), status=status))
    print(f"Monthly trend rule: close vs {a.months}-month average at the last completed month-end; weight {w:.0%} each (${POT * w:,.0f} of ${POT:,} paper pot); pot flat from {a.flat_from}\n")
    acts = []
    for r in rows:
        if "note" in r: print(f"{r['sym']:5s} {r['note']}"); continue
        print(f"{r['sym']:5s} {r['date']}  close {r['close']:>9,.2f}  avg {r['sma']:>9,.2f}  ({(r['close'] / r['sma'] - 1) * 100:+.1f}%)  {'ON ' if r['on'] else 'OFF'}  {r['status']}")
        if r["status"].startswith(("ENTER", "EXIT")): acts.append(f"{r['sym']}: {r['status']} (state as of {r['date']})")
    print("\nACTIONS\n  " + ("\n  ".join(acts) if acts else "none"))
    if a.log:
        os.makedirs(os.path.dirname(a.log) or ".", exist_ok=True)
        old = pd.read_csv(a.log) if os.path.exists(a.log) else pd.DataFrame(columns=["Date", "Symbol", "Close", "Avg", "State"])
        new = pd.DataFrame([dict(Date=str(r["date"]), Symbol=r["sym"], Close=round(r["close"], 4), Avg=round(r["sma"], 4), State="ON" if r["on"] else "OFF") for r in rows if "note" not in r])
        k = pd.concat([old, new]).drop_duplicates(["Date", "Symbol"], keep="first"); added = len(k) - len(old); k.to_csv(a.log, index=False)
        print(f"(log: {added} new row(s) -> {a.log})")
    print(f"(run {pd.Timestamp.now(tz=ET).strftime('%Y-%m-%d %H:%M ET')}; completed months only)")


if __name__ == "__main__":
    main()