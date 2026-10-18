#!/usr/bin/env python3
"""Line explorer: line>=3 falling-line breakouts, five exits, fresh-9/21 split, permutation tests and a one-position portfolio block (CAGR/vol/maxDD at 100% and at --stake, vs buy&hold, exposure-matched B&H and a random-entry null).
    python3 research/line3_explore.py data/iau.csv --atr true --from 2015-06-01
Needs Date,Open,High,Low,Close (daily) and pivot_line_breakouts.py in the same folder.  Exits: fixed, chand, line, swing (swing-low trail N=3), x921.  scan.py reimplements the entry + swing exit and was checked against this file."""
import sys, argparse, numpy as np, pandas as pd
ap = argparse.ArgumentParser(); ap.add_argument("file"); ap.add_argument("--mint", type=int, default=3); ap.add_argument("--tol", type=float, default=0.5); ap.add_argument("--atr", default="star", choices=["star", "true"])
ap.add_argument("--from", dest="frm", default="2001-01-01"); ap.add_argument("--trim", type=int, default=0); ap.add_argument("--perms", type=int, default=5000); ap.add_argument("--seed", type=int, default=1)
ap.add_argument("--cost", type=float, default=4.0, help="round-trip cost in bps"); ap.add_argument("--stake", type=float, default=0.2); ap.add_argument("--draws", type=int, default=200); ap.add_argument("--noport", action="store_true")
a = ap.parse_args(); rng = np.random.default_rng(a.seed)
sys.argv = ["x", a.file]
import pivot_line_breakouts as P
P.CONF = False
o, h, l, c, D, n = P.o, P.h, P.l, P.c, P.D, P.n; COST = a.cost * 1e-4; CAP = 120; K = 1.68
if a.atr == "star":
    pc = np.r_[c[0], c[:-1]]; x = abs(c - pc); atr = np.empty(n); atr[0] = x[0]
    for i in range(1, n): atr[i] = atr[i - 1] + (x[i] - atr[i - 1]) / 14
    atr = K * atr; P.atr = atr
else: atr = P.atr
S = pd.Series(c); e9 = S.ewm(span=9, adjust=False).mean().values; e21 = S.ewm(span=21, adjust=False).mean().values
on = e9 > e21; crossed = np.r_[False, on[1:] & ~on[:-1]]; fresh = pd.Series(crossed).rolling(5, min_periods=1).max().values.astype(bool) & on
S0 = int(np.searchsorted(D, np.datetime64(a.frm)))
def walk(e, kind):
    """index of the bar whose CLOSE triggers the exit (exit fills at the next open).  Kinds:
    fixed  stop 1.5 ATR / target 3.5 ATR | chand  trail 1.5 ATR below highest close
    line   close back below the broken line (line extended), or the 1.5 ATR hard stop
    swing  close below the highest confirmed swing low (N=3) formed since entry, floor = 1.5 ATR hard stop
    x921   EMA9 crosses back below EMA21 (only once EMA9 has been above since entry), or the 1.5 ATR hard stop"""
    ent = o[e]; ae = atr[e - 1]; hc = c[e]; armed = False
    if kind == "line":
        if e not in EVI: return None
        L, sl, e0 = EVI[e]
    if kind == "swing": cand = PLOW[PLOW >= e]
    for j in range(e, min(n, e + CAP + 1)):
        hc = max(hc, c[j])
        if kind == "fixed": hit = c[j] <= ent - 1.5 * ae or c[j] >= ent + 3.5 * ae
        elif kind == "chand": hit = c[j] <= hc - 1.5 * ae
        elif kind == "line": hit = c[j] <= ent - 1.5 * ae or c[j] < L + sl * (j - e0)
        elif kind == "swing":
            ok = cand[cand + 3 <= j - 1]; hit = c[j] <= (max(ent - 1.5 * ae, l[ok].max()) if len(ok) else ent - 1.5 * ae)
        else:
            if e9[j] > e21[j]: armed = True
            hit = c[j] <= ent - 1.5 * ae or (armed and e9[j] < e21[j])
        if hit or j - e >= CAP or j == n - 1: return j
    return None
def sim(e, kind):
    j = walk(e, kind)
    if j is None: return None
    ent = o[e]; px = o[j + 1] if j + 1 < n else c[j]
    return px / ent - 1 - COST, (j + 1 if j + 1 < n else j) - e
def box(t, k=4):
    lim = k * atr[t - 1]; mx = mn = c[t - 1]; age = 1
    while age < 120 and t - 1 - age >= 0:
        v = c[t - 1 - age]; m2, n2 = max(mx, v), min(mn, v)
        if m2 - n2 > lim: break
        mx, mn = m2, n2; age += 1
    return age, mx
ev = P.find_events(a.tol, a.mint)
EVI = {x["t"] + 1: (x["L_e"], x["slope"], x["t"] + 2) for x in ev}   # entry bar -> (line value at bar t+2, slope per bar, t+2)
PLOW = np.array([i for i in range(3, n - 3) if l[i] == l[i - 3:i + 4].min() and l[i] < l[i - 3:i].min()])
sets ={"LINE>=mint": [x["t"] for x in ev]}
sets = {k: [t for t in v if t + 1 >= S0 and t + 1 < n - a.trim - 2] for k, v in sets.items()}
print(f"{a.file}: {n} bars {str(D[0])[:10]}..{str(D[-1])[:10]}; atr={a.atr}; median ATR/close {np.median(atr[100:] / c[100:]) * 100:.2f}%; scoring from {str(D[S0])[:10]}")
res = {}
for sn, sig in sets.items():
    print(f"\n######## {sn}: signals {len(sig)} (fresh {sum(fresh[t] for t in sig)})")
    for kind, name in (("fixed", "fixed 1.5/3.5 ATR*"), ("chand", "chandelier 1.5 ATR*"), ("line", "close back below broken line (+1.5 ATR hard stop)"), ("swing", "swing-low trail N=3 (+1.5 ATR hard stop)"), ("x921", "9/21 cross-down once armed (+1.5 ATR hard stop)")):
        rows = [(t, sim(t + 1, kind)) for t in sig]; rows = [(t, r) for t, r in rows if r]
        lab = np.array([fresh[t] for t, _ in rows]); R = np.array([r[0] for _, r in rows]) * 100; H = np.array([r[1] for _, r in rows]); yy = pd.to_datetime(D[[t + 1 for t, _ in rows]]).year.values
        print(f"=== {name} ===")
        for g, gl in ((True, "fresh 9/21 cross <=5 bars"), (False, "other")):
            m = lab == g
            if m.sum() == 0: print(f"  {gl:26s} n=0"); continue
            yrs = "  ".join(f"{y}:{R[m & (yy == y)].mean():+.2f}%[{(m & (yy == y)).sum()}]" for y in sorted(set(yy[m])))
            print(f"  {gl:26s} n={m.sum():3d} win {np.mean(R[m]>0)*100:4.1f}%  mean {R[m].mean():+.2f}%  median {np.median(R[m]):+.2f}%  hold {H[m].mean():4.1f}b | {yrs}")
        if lab.any() and (~lab).any():
            d0 = R[lab].mean() - R[~lab].mean(); cnt = sum((R[p].mean() - R[~p].mean()) >= d0 for p in (rng.permutation(lab) for _ in range(a.perms)))
            print(f"  fresh - other = {d0:+.2f}%   permutation p (one-sided) = {(cnt + 1) / (a.perms + 1):.3f}")
        res[(sn, kind)] = (lab.sum(), R[lab].mean() if lab.any() else np.nan, R[~lab].mean() if (~lab).any() else np.nan)
nF, mF, mO = res[("LINE>=mint", "fixed")]
c1 = nF >= 10; c2 = mF > 0; c3 = mF > mO
print(f"\nCRITERIA (primary cell): (1) fresh n>=10: {'PASS' if c1 else 'FAIL'} (n={nF})  (2) fresh mean>0: {'PASS' if c2 else 'FAIL'} ({mF:+.2f}%)  (3) fresh>other: {'PASS' if c3 else 'FAIL'} ({mF:+.2f}% vs {mO:+.2f}%)  => {'PASS' if (c1 and c2 and c3) else 'FAIL'}")

# ---------------- ONE-POSITION ANNUALIZED PORTFOLIO (added 2026-10-18) ----------------
# take-all (blended), fresh-only and other-only signals; one position at a time, buy next open, exits on closes (fill next open).
# daily mark-to-market; position held at a constant fraction W of equity (daily rebalanced); cost split across entry and exit bars.
# comparators: buy&hold, exposure-matched buy&hold (same fraction of time in market), random-entry null (same exit, same trade count, non-overlapping).
if not a.noport:
    sig_all = sorted(sets["LINE>=mint"]); YRS = (D[n - 1] - D[S0]).astype("timedelta64[D]").astype(int) / 365.25
    nbars = n - S0; bpy = nbars / YRS; HC = COST / 2
    def path(e, kind):
        j = walk(e, kind)
        if j is None: return None
        fo = j + 1 < n; x = j + 1 if fo else j
        r = [c[e] / o[e] - 1] + [c[k] / c[k - 1] - 1 for k in range(e + 1, (x - 1 if fo else x) + 1)]
        if fo: r.append(o[x] / c[x - 1] - 1)
        r = np.array(r); r[0] -= HC; r[-1] -= HC
        return x, r
    KINDS = ("fixed", "chand", "line", "swing", "x921")
    PATHS = {k: {e: pp for e in range(max(S0, 1), n - 2) if (pp := path(e, k)) is not None} for k in KINDS}
    rb = np.r_[0.0, c[1:] / c[:-1] - 1]
    def series(trades, kind):
        s = np.zeros(n)
        for e in trades:
            x, r = PATHS[kind][e]; s[e:e + len(r)] += r
        return s
    def select(sigs, kind):
        out, last = [], -1
        for t in sigs:
            e = t + 1
            if e <= last or e not in PATHS[kind]: continue
            out.append(e); last = PATHS[kind][e][0]
        return out
    def stats(s, W):
        d = W * s[S0:]; eq = np.cumprod(1 + d)
        return eq[-1] ** (1 / YRS) * 100 - 100, d.std() * np.sqrt(bpy) * 100, (eq / np.maximum.accumulate(np.r_[1.0, eq])[1:] - 1).min() * 100
    def null_cagr(kind, K, draws):
        pool = np.arange(max(S0, 1), n - 2); out = []
        for _ in range(draws):
            occ = np.zeros(n, bool); picked = []
            for e in rng.permutation(pool):
                x = PATHS[kind][e][0]
                if occ[e:x + 1].any(): continue
                occ[e:x + 1] = True; picked.append(e)
                if len(picked) == K: break
            out.append(stats(series(picked, kind), 1.0)[0])
        return np.array(out)
    print(f"\n######## ONE-POSITION PORTFOLIO: {str(D[S0])[:10]}..{str(D[-1])[:10]} ({YRS:.1f} y, {bpy:.0f} bars/yr), cost {a.cost:.0f} bps round trip ########")
    b1 = stats(rb, 1.0); b2 = stats(rb, a.stake)
    print(f"buy&hold @100%: CAGR {b1[0]:+.1f}%  vol {b1[1]:.1f}%  maxDD {b1[2]:.1f}%   |   @{a.stake*100:.0f}%: CAGR {b2[0]:+.1f}%  vol {b2[1]:.1f}%  maxDD {b2[2]:.1f}%")
    print(f"{'exit':6s} {'set':11s} {'n':>3s} {'/yr':>4s} {'hold':>5s} {'inMkt%':>6s} | @100%: {'CAGR':>6s} {'vol':>5s} {'maxDD':>6s} | @{a.stake*100:.0f}%: {'CAGR':>6s} {'vol':>5s} {'maxDD':>6s} | {'exp-B&H':>7s} | null@100% median [5,95]  pct")
    for kind in KINDS:
        for sname, sg in (("blended(all)", sig_all), ("fresh only", [t for t in sig_all if fresh[t]]), ("other only", [t for t in sig_all if not fresh[t]])):
            tr = select(sg, kind)
            if not tr: print(f"{kind:6s} {sname:11s} none"); continue
            s = series(tr, kind); inm = sum(len(PATHS[kind][e][1]) for e in tr) / nbars; hold = np.mean([len(PATHS[kind][e][1]) - 1 for e in tr])
            s1 = stats(s, 1.0); s2 = stats(s, a.stake); eb = stats(rb, inm)[0]; nul = null_cagr(kind, len(tr), a.draws) if kind != "line" else None
            nulstr = (f"{np.median(nul):+6.1f} [{np.percentile(nul,5):+.1f},{np.percentile(nul,95):+.1f}]  {(nul < s1[0]).mean()*100:3.0f}" if nul is not None else "   n/a (needs a line)")
            print(f"{kind:6s} {sname:11s} {len(tr):3d} {len(tr)/YRS:4.1f} {hold:5.1f} {inm*100:6.1f} | {s1[0]:+11.1f} {s1[1]:5.1f} {s1[2]:6.1f} | {s2[0]:+10.1f} {s2[1]:5.1f} {s2[2]:6.1f} | {eb:+7.1f} | {nulstr}")
