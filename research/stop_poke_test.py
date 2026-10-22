#!/usr/bin/env python3
"""Two tests on the line>=3 breakout with the swing-low trail exit (daily bars).
  1. INTRADAY STOP: the hard stop (entry - m*ATR) is a stop-market that fires on the bar's low (gap -> filled at the open), instead of only on a close.
     Variants: close-based 1.5 ATR (what line3_explore.py tests), intraday 1.5 / 2 / 3 ATR, no hard stop.  Swing-low trail itself stays close-based, fill next open.
  2. FAILED POKES: signals split by whether the line had >=1 failed poke (high above the line, close back under it) in the previous 10 / 20 bars.
    python3 research/stop_poke_test.py data/btc.csv --from 2015-06-01
Needs Date,Open,High,Low,Close and pivot_line_breakouts.py in the same folder."""
import sys, argparse, numpy as np, pandas as pd
ap = argparse.ArgumentParser(); ap.add_argument("file"); ap.add_argument("--from", dest="frm", default="2015-06-01")
ap.add_argument("--cost", type=float, default=4.0); ap.add_argument("--stake", type=float, default=0.2); ap.add_argument("--tol", type=float, default=0.5)
ap.add_argument("--mint", type=int, default=3); ap.add_argument("--dump", default=None, help="save the daily return series of the intraday-1.5-ATR variant (for combining symbols)"); ap.add_argument("--perms", type=int, default=5000); ap.add_argument("--seed", type=int, default=1)
a = ap.parse_args(); rng = np.random.default_rng(a.seed); sys.argv = ["x", a.file]
import pivot_line_breakouts as P
P.CONF = False
o, h, l, c, D, n, atr = P.o, P.h, P.l, P.c, P.D, P.n, P.atr; COST = a.cost * 1e-4; HC = COST / 2; CAP = 120
S0 = int(np.searchsorted(D, np.datetime64(a.frm)))
ev = [x for x in P.find_events(a.tol, a.mint) if x["t"] + 1 >= S0 and x["t"] + 1 < n - 2]
PLOW = np.array([i for i in range(3, n - 3) if l[i] == l[i - 3:i + 4].min() and l[i] < l[i - 3:i].min()])
YRS = (D[n - 1] - D[S0]).astype("timedelta64[D]").astype(int) / 365.25; nbars = n - S0; bpy = nbars / YRS

def run(e, mult, wick, trail=True):
    """-> (exit bar x, exit px, reason, path of daily returns from entry to exit incl. costs)"""
    ent = o[e]; ae = atr[e - 1]; stop = ent - mult * ae if mult else -np.inf; cand = PLOW[PLOW >= e]
    for j in range(e, min(n, e + CAP + 1)):
        if wick and l[j] <= stop: x, px, why = j, min(o[j], stop) if j > e else stop, "stop"; break
        ok = cand[cand + 3 <= j - 1]; level = max(stop, l[ok].max() if (trail and len(ok)) else -np.inf)
        if c[j] <= level or j - e >= CAP or j == n - 1:
            why = "trail" if c[j] <= level else "cap/end"
            x, px = (j + 1, o[j + 1]) if j + 1 < n else (j, c[j]); break
    r = []; prev = ent
    for k in range(e, x): r.append(c[k] / prev - 1); prev = c[k]
    r.append(px / prev - 1); r = np.array(r); r[0] -= HC; r[-1] -= HC
    return x, px, why, r

def stats(s, W):
    d = W * s[S0:]; eq = np.cumprod(1 + d)
    return eq[-1] ** (1 / YRS) * 100 - 100, (eq / np.maximum.accumulate(np.r_[1.0, eq])[1:] - 1).min() * 100

sig = [x["t"] for x in ev]
print(f"{a.file}: {str(D[S0])[:10]}..{str(D[-1])[:10]}  signals {len(sig)}  cost {a.cost:.0f} bps RT\n")
print("1) INTRADAY STOP (swing-low trail, one position at a time, buy next open)")
print(f"{'variant':26s} {'n':>3s} {'win%':>5s} {'mean%':>6s} {'stops':>5s} | @100%: {'CAGR':>6s} {'maxDD':>6s} | @{a.stake*100:.0f}%: {'CAGR':>6s} {'maxDD':>6s} | stopped trades: mean ret vs close-rule on same entry")
base = {}
for name, mult, wick, trl in (("close-based 1.5 ATR (base)", 1.5, False, True), ("intraday 1.5 ATR", 1.5, True, True), ("intraday 2 ATR", 2.0, True, True), ("intraday 3 ATR", 3.0, True, True), ("no hard stop", 0, False, True), ("NO TRAIL: 1.5 stop + 120b cap", 1.5, True, False), ("NO TRAIL, NO STOP: 120b hold", 0, False, False)):
    tr, last, s, rets = [], -1, np.zeros(n), []
    for t in sig:
        e = t + 1
        if e <= last: continue
        x, px, why, r = run(e, mult, wick, trl); last = x; tr.append((e, why)); s[e:e + len(r)] += r; rets.append(((1 + r).prod() - 1) * 100)
    if name.startswith("close-based"):
        for (e, why), rr in zip(tr, rets): base[e] = rr
    st = [(e, rr) for (e, why), rr in zip(tr, rets) if why == "stop"]
    cmp = ""
    if st:
        # same-entry baseline return, computed per entry independently (trades can differ in what follows)
        bb = [((1 + run(e, 1.5, False)[3]).prod() - 1) * 100 for e, _ in st]
        cmp = f"{np.mean([rr for _, rr in st]):+.2f}% vs {np.mean(bb):+.2f}%"
    if a.dump and name == "intraday 1.5 ATR": np.save(a.dump, np.c_[D.astype('datetime64[D]').astype(np.int64), s])
    s1, s2 = stats(s, 1.0), stats(s, a.stake)
    print(f"{name:26s} {len(tr):3d} {np.mean(np.array(rets)>0)*100:5.1f} {np.mean(rets):+6.2f} {len(st):5d} | {s1[0]:+11.1f} {s1[1]:6.1f} | {s2[0]:+10.1f} {s2[1]:6.1f} | {cmp}")

print("\n2) FAILED POKES before the break (swing-low trail, close-based 1.5 ATR floor, each signal on its own)")
R = []; line_at = []
for x in ev:
    t = x["t"]; R.append((1 + run(t + 1, 1.5, False)[3]).prod() - 1); line_at.append(lambda i, x=x: x["L_e"] + x["slope"] * (i - (x["t"] + 2)))
R = np.array(R) * 100
def pokes(x, W):
    t = x["t"]; f = 0
    for i in range(max(0, t - W), t):
        L = x["L_e"] + x["slope"] * (i - (t + 2))
        if h[i] > L and c[i] < L: f += 1
    return f
for W in (10, 20):
    k = np.array([pokes(x, W) for x in ev]); m = k >= 1
    print(f"  window {W} bars: signals with >=1 failed poke: {m.sum()}, none: {(~m).sum()}")
    for lab, mm in ((f">=1 failed poke", m), ("no recent poke", ~m)):
        if mm.sum(): print(f"    {lab:16s} n={mm.sum():3d} win {np.mean(R[mm]>0)*100:4.1f}%  mean {R[mm].mean():+.2f}%  median {np.median(R[mm]):+.2f}%")
    if m.any() and (~m).any():
        d0 = R[m].mean() - R[~m].mean(); cnt = sum((R[p].mean() - R[~p].mean()) >= d0 for p in (rng.permutation(m) for _ in range(a.perms)))
        print(f"    poke - none = {d0:+.2f}%   permutation p (one-sided, poke better) = {(cnt + 1) / (a.perms + 1):.3f}")
    for kk in (1, 2):
        mm = k >= kk
        if kk == 2 and mm.sum() >= 3: print(f"    >=2 pokes       n={mm.sum():3d} win {np.mean(R[mm]>0)*100:4.1f}%  mean {R[mm].mean():+.2f}%")