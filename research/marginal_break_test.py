#!/usr/bin/env python3
"""Marginal breaks: does it matter how far the signal bar closes above the falling line?
margin = (close[t] - line[t]) / ATR[t]  at the signal bar t.  Trades: buy next open, swing-low trail, intraday 1.5 ATR stop (the paper plan).
  1. Per signal (each on its own): n / win / mean / median by margin bucket.
  2. Filter test: take only signals with margin >= X (one position at a time): n, CAGR @100% and @20% stake, maxDD.
    python3 research/marginal_break_test.py data/btc.csv --from 2015-06-01 [--mint 3]
Needs Date,Open,High,Low,Close and pivot_line_breakouts.py in the same folder."""
import sys, argparse, numpy as np, pandas as pd
ap = argparse.ArgumentParser(); ap.add_argument("file"); ap.add_argument("--from", dest="frm", default="2015-06-01")
ap.add_argument("--cost", type=float, default=4.0); ap.add_argument("--stake", type=float, default=0.2); ap.add_argument("--tol", type=float, default=0.5)
ap.add_argument("--mint", type=int, default=3); ap.add_argument("--perms", type=int, default=5000); ap.add_argument("--seed", type=int, default=1)
a = ap.parse_args(); rng = np.random.default_rng(a.seed); sys.argv = ["x", a.file]
import pivot_line_breakouts as P
P.CONF = False
o, h, l, c, D, n, atr = P.o, P.h, P.l, P.c, P.D, P.n, P.atr; COST = a.cost * 1e-4; HC = COST / 2; CAP = 120
S0 = int(np.searchsorted(D, np.datetime64(a.frm)))
ev = [x for x in P.find_events(a.tol, a.mint) if x["t"] + 1 >= S0 and x["t"] + 1 < n - 2]
for x in ev: x["margin"] = (c[x["t"]] - (x["L_e"] - 2 * x["slope"])) / atr[x["t"]]
PLOW = np.array([i for i in range(3, n - 3) if l[i] == l[i - 3:i + 4].min() and l[i] < l[i - 3:i].min()])
YRS = (D[n - 1] - D[S0]).astype("timedelta64[D]").astype(int) / 365.25

def run(e, mult=1.5):
    ent = o[e]; ae = atr[e - 1]; stop = ent - mult * ae; cand = PLOW[PLOW >= e]
    for j in range(e, min(n, e + CAP + 1)):
        if l[j] <= stop: x, px = j, (min(o[j], stop) if j > e else stop); break
        ok = cand[cand + 3 <= j - 1]; level = max(stop, l[ok].max() if len(ok) else -np.inf)
        if c[j] <= level or j - e >= CAP or j == n - 1:
            x, px = (j + 1, o[j + 1]) if j + 1 < n else (j, c[j]); break
    r = []; prev = ent
    for k in range(e, x): r.append(c[k] / prev - 1); prev = c[k]
    r.append(px / prev - 1); r = np.array(r); r[0] -= HC; r[-1] -= HC
    return x, r

def stats(s, W):
    d = W * s[S0:]; eq = np.cumprod(1 + d)
    return eq[-1] ** (1 / YRS) * 100 - 100, (eq / np.maximum.accumulate(np.r_[1.0, eq])[1:] - 1).min() * 100

R = np.array([((1 + run(x["t"] + 1)[1]).prod() - 1) * 100 for x in ev]); M = np.array([x["margin"] for x in ev])
print(f"{a.file}: {str(D[S0])[:10]}..{str(D[-1])[:10]}  signals {len(ev)}  mint {a.mint}  median margin {np.median(M):.2f} ATR\n")
print("1) by margin of the signal close above the line (ATR)")
for lo, hi in ((-1, 0.1), (0.1, 0.25), (0.25, 0.5), (0.5, 1.0), (1.0, 99)):
    m = (M > lo) & (M <= hi)
    if m.sum(): print(f"  ({lo:4.2f}, {hi:4.2f}]  n={m.sum():3d}  win {np.mean(R[m]>0)*100:4.1f}%  mean {R[m].mean():+6.2f}%  median {np.median(R[m]):+6.2f}%")
print("\n  barely vs clearly above (one-sided permutation p, clear > barely):")
for thr in (0.1, 0.25, 0.5):
    m = M >= thr
    if m.any() and (~m).any():
        d0 = R[m].mean() - R[~m].mean(); cnt = sum((R[p].mean() - R[~p].mean()) >= d0 for p in (rng.permutation(m) for _ in range(a.perms)))
        print(f"    margin >= {thr:.2f} ATR: n={m.sum()} vs {(~m).sum()}   {R[m].mean():+.2f}% vs {R[~m].mean():+.2f}%   diff {d0:+.2f}%   p={(cnt + 1) / (a.perms + 1):.3f}")
print(f"\n2) filter: take only signals with margin >= X (one position at a time)")
print(f"{'min margin':>10s} {'n':>3s} {'/yr':>4s} {'win%':>5s} {'mean%':>6s} | @100%: {'CAGR':>6s} {'maxDD':>6s} | @{a.stake*100:.0f}%: {'CAGR':>6s} {'maxDD':>6s}")
for thr in (-99, 0.1, 0.25, 0.5):
    s = np.zeros(n); last = -1; rets = []
    for x in ev:
        if x["margin"] < thr: continue
        e = x["t"] + 1
        if e <= last: continue
        xx, r = run(e); last = xx; s[e:e + len(r)] += r; rets.append(((1 + r).prod() - 1) * 100)
    if not rets: continue
    s1, s2 = stats(s, 1.0), stats(s, a.stake)
    print(f"{('all' if thr < -90 else f'{thr:.2f}'):>10s} {len(rets):3d} {len(rets)/YRS:4.1f} {np.mean(np.array(rets)>0)*100:5.1f} {np.mean(rets):+6.2f} | {s1[0]:+11.1f} {s1[1]:6.1f} | {s2[0]:+10.1f} {s2[1]:6.1f}")