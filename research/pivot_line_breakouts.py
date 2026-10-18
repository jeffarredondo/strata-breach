#!/usr/bin/env python3
"""Swing-pivot falling-resistance-line breakouts (long only) with several exit rules and a matched-random-entry null.
    python pivot_line_breakouts.py iau_train.csv [--tols 0.2,0.35,0.5] [--min-touches 3] [--n 3] [--spacing 5] [--poke 1.0]

LINE: swing highs (highest high over N bars each side, confirmed N bars later).  A line = two confirmed pivot highs (b later and lower than a, >= spacing bars apart).
      Valid at bar t if no CLOSE since a is above it and no high pokes more than --poke ATR above it.  Touch = confirmed pivot high within tol*ATR of the line
      (wick counts, either side), touches >= spacing bars apart, anchors included.  Need >= min-touches.
EVENT: close[t] above line (first time), close[t+1] above line (confirmation) -> buy at open[t+2].  One position at a time.
EXITS (decided on close, filled next open, 2 bps/side, cap 120 bars unless noted).  R = 1.5*ATR(14) at entry, so R is comparable across exits:
  E1 fixed   stop entry-1.5ATR / target +2.33R
  E2 chand3  highest close since entry - 3 ATR (ATR fixed at entry)
  E3 chand2  same, 2 ATR
  E4 stflip  supertrend(10,3) flips short
  E5 linefl  max(old line value, chand3)   [floor under price = the broken line]
  E6 hold10  sell after 10 bars, no stop
  E7 don10   close below the lowest low of the previous 10 bars
NULL: same exit, same number of trades, entry bar drawn uniformly at random (overlap allowed); percentile of the real mean R in that null.
"""
import argparse, numpy as np, pandas as pd

ap = argparse.ArgumentParser(); ap.add_argument("file")
ap.add_argument("--tols", default="0.2,0.35,0.5"); ap.add_argument("--min-touches", type=int, default=3)
ap.add_argument("--n", type=int, default=3); ap.add_argument("--spacing", type=int, default=5); ap.add_argument("--lookback", type=int, default=150)
ap.add_argument("--poke", type=float, default=1.0); ap.add_argument("--maxhold", type=int, default=120)
ap.add_argument("--draws", type=int, default=2000); ap.add_argument("--seed", type=int, default=1); ap.add_argument("--cost", type=float, default=2.0)
ap.add_argument("--out", default=None)
a = ap.parse_args(); rng = np.random.default_rng(a.seed)

df = pd.read_csv(a.file, parse_dates=["Date"]).sort_values("Date").reset_index(drop=True)
D = df["Date"].values; o, h, l, c = (df[k].values.astype(float) for k in ("Open", "High", "Low", "Close")); n = len(df); N = a.n
pc = np.r_[c[0], c[:-1]]; tr = np.maximum(h - l, np.maximum(abs(h - pc), abs(l - pc)))
def rma(x, k):
    out = np.empty(len(x)); out[0] = x[0]
    for i in range(1, len(x)): out[i] = out[i - 1] + (x[i] - out[i - 1]) / k
    return out
atr = rma(tr, 14)
# supertrend (10,3)
a10 = rma(tr, 10); hl2 = (h + l) / 2; ub = hl2 + 3 * a10; lb = hl2 - 3 * a10
fu, fl, st = ub.copy(), lb.copy(), np.ones(n, int)
for i in range(1, n):
    fu[i] = ub[i] if (ub[i] < fu[i - 1] or c[i - 1] > fu[i - 1]) else fu[i - 1]
    fl[i] = lb[i] if (lb[i] > fl[i - 1] or c[i - 1] < fl[i - 1]) else fl[i - 1]
    if st[i - 1] == 1: st[i] = -1 if c[i] < fl[i] else 1
    else: st[i] = 1 if c[i] > fu[i] else -1

ispiv = np.zeros(n, bool)
for i in range(N, n - N):
    w = h[i - N:i + N + 1]
    if h[i] == w.max() and h[i] > h[i - N:i].max(): ispiv[i] = True
PIV = np.where(ispiv)[0]
COST = a.cost * 2e-4 / 2 * 2  # round trip as a fraction (2 bps/side)
COST = 2 * a.cost * 1e-4

EX = ["E1 fixed", "E2 chand3", "E3 chand2", "E4 stflip", "E5 linefl", "E6 hold10", "E7 don10"]
def sim(e, kind, f0=None, sl=0.0):
    """buy open[e]; returns (net return, R, bars held, exit bar)"""
    if e >= n - 1: return None
    ent = o[e]; ae = atr[e - 1]; Runit = 1.5 * ae / ent
    hc = c[e]; x = None
    for j in range(e, n):
        hc = max(hc, c[j]); held = j - e + 1; hit = False
        if kind == 0: hit = c[j] <= ent - 1.5 * ae or c[j] >= ent + 2.33 * 1.5 * ae
        elif kind == 1: hit = c[j] <= hc - 3 * ae
        elif kind == 2: hit = c[j] <= hc - 2 * ae
        elif kind == 3: hit = st[j] == -1
        elif kind == 4: hit = c[j] <= max(hc - 3 * ae, f0 + sl * (j - e))
        elif kind == 5: hit = held >= 10
        elif kind == 6: hit = j >= 10 and c[j] < l[j - 10:j].min()
        cap = 10 if kind == 5 else a.maxhold
        if hit or held >= cap or j == n - 1:
            x = j + 1 if j + 1 < n else j; px = o[x] if j + 1 < n else c[j]
            r = px / ent - 1 - COST
            return r, r / Runit, x - e, x
    return None

CONF = True
def find_events(tol, mint):
    ev = []
    for t in range(a.lookback0 if hasattr(a, "lookback0") else 60, n - 3):
        m = (PIV + N <= t - 1) & (PIV >= t - a.lookback); P = PIV[m]
        if len(P) < 2: continue
        ia, ib = np.triu_indices(len(P), 1); A = P[ia]; B = P[ib]
        ok = (B - A >= a.spacing) & (h[B] < h[A]); A, B = A[ok], B[ok]
        if len(A) == 0: continue
        s = (h[B] - h[A]) / (B - A)
        L0 = h[A] + s * (t - A); L1 = h[A] + s * (t - 1 - A); L2 = h[A] + s * (t + 1 - A)
        cross = (c[t] > L0) & (c[t - 1] <= L1) & ((c[t + 1] > L2) | (not CONF))
        best = None
        for k in np.where(cross)[0]:
            ai, sl = A[k], s[k]; j = np.arange(ai, t); line = h[ai] + sl * (j - ai)
            if (c[j] > line).any() or ((h[j] - line) > a.poke * atr[j]).any(): continue
            pk = P[P >= ai]; dist = np.abs(h[pk] - (h[ai] + sl * (pk - ai))); tp = pk[dist <= tol * atr[pk]]
            cnt, last = 0, -10 ** 9
            for xx in tp:
                if xx - last >= a.spacing: cnt += 1; last = xx
            if cnt >= mint:
                cand = (cnt, t - ai, ai, sl)
                if best is None or cand[:2] > best[:2]: best = cand
        if best is not None and t + 2 < n - 1:
            cnt, span, ai, sl = best; e = t + 2
            ev.append(dict(t=t, e=e, date=D[e], touches=cnt, span=span, L_e=h[ai] + sl * (e - ai), slope=sl, dist=(o[e] - (h[ai] + sl * (e - ai))) / atr[e - 1]))
    return ev

# table of sims for every bar (null) for kinds without a line
ALL = {}
for k in (0, 1, 2, 3, 5, 6):
    arr = np.full(n, np.nan)
    for e in range(60, n - 2):
        r = sim(e, k)
        if r: arr[e] = r[1]
    ALL[k] = arr
valid = np.arange(60, n - 2)

def boot(x, B=2000):
    x = np.asarray(x); m = [rng.choice(x, len(x)).mean() for _ in range(B)]; return np.percentile(m, [5, 95])

def run(tol, mint):
    ev = find_events(tol, mint)
    yrs = (pd.Timestamp(D[-1]) - pd.Timestamp(D[0])).days / 365.25
    print(f"\n=== tol {tol} ATR  min touches {mint}  raw events {len(ev)} ({len(ev)/yrs:.1f}/yr) ===")
    if len(ev) < 3: print("too few"); return None
    dmed = np.median([x["dist"] for x in ev]); smed = np.median([x["slope"] for x in ev])
    rows = []
    for k, name in enumerate(EX):
        taken, last = [], -1
        for x in ev:
            if x["e"] <= last: continue
            r = sim(x["e"], k, x["L_e"], x["slope"])
            if r is None: continue
            taken.append((x, r)); last = r[3]
        if not taken: continue
        R = np.array([r[1] for _, r in taken]); ret = np.array([r[0] for _, r in taken]); hold = np.array([r[2] for _, r in taken])
        if k == 4:
            arr = np.full(n, np.nan)
            for e in range(60, n - 2):
                rr = sim(e, 4, o[e] - dmed * atr[e - 1], smed)
                if rr: arr[e] = rr[1]
            pool = arr[valid]
        else: pool = ALL[k][valid]
        pool = pool[~np.isnan(pool)]
        nul = np.array([rng.choice(pool, len(R)).mean() for _ in range(a.draws)])
        pct = (nul < R.mean()).mean() * 100; lo, hi = boot(R)
        yr = pd.to_datetime([x["date"] for x, _ in taken]).year.values
        e1 = R[yr <= 2011].mean() if (yr <= 2011).any() else np.nan; e2 = R[yr >= 2012].mean() if (yr >= 2012).any() else np.nan
        rows.append((name, len(R), (R > 0).mean() * 100, R.mean(), lo, hi, np.median(R), ret.mean() * 100, hold.mean(), nul.mean(), pct, e1, e2, (yr <= 2011).sum(), (yr >= 2012).sum()))
    print(f"{'exit':10s} {'n':>3s} {'win%':>5s} {'meanR':>6s} {'90%CI':>14s} {'medR':>6s} {'ret%':>6s} {'hold':>5s} | {'nullR':>6s} {'pct':>4s} | {'R06-11':>6s}(n) {'R12-18':>6s}(n)")
    for r in rows:
        print(f"{r[0]:10s} {r[1]:3d} {r[2]:5.1f} {r[3]:+6.2f} [{r[4]:+5.2f},{r[5]:+5.2f}] {r[6]:+6.2f} {r[7]:+6.2f} {r[8]:5.1f} | {r[9]:+6.2f} {r[10]:4.0f} | {r[11]:+6.2f}({r[13]:2d}) {r[12]:+6.2f}({r[14]:2d})")
    cnt_by_year = pd.Series([pd.Timestamp(x['date']).year for x in ev]).value_counts().sort_index()
    print("raw events by year:", dict(cnt_by_year)); print(f"median entry distance above line: {dmed:+.2f} ATR; touches median {np.median([x['touches'] for x in ev]):.0f}")
    if a.out: pd.DataFrame(ev).to_csv(f"{a.out}_tol{tol}_m{mint}.csv", index=False)
    return ev

if __name__ == "__main__":
    print(f"{a.file}: {df['Date'].iloc[0].date()}..{df['Date'].iloc[-1].date()}  {n} bars, {len(PIV)} pivot highs (N={N})")
    for t in [float(x) for x in a.tols.split(",")]: run(t, a.min_touches)
