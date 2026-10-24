#!/usr/bin/env python3
"""Swing-low size N for the trail exit: a swing low = lowest low of the N bars before and the N bars after it, confirmed N bars later (N=3 is the plan).
Line>=3 breaks, buy next open, intraday 1.5 ATR stop, trail = highest confirmed swing low (floor = the stop), exit on a close at/below it, fill next open, one position at a time, 4 bps.
    python3 research/swing_n_test.py data/btc.csv 2015-06-01 [--stake 0.33] [--ns 1,2,3,4,5,7]
Needs Date,Open,High,Low,Close and pivot_line_breakouts.py in the same folder."""
import sys, os, argparse, numpy as np
ap = argparse.ArgumentParser(); ap.add_argument("file"); ap.add_argument("frm"); ap.add_argument("--stake", type=float, default=0.33); ap.add_argument("--ns", default="1,2,3,4,5,7"); a = ap.parse_args()
sys.argv = ["x", a.file]
import pivot_line_breakouts as P
P.CONF = False
o, h, l, c, D, n, atr = P.o, P.h, P.l, P.c, P.D, P.n, P.atr; HC = 2e-4; CAP = 120
S0 = int(np.searchsorted(D, np.datetime64(a.frm))); YRS = (D[n - 1] - D[S0]).astype("timedelta64[D]").astype(int) / 365.25
ev = [x for x in P.find_events(0.5, 3) if x["t"] + 1 >= S0 and x["t"] + 1 < n - 2]
def stats(s, W):
    eq = np.cumprod(1 + W * s[S0:]); return eq[-1] ** (1 / YRS) * 100 - 100, (eq / np.maximum.accumulate(np.r_[1.0, eq])[1:] - 1).min() * 100
print(f"{os.path.basename(a.file)}: {str(D[S0])[:10]}..{str(D[-1])[:10]}  signals {len(ev)}")
print(f"{'N':>2s} {'trades':>6s} {'win%':>5s} {'mean%':>6s} {'hold':>5s} {'stop%':>5s} | @100%: {'CAGR':>6s} {'maxDD':>6s} | @{a.stake*100:.0f}%: {'CAGR':>6s} {'maxDD':>6s}")
for N in map(int, a.ns.split(",")):
    PL = np.array([i for i in range(N, n - N) if l[i] == l[i - N:i + N + 1].min() and l[i] < l[i - N:i].min()])
    s = np.zeros(n); last = -1; R = []; H = []; st = 0
    for x in ev:
        e = x["t"] + 1
        if e <= last: continue
        ent = o[e]; ae = atr[e - 1]; stop = ent - 1.5 * ae; cand = PL[PL >= e]; why = "trail"
        for j in range(e, min(n, e + CAP + 1)):
            if l[j] <= stop: xx, px, why = j, (min(o[j], stop) if j > e else stop), "stop"; break
            ok = cand[cand + N <= j - 1]; lev = max(stop, l[ok].max() if len(ok) else -np.inf)
            if c[j] <= lev or j - e >= CAP or j == n - 1: xx, px = (j + 1, o[j + 1]) if j + 1 < n else (j, c[j]); break
        r = []; prev = ent
        for k in range(e, xx): r.append(c[k] / prev - 1); prev = c[k]
        r.append(px / prev - 1); r = np.array(r); r[0] -= HC; r[-1] -= HC
        last = xx; s[e:e + len(r)] += r; R.append(((1 + r).prod() - 1) * 100); H.append(xx - e + 1); st += why == "stop"
    s1, s2 = stats(s, 1.0), stats(s, a.stake)
    print(f"{N:2d} {len(R):6d} {np.mean(np.array(R)>0)*100:5.1f} {np.mean(R):+6.2f} {np.mean(H):5.1f} {st/len(R)*100:5.0f} | {s1[0]:+11.1f} {s1[1]:6.1f} | {s2[0]:+10.1f} {s2[1]:6.1f}")
