#!/usr/bin/env python3
"""Monthly trend rule, run in parallel with scan.py (separate paper pot, not part of RULES.md).

RULE: at each month-end close, a symbol is ON if its close is above the average of its last 10 month-end closes, otherwise OFF.
      A change takes effect at the next open (buy or sell).  Each entry is sized at 1/N of the pot's value on the entry date and held until that symbol's own exit (no leverage); OFF symbols are cash.
TRIM: at each month-end close, if a held position is worth more than 30% of the pot, sell the excess at the next open to bring it back to 20% of the pot (cash stays idle).  Never add to a position.

    python3 monthly_trend.py                          # IAU, PPLT, IBIT, VGT, BNO, as of the last completed month-end
    python3 monthly_trend.py --log log/monthly_log.csv    # append one row per symbol per month-end (re-runs never duplicate)
    python3 monthly_trend.py --csv-dir data           # read SYMBOL.csv (Date,Open,High,Low,Close) from a folder instead of Yahoo
    python3 monthly_trend.py --flat-from 2026-10-31   # paper pot starts flat on this date (default) and buys what is ON at the last month-end before it
    python3 monthly_trend.py --asof 2026-09-30        # state as of an earlier month-end
    python3 monthly_trend.py --trim-above 0           # no trim guidance (position weights are still shown)

Only completed months count.  The state changes once a month; running it on other days just repeats the last month-end.
"""
import argparse, os
import numpy as np, pandas as pd

ET = "America/New_York"
SYMBOLS = "IAU,PPLT,IBIT,VGT,BNO"
POT = 5000
COST = 2e-4
TRIM_ABOVE = 0.30   # a held position worth more than this share of the pot gets trimmed at the next open ...
TRIM_TO = 0.20      # ... back to this share (the 1/N entry weight for 5 symbols)


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


def model_pot(D, flat_from, now, months=10, trim_above=TRIM_ABOVE, trim_to=TRIM_TO, asof=None, pot0=POT):
    """Model of the paper pot: every signal taken, entry = pot value / N at the next open, exit at the next open, 2 bps per side, and the trim rule (weights checked at each month-end close,
    trim at the next open, positions only ever sold down).  D: {symbol: DataFrame(Open, Close)}.  Returns value, daily curve, holdings with weights at the last close,
    pending ENTER/EXIT/TRIM at the next open, closed round trips (% per full exit, trims excluded) and the number of trims."""
    N = len(D); cash, pos, prev, curve, ev, done, ntrim = pot0, {}, pot0, [], {}, [], 0
    for sym, d in D.items():
        c = d["Close"]
        if asof: c = c[c.index <= pd.Timestamp(asof)]; d = d.loc[c.index]; me = c.groupby([c.index.year, c.index.month]).tail(1)
        else: me = month_ends(c, now)
        ev[sym] = (d, events(d, me, me.rolling(months).mean(), flat_from) if len(me) > months else [])
    ref = max((d for d, _ in ev.values()), key=len); rc = ref["Close"]
    mes = set(month_ends(rc, now).index if not asof else rc[rc.index <= pd.Timestamp(asof)].groupby([rc[rc.index <= pd.Timestamp(asof)].index.year, rc[rc.index <= pd.Timestamp(asof)].index.month]).tail(1).index)
    dates = sorted({t for d, _ in ev.values() for t in d.index if t >= flat_from}); cl = {k: d["Close"].reindex(dates).ffill() for k, (d, _) in ev.items()}
    act = {(sym, d.index[j]): k for sym, (d, e) in ev.items() for k, j in e if j is not None}
    check = False; weights = {}
    for dt in dates:
        for sym in D:
            if act.get((sym, dt)) == "EXIT" and sym in pos: p = pos.pop(sym); px = D[sym].loc[dt, "Open"] * (1 - COST); cash += p["sh"] * px; done.append((px / p["px"] - 1) * 100)
        for sym in D:
            if act.get((sym, dt)) == "ENTER" and sym not in pos:
                stake = min(prev / N, cash)
                if stake > 0: px = D[sym].loc[dt, "Open"] * (1 + COST); cash -= stake; pos[sym] = dict(sh=stake / px, stake=stake, px=px)
        if check and trim_above > 0 and pos:
            eq0 = cash + sum(p["sh"] * D[s].loc[dt, "Open"] for s, p in pos.items())
            for sym, p in pos.items():
                v = p["sh"] * D[sym].loc[dt, "Open"]
                if v > trim_above * eq0: sell = v - trim_to * eq0; p["sh"] -= sell / D[sym].loc[dt, "Open"]; cash += sell * (1 - COST); ntrim += 1
        check = False
        eq = cash + sum(p["sh"] * cl[sym][dt] for sym, p in pos.items()); curve.append(eq); prev = eq
        weights = {sym: p["sh"] * cl[sym][dt] / eq for sym, p in pos.items()} if eq else {}
        if dt in mes and trim_above > 0 and any(w > trim_above for w in weights.values()): check = True
    pend = [f"{k} {sym}" for sym, (d, e) in ev.items() for k, j in e if j is None]
    trims = {sym: 1 - trim_to / w for sym, w in weights.items() if check and w > trim_above}
    return dict(dates=dates, curve=curve, pos=pos, weights=weights, trims=trims, ntrim=ntrim, eq=curve[-1] if curve else pot0, pend=pend, done=done)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbols", default=SYMBOLS); ap.add_argument("--months", type=int, default=10)
    ap.add_argument("--csv-dir", default=None); ap.add_argument("--asof", default=None, help="state as of this month-end (YYYY-MM-DD)")
    ap.add_argument("--flat-from", default="2026-10-31", help="paper pot starts flat on this date and buys what is ON at the last month-end before it")
    ap.add_argument("--trim-above", type=float, default=TRIM_ABOVE, help="trim a held position worth more than this share of the pot at the month-end close (0 = off)")
    ap.add_argument("--trim-to", type=float, default=TRIM_TO, help="trim back down to this share of the pot")
    ap.add_argument("--log", default=None, help="append one row per symbol per month-end to this CSV")
    a = ap.parse_args()
    syms = [x.strip().upper() for x in a.symbols.split(",")]; now = pd.Timestamp.now(tz="UTC"); w = 1 / len(syms); ff = pd.Timestamp(a.flat_from)
    rows = []; D = {}
    for s in syms:
        d = load(s, a.csv_dir); D[s] = d; c = d["Close"]
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
    m = model_pot(D, ff, now, a.months, a.trim_above, a.trim_to, a.asof)
    if m["pos"]:
        print(f"\nWEIGHTS at the last close, model pot ${m['eq']:,.0f} (trim above {a.trim_above:.0%} of the pot back to {a.trim_to:.0%}; weights drift with price, never topped up)")
        for sym, w in sorted(m["weights"].items(), key=lambda x: -x[1]): print(f"  {sym:5s} {w:5.1%}" + (f"   TRIM at next open: sell about {m['trims'][sym]:.0%} of the position" if sym in m["trims"] else ""))
    for sym, f in m["trims"].items(): acts.append(f"{sym}: TRIM at next open, sell about {f:.0%} of the position (weight {m['weights'][sym]:.1%} > {a.trim_above:.0%}; back to {a.trim_to:.0%} of the pot)")
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