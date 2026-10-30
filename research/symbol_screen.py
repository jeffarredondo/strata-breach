#!/usr/bin/env python3
"""Symbol screen in R.  Same line>=3 breakout signals and the plan's exit (swing-low trail, intraday 1.5 ATR stop) on each file, one position at a time,
every trade expressed in R = trade return / (1.5 x ATR(14) at entry / entry open), so symbols with different volatility are comparable.
Per symbol: trades, per year, win rate, mean / median R (+ bootstrap 5-95% of the mean), share of trades reaching 3R / 5R / 10R, best trade in R, top-3 trades' share of total positive R,
skew of R, and the same signals' mean R against random entries (same exit, same count): percentile of the real mean.
    python3 research/symbol_screen.py data/iau.csv data/pplt.csv data/ibit_hours_2018_2026.csv --from 2018-09-01"""
import sys, os, argparse, subprocess, numpy as np, pandas as pd
ap = argparse.ArgumentParser(); ap.add_argument("files", nargs="+"); ap.add_argument("--from", dest="frm", default="2018-09-01"); ap.add_argument("--cost", type=float, default=4.0)
ap.add_argument("--draws", type=int, default=2000); ap.add_argument("--seed", type=int, default=1); ap.add_argument("--one", action="store_true"); a = ap.parse_args()
if not a.one:
    here = os.path.dirname(os.path.abspath(__file__)); rows = []
    for f in a.files:
        r = subprocess.run([sys.executable, os.path.abspath(__file__), os.path.abspath(f), "--from", a.frm, "--cost", str(a.cost), "--draws", str(a.draws), "--seed", str(a.seed), "--one"], capture_output=True, text=True, cwd=here)
        rows.append(r.stdout.strip() or f"{os.path.basename(f)}: error {r.stderr.strip()[-120:]}")
    print(f"{'symbol':16s} {'n':>3s} {'/yr':>4s} {'win':>4s} {'meanR':>6s} {'(5-95%)':>13s} {'medR':>6s} {'>=3R':>5s} {'>=5R':>5s} {'>=10R':>5s} {'bestR':>6s} {'top3':>5s} {'skew':>5s} | {'null meanR':>10s} {'real pct':>8s}")
    print("\n".join(rows)); sys.exit()
rng = np.random.default_rng(a.seed); f = a.files[0]; sys.argv = ["x", f]
import pivot_line_breakouts as P
P.CONF = False; P.MAJOR = False
o, h, l, c, D, n, atr = P.o, P.h, P.l, P.c, P.D, P.n, P.atr; HC = a.cost * 1e-4 / 2; CAP = 120
S0 = int(np.searchsorted(D, np.datetime64(a.frm))); YRS = (D[n - 1] - D[S0]).astype("timedelta64[D]").astype(int) / 365.25
ev = [x for x in P.find_events(0.5, 3) if x["t"] + 1 >= S0 and x["t"] + 1 < n - 2]
PLOW = np.array([i for i in range(3, n - 3) if l[i] == l[i - 3:i + 4].min() and l[i] < l[i - 3:i].min()])
def run(e):
    ent = o[e]; ae = atr[e - 1]; stop = ent - 1.5 * ae; cand = PLOW[PLOW >= e]
    for j in range(e, min(n, e + CAP + 1)):
        if l[j] <= stop: x, px = j, (min(o[j], stop) if j > e else stop); break
        ok = cand[cand + 3 <= j - 1]; level = max(stop, l[ok].max() if len(ok) else -np.inf)
        if c[j] <= level or j - e >= CAP or j == n - 1:
            x, px = (j + 1, o[j + 1]) if j + 1 < n else (j, c[j]); break
    r = []; prev = ent
    for k in range(e, x): r.append(c[k] / prev - 1); prev = c[k]
    r.append(px / prev - 1); r = np.array(r); r[0] -= HC; r[-1] -= HC
    return x, ((1 + r).prod() - 1) / (1.5 * ae / ent)
R, last = [], -1
for x in ev:
    e = x["t"] + 1
    if e <= last: continue
    xx, rr = run(e); last = xx; R.append(rr)
R = np.array(R); name = os.path.basename(f).split(".")[0]
if len(R) < 3: print(f"{name:16s} {len(R):3d} trades"); sys.exit()
bs = np.array([rng.choice(R, len(R)).mean() for _ in range(a.draws)]); pos = R[R > 0]; top3 = np.sort(R)[-3:].sum() / pos.sum() * 100 if len(pos) else np.nan
skew = ((R - R.mean()) ** 3).mean() / (R.std() ** 3)
nm = np.array([np.mean([run(int(e))[1] for e in rng.integers(S0 + 1, n - 130, len(R))]) for _ in range(300)])
print(f"{name:16s} {len(R):3d} {len(R)/YRS:4.1f} {np.mean(R>0)*100:3.0f}% {R.mean():+6.2f} {f'{np.percentile(bs,5):+.2f}..{np.percentile(bs,95):+.2f}':>13s} {np.median(R):+6.2f} {np.mean(R>=3)*100:4.0f}% {np.mean(R>=5)*100:4.0f}% {np.mean(R>=10)*100:4.0f}% {R.max():+6.1f} {top3:4.0f}% {skew:+5.1f} | {nm.mean():+10.2f} {np.mean(nm<R.mean())*100:7.0f}%")