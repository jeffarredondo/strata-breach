#!/usr/bin/env python3
"""Per-trade return distribution for the plan (line>=3 break, intraday 1.5 ATR stop + swing-low trail, one position at a time): counts by exit reason, win/loss sizes, percentiles, buckets, share of return from the top trades.
    python3 research/trade_dist.py data/btc.csv 2015-06-01   (second argument = scoring start date)
Needs Date,Open,High,Low,Close and pivot_line_breakouts.py in the same folder."""
import sys, os, numpy as np
f = sys.argv[1]; frm = sys.argv[2]; sys.argv = ["x", f]
import pivot_line_breakouts as P
P.CONF = False
o, h, l, c, D, n, atr = P.o, P.h, P.l, P.c, P.D, P.n, P.atr; HC = 2e-4; CAP = 120
S0 = int(np.searchsorted(D, np.datetime64(frm)))
ev = [x for x in P.find_events(0.5, 3) if x["t"] + 1 >= S0 and x["t"] + 1 < n - 2]
PLOW = np.array([i for i in range(3, n - 3) if l[i] == l[i - 3:i + 4].min() and l[i] < l[i - 3:i].min()])
def run(e):
    ent = o[e]; ae = atr[e - 1]; stop = ent - 1.5 * ae; cand = PLOW[PLOW >= e]
    for j in range(e, min(n, e + CAP + 1)):
        if l[j] <= stop: x, px, why = j, (min(o[j], stop) if j > e else stop), "stop"; break
        ok = cand[cand + 3 <= j - 1]; lev = max(stop, l[ok].max() if len(ok) else -np.inf)
        if c[j] <= lev or j - e >= CAP or j == n - 1: why = "trail"; x, px = (j + 1, o[j + 1]) if j + 1 < n else (j, c[j]); break
    r = []; prev = ent
    for k in range(e, x): r.append(c[k] / prev - 1); prev = c[k]
    r.append(px / prev - 1); r = np.array(r); r[0] -= HC; r[-1] -= HC
    return x, why, ((1 + r).prod() - 1) * 100, x - e + 1
last = -1; T = []
for x in ev:
    e = x["t"] + 1
    if e <= last: continue
    xx, why, ret, hold = run(e); last = xx; T.append((why, ret, hold))
why = np.array([t[0] for t in T]); R = np.array([t[1] for t in T]); H = np.array([t[2] for t in T])
name = os.path.basename(f)
print(f"== {name} {frm}..: {len(R)} trades, stops {np.sum(why=='stop')} ({np.mean(why=='stop')*100:.0f}%), trail exits {np.sum(why=='trail')}")
def line(lab, m):
    if m.sum(): print(f"  {lab:22s} n={m.sum():3d}  mean {R[m].mean():+6.2f}%  median {np.median(R[m]):+6.2f}%  min {R[m].min():+6.1f}%  max {R[m].max():+6.1f}%  hold {H[m].mean():4.1f}b")
line("all", np.ones(len(R), bool)); line("stopped", why == "stop"); line("trail exit, loss", (why == "trail") & (R <= 0)); line("trail exit, gain", (why == "trail") & (R > 0)); line("winners", R > 0); line("losers", R <= 0)
q = np.percentile(R, [10, 25, 50, 75, 90]); print("  pctiles 10/25/50/75/90: " + " / ".join(f"{v:+.1f}%" for v in q))
srt = np.sort(R)[::-1]; tot = np.log1p(R / 100).sum(); print(f"  top 3 trades = {np.log1p(srt[:3]/100).sum()/tot*100:.0f}% of total log return; top 5 = {np.log1p(srt[:5]/100).sum()/tot*100:.0f}%")
edges = [-100, -5, -3, -1, 0, 2, 5, 10, 20, 50, 1e9]; cnt, _ = np.histogram(R, bins=edges)
print("  buckets (<=-5, -5..-3, -3..-1, -1..0, 0..2, 2..5, 5..10, 10..20, 20..50, >50): " + str(cnt.tolist()))