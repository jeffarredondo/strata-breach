#!/usr/bin/env python3
"""Monthly review.  Read-only: nothing here places or changes anything, and scan.py / monthly_trend.py are untouched.

    python3 month_check.py                              # both pots since their start dates, Yahoo data
    python3 month_check.py --trades log/trades.csv      # also compare your logged fills with the model's (export your sheet in that layout)
    python3 month_check.py --csv-dir data               # read SYMBOL.csv (Date,Open,High,Low,Close) instead of Yahoo

Three things it prints:
  1. DAILY POT   the rules replayed from --flat-from (take every signal, 33% of the pot, max 3 open, IAU/PPLT/IBIT before VGT/BNO, swing-low exit at the next open,
                 2 bps per side): trades, value, drawdown.  Same replay as scan.py's MODEL line.
  2. ADHERENCE   (needs --trades) model entries and exits vs your logged ones: signals taken / missed, fill vs the model's next open in bps (+ = worse for you), and rows not in the model.
  3. MONTHLY POT the monthly_trend.py rule from --monthly-from (including its trim guidance): states, value, drawdown.
Each pot's return is placed in a cone: bootstrap paths drawn from the backtest trades (research/backtest_trades.csv) or months (research/backtest_monthly.csv)
for the same elapsed time.  The cone starts after about 3 months; before that there is nothing to compare.
"""
import argparse, os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import scan, monthly_trend as mt

ET = scan.ET; PRIORITY = ["IAU", "PPLT", "IBIT", "VGT", "BNO"]; STAKE = 0.33; SLOTS = 3; COST = 2e-4; POT0 = 5000.


def get(sym, csv_dir):
    if csv_dir:
        d = pd.read_csv(os.path.join(csv_dir, f"{sym.lower()}.csv"), parse_dates=["Date"]).set_index("Date").sort_index()[["Open", "High", "Low", "Close"]]
        d.index = d.index.tz_localize(ET); return d
    return scan.load_yahoo(sym, "1d")[0]


def model_trades(s, start):
    """Entries/exits the rules would have made since `start` (same loop as scan.model_position).  x is None while the exit is not filled yet."""
    out, open_e = [], None
    for j in range(60, s.n):
        if open_e is not None:
            if scan.trail(s, open_e, s.o[open_e], j)["hit"]:
                out.append(dict(e=open_e, x=j + 1 if j + 1 < s.n else None, pending=j + 1 >= s.n)); open_e = None
            continue
        if s.idx[j] < start or j + 1 > s.n - 1: continue
        if scan.find_line(s, j, "cross"): open_e = j + 1
    if open_e is not None: out.append(dict(e=open_e, x=None))
    return out


def metrics(rets, ref=None):
    """One line: n, win rate, average win/loss, payoff, profit factor, mean trade.  rets are trade returns in %."""
    r = np.array(rets, float)
    if len(r) == 0: return "none closed yet"
    w, l = r[r > 0], r[r <= 0]; pf = w.sum() / -l.sum() if len(l) and l.sum() < 0 else float("inf")
    pay = (w.mean() / -l.mean()) if len(w) and len(l) and l.mean() < 0 else float("nan")
    return f"n={len(r)}, win {len(w) / len(r) * 100:.0f}%, avg win {w.mean() if len(w) else 0:+.1f}%, avg loss {l.mean() if len(l) else 0:+.1f}%, payoff {pay:.1f}, PF {pf:.2f}, mean {r.mean():+.2f}%"


def dd(curve):
    c = np.array(curve); return (c / np.maximum.accumulate(c) - 1).min() if len(c) else 0.0


def daily_pot(S, trades, start):
    dates = sorted({t for s in S.values() for t in s.idx if t >= start}); cl = {k: pd.Series(s.c, index=s.idx).reindex(dates).ffill() for k, s in S.items()}
    ent = {(sym, S[sym].idx[t["e"]]): t for sym, ts in trades.items() for t in ts}
    cash, pos, prev, curve, done, skipped = POT0, {}, POT0, [], [], []
    for dt in dates:
        for sym, p in list(pos.items()):
            t, s = p["t"], S[sym]
            if t["x"] is not None and s.idx[t["x"]] == dt:
                px = s.o[t["x"]] * (1 - COST); cash += p["sh"] * px; done.append(dict(sym=sym, e=p["t"]["e"], x=t["x"], ret=px / p["cost"] - 1, pnl=p["sh"] * px - p["stake"])); del pos[sym]
        for sym in PRIORITY:
            t = ent.get((sym, dt))
            if not t: continue
            if sym in pos or len(pos) >= SLOTS or cash <= 0: skipped.append((sym, dt.date())); continue
            stake = min(STAKE * prev, cash); cost = S[sym].o[t["e"]] * (1 + COST); cash -= stake; pos[sym] = dict(t=t, sh=stake / cost, stake=stake, cost=cost)
        eq = cash + sum(p["sh"] * cl[sym][dt] for sym, p in pos.items()); curve.append(eq); prev = eq
    return dict(dates=dates, curve=curve, done=done, open=pos, skipped=skipped, eq=curve[-1] if curve else POT0)


def cone_daily(years, ret):
    bt = pd.read_csv(os.path.join(HERE, "research", "backtest_trades.csv")); r = bt["RetPct"].values / 100
    rate = len(bt) / ((pd.Timestamp(bt.EntryDate.max()) - pd.Timestamp(bt.EntryDate.min())).days / 365.25); rng = np.random.default_rng(1)
    m = np.array([np.prod(1 + STAKE * rng.choice(r, rng.poisson(rate * years))) - 1 for _ in range(20000)])
    return np.percentile(m, [5, 25, 50, 75, 95]) * 100, (m < ret).mean() * 100


def cone_monthly(months, ret):
    r = pd.read_csv(os.path.join(HERE, "research", "backtest_monthly.csv"))["RetPct"].values / 100; rng = np.random.default_rng(2)
    m = np.array([np.prod(1 + rng.choice(r, months)) - 1 for _ in range(20000)])
    return np.percentile(m, [5, 25, 50, 75, 95]) * 100, (m < ret).mean() * 100


def show_cone(label, years, ret, fn, arg):
    if years * 12 < 3: print(f"  cone: starts after ~3 months ({years * 12:.1f} elapsed)"); return
    q, pct = fn(arg, ret / 100)
    print(f"  cone for the same time (backtest bootstrap): 5% {q[0]:+.1f}  25% {q[1]:+.1f}  median {q[2]:+.1f}  75% {q[3]:+.1f}  95% {q[4]:+.1f}   |   {label} {ret:+.1f}% is at percentile {pct:.0f}")


def adherence(S, trades, res, path, pot_filter):
    h = pd.read_csv(path)
    if pot_filter and "Pot" in h.columns: h = h[h["Pot"].astype(str).str.lower() == pot_filter.lower()]
    h = h.dropna(subset=["Symbol"]).copy(); h["Symbol"] = h["Symbol"].astype(str).str.upper().str.strip(); h["ed"] = pd.to_datetime(h["EntryTime"]).dt.normalize()
    h["xd"] = pd.to_datetime(h["ExitTime"], errors="coerce").dt.normalize() if "ExitTime" in h.columns else pd.NaT; used = set(); taken = missed = 0; es, xs = [], []; rows = []
    for sym, ts in trades.items():
        s = S[sym]
        for t in ts:
            d = s.idx[t["e"]].tz_localize(None).normalize()
            if (sym, d.date()) in {(a, b) for a, b in res["skipped"]}: continue                       # model could not take it (slots/cash)
            m = h[(h["Symbol"] == sym) & ((h["ed"] - d).abs() <= pd.Timedelta(days=1)) & ~h.index.isin(used)]
            if m.empty: missed += 1; rows.append(f"  missed   {sym} model entry {d.date()} open {s.o[t['e']]:,.2f}"); continue
            r = m.iloc[0]; used.add(m.index[0]); taken += 1; ep, xp = pd.to_numeric(r.get("EntryPx"), errors="coerce"), pd.to_numeric(r.get("ExitPx"), errors="coerce")
            if pd.notna(ep) and ep > 0: es.append((ep / s.o[t["e"]] - 1) * 1e4)
            if t["x"] is not None and pd.notna(xp) and xp > 0: xs.append((s.o[t["x"]] / xp - 1) * 1e4)
    extra = h[~h.index.isin(used)]
    xr = pd.to_numeric(h["ExitPx"], errors="coerce") if "ExitPx" in h.columns else pd.Series(np.nan, index=h.index); er = pd.to_numeric(h["EntryPx"], errors="coerce")
    mine = ((xr / er - 1) * 100)[xr.notna() & (xr > 0) & (er > 0)].tolist()
    print(f"  your closed trades:        {metrics(mine)}\n  model, same period:        {metrics([t['ret'] * 100 for t in res['done']])}")
    print(f"  model entries taken {taken}, missed {missed}; signals the model skipped for slots/cash: {len(res['skipped'])}")
    for x in rows: print(x)
    if es: print(f"  entry fill vs model open: mean {np.mean(es):+.0f} bps (n={len(es)}, + = you paid more)")
    if xs: print(f"  exit fill vs model open:  mean {np.mean(xs):+.0f} bps (n={len(xs)}, + = you received less)")
    for _, r in extra.iterrows(): print(f"  not in the model: {r['Symbol']} entry {r['ed'].date()} @ {r['EntryPx']}")


def monthly_pot(D, flat_from, now):
    """The monthly_trend.py model (entries 1/N of the pot, trim above 30% back to 20% at month-end, exits at signal), so both scripts use the same code."""
    return mt.model_pot(D, flat_from, now, pot0=POT0)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--flat-from", default="2026-10-19"); ap.add_argument("--monthly-from", default="2026-10-31")
    ap.add_argument("--trades", default=None, help="your trade log CSV (Symbol, EntryTime, EntryPx, ExitTime, ExitPx; optional Pot column)"); ap.add_argument("--pot", default=None, help="only rows with this Pot value")
    ap.add_argument("--csv-dir", default=None); a = ap.parse_args(); now = pd.Timestamp.now(tz="UTC")
    S = {}; D = {}
    for sym in PRIORITY:
        d = get(sym, a.csv_dir); D[sym] = d.copy(); D[sym].index = D[sym].index.tz_localize(None) if D[sym].index.tz is None else D[sym].index.tz_convert(ET).tz_localize(None); S[sym] = scan.S(d)
    start = pd.Timestamp(a.flat_from).tz_localize(ET); today = D["IAU"].index[-1].date()
    trades = {sym: model_trades(S[sym], start) for sym in PRIORITY}; res = daily_pot(S, trades, start)
    yrs = max((S["IAU"].idx[-1] - start).days, 0) / 365.25; ret = (res["eq"] / POT0 - 1) * 100
    print(f"MONTHLY REVIEW  (data through {today})\n\n1. DAILY POT, flat from {a.flat_from}, ${POT0:,.0f}, {STAKE:.0%} per trade, max {SLOTS} open")
    print(f"  value ${res['eq']:,.0f} ({ret:+.1f}%), max drawdown {dd(res['curve']) * 100:.1f}%, closed trades {len(res['done'])}, open {', '.join(res['open']) or 'none'}")
    for t in res["done"]: print(f"    {t['sym']:5s} {S[t['sym']].idx[t['e']].date()} -> {S[t['sym']].idx[t['x']].date()}  {t['ret'] * 100:+.1f}%  ${t['pnl']:+,.0f}")
    bt = pd.read_csv(os.path.join(HERE, "research", "backtest_trades.csv"))["RetPct"].values
    print(f"  metrics (perfect adherence): {metrics([t['ret'] * 100 for t in res['done']])}\n  backtest 2018-26 reference:  {metrics(bt)}")
    for sym, p in res["open"].items(): print(f"    {sym:5s} {S[sym].idx[p['t']['e']].date()} -> open  ({(S[sym].c[-1] / p['cost'] - 1) * 100:+.1f}% at the last close){'  EXIT at next open' if p['t'].get('pending') else ''}")
    for sym, d in res["skipped"]: print(f"    {sym:5s} signal {d} not taken (slots/cash)")
    show_cone("daily pot", yrs, ret, cone_daily, yrs)
    if a.trades: print("\n2. ADHERENCE vs " + a.trades); adherence(S, trades, res, a.trades, a.pot)
    else: print("\n2. ADHERENCE: pass --trades YOUR_EXPORT.csv to compare your fills with the model")
    mf = pd.Timestamp(a.monthly_from); m = monthly_pot(D, mf, now); myrs = max((D["IAU"].index[-1] - mf).days, 0) / 365.25; mret = (m["eq"] / POT0 - 1) * 100
    print(f"\n3. MONTHLY POT, flat from {a.monthly_from}, ${POT0:,.0f}, 1/{len(PRIORITY)} of the pot at entry, trim above {mt.TRIM_ABOVE:.0%} back to {mt.TRIM_TO:.0%} at month-end, never topped up")
    print(f"  value ${m['eq']:,.0f} ({mret:+.1f}%), max drawdown {dd(m['curve']) * 100:.1f}%, holding {', '.join(m['pos']) or 'none'}" + (f"; at next open: {', '.join(m['pend'] + ['TRIM ' + k for k in m['trims']])}" if m["pend"] or m["trims"] else "") + (f"; trims so far {m['ntrim']}" if m["ntrim"] else ""))
    print(f"  metrics (perfect adherence), closed round trips: {metrics(m['done'])}")
    show_cone("monthly pot", myrs, mret, cone_monthly, int(round(myrs * 12)))
    print(f"\n(model fills = next open, 2 bps per side; the scan's trail is close-based, so intraday stop fills are not modeled here; run {pd.Timestamp.now(tz=ET).strftime('%Y-%m-%d %H:%M ET')})")


if __name__ == "__main__":
    main()