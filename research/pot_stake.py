#!/usr/bin/env python3
"""Combined pot at different stakes per trade: runs the plan (swing-low trail + intraday 1.5 ATR stop, 3-touch lines, daily) on each file via stop_poke_test.py,
then adds the three symbols' daily returns at the same stake.  Also counts how often 1 / 2 / 3 positions are open at once.
    python3 research/pot_stake.py data/iau.csv data/pplt.csv data/btc.csv --from 2015-06-01 --recent 2024-11-01
Needs stop_poke_test.py and pivot_line_breakouts.py in the same folder."""
import sys, os, argparse, subprocess, tempfile, numpy as np, pandas as pd
ap = argparse.ArgumentParser(); ap.add_argument("files", nargs="+"); ap.add_argument("--from", dest="frm", default="2015-06-01")
ap.add_argument("--recent", default="2024-11-01"); ap.add_argument("--stakes", default="0.2,0.33,0.5"); a = ap.parse_args()
here = os.path.dirname(os.path.abspath(__file__)); ser = {}
for f in a.files:
    tmp = tempfile.mktemp(suffix=".npy")
    subprocess.run([sys.executable, os.path.join(here, "stop_poke_test.py"), os.path.abspath(f), "--from", a.frm, "--dump", tmp], cwd=here, check=True, capture_output=True)
    z = np.load(tmp); ser[os.path.basename(f)] = pd.Series(z[:, 1], index=pd.to_datetime(z[:, 0], unit="D")); os.remove(tmp)
u = sorted(set().union(*[s.index for s in ser.values()])); u = pd.DatetimeIndex(u)
R = pd.DataFrame({k: s.reindex(u).fillna(0.0) for k, s in ser.items()}); R = R[R.index >= a.frm]
def stat(r, W):
    yrs = (r.index[-1] - r.index[0]).days / 365.25; eq = (1 + W * r.sum(axis=1)).cumprod()
    return eq.iloc[-1] ** (1 / yrs) * 100 - 100, (eq / eq.cummax() - 1).min() * 100
for lab, r in (("full", R), (f"since {a.recent}", R[R.index >= a.recent])):
    print(f"\n{lab}: {r.index[0].date()}..{r.index[-1].date()}  symbols: {', '.join(R.columns)}")
    print(f"{'stake/trade':>12s} {'3 open = % of pot':>18s} {'pot CAGR':>9s} {'maxDD':>7s}")
    for W in map(float, a.stakes.split(",")):
        c, d = stat(r, W); print(f"{W*100:11.0f}% {W*len(R.columns)*100:17.0f}% {c:+9.1f} {d:7.1f}")
openn = (R != 0).sum(axis=1); print("\npositions open at once (share of days): " + ", ".join(f"{k}: {(openn == k).mean()*100:.1f}%" for k in range(0, len(R.columns) + 1)))