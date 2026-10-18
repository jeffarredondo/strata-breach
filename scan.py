#!/usr/bin/env python3
"""Line>=3 breakout scanner + swing-low trail monitor.  Same logic as line3_explore.py (true ATR, N=3 pivots, tol 0.5, spacing 5, wick poke <=1 ATR).

    python3 scan.py                         # IAU 4H, PPLT 4H, BTC-USD 1D, positions from positions.csv
    python3 scan.py --symbols IAU:4h,BTC-USD:1d --positions my.csv
    python3 scan.py --csv btc.csv --label BTCUSD --tf 1d      # test on a local Date,Open,High,Low,Close file

Only CLOSED bars are used.  Per symbol it prints:
  ENTRY  - last closed bar closed above a falling line with >=3 touches (buy at the next open); flags a fresh 9/21 cross (<=5 bars)
  WATCH  - otherwise, the nearest falling line (>=3 touches) still above price and how far away it is
  MODEL  - no input needed: replays the rules (take every signal, one position at a time, swing-low exit) over recent bars and shows the trail/hold/exit
           state of whatever position the rules would be holding right now
  OPEN   - optional: --positions YOUR_TRADE_LOG.csv (Symbol,TF,EntryTime,EntryPx[,ExitTime]; rows with no ExitTime are open; naive times = New York)
           gives the same trail/hold/exit readout for your actual entry
4H bars are built from Yahoo 1h bars (equities: 09:30-13:30 and 13:30-16:00 ET; crypto: 00/04/08.. UTC); check they line up with your chart.
"""
import argparse, os, sys
import numpy as np, pandas as pd

N, SPACING, LOOKBACK, POKE, TOL, MINT, HARD, CAP = 3, 5, 150, 1.0, 0.5, 3, 1.5, 120
ET = "America/New_York"
LABEL = {"BTC-USD": "BTCUSD"}
SHOW_WICKS = False


# ---------------------------------------------------------------- data
def rma(x, k):
    out = np.empty(len(x)); out[0] = x[0]
    for i in range(1, len(x)): out[i] = out[i - 1] + (x[i] - out[i - 1]) / k
    return out


def bin_end(ts, tf, crypto):
    if tf == "1d":
        return ts + pd.Timedelta(days=1) if crypto else ts.normalize() + pd.Timedelta(hours=16)
    if crypto: return ts + pd.Timedelta(hours=4)
    m = ts.hour * 60 + ts.minute
    return ts.normalize() + (pd.Timedelta(hours=13, minutes=30) if m < 13 * 60 + 30 else pd.Timedelta(hours=16))


def load_yahoo(sym, tf):
    import yfinance as yf
    crypto = sym.endswith("-USD")
    tk = yf.Ticker(sym)
    d = tk.history(period="5y", interval="1d", auto_adjust=False) if tf == "1d" else tk.history(period="730d", interval="1h", auto_adjust=False)
    d = d[["Open", "High", "Low", "Close"]].dropna()
    if d.empty: raise SystemExit(f"{sym}: no data from Yahoo")
    d.index = d.index.tz_convert("UTC") if crypto else d.index.tz_convert(ET)
    if tf == "4h":
        agg = {"Open": "first", "High": "max", "Low": "min", "Close": "last"}
        if crypto: d = d.resample("4h").agg(agg).dropna()
        else:
            mins = d.index.hour * 60 + d.index.minute
            d["bin"] = d.index.normalize() + pd.to_timedelta(np.where(mins < 13 * 60 + 30, 9 * 60 + 30, 13 * 60 + 30), unit="m")
            d = d.groupby("bin").agg(agg); d.index.name = None
    elif not crypto:
        d.index = d.index.normalize()
    now = pd.Timestamp.now(tz="UTC")
    closed = np.array([bin_end(t, tf, crypto) <= now for t in d.index])
    return d[closed], crypto


def load_csv(path):
    d = pd.read_csv(path, parse_dates=["Date"]).set_index("Date").sort_index()
    d.index = d.index.tz_localize("UTC"); return d[["Open", "High", "Low", "Close"]], True


class S:  # arrays for one symbol
    def __init__(s, d):
        s.idx = d.index; s.o, s.h, s.l, s.c = (d[k].values.astype(float) for k in ("Open", "High", "Low", "Close")); s.n = n = len(d)
        h, l, c = s.h, s.l, s.c
        pc = np.r_[c[0], c[:-1]]; tr = np.maximum(h - l, np.maximum(abs(h - pc), abs(l - pc))); s.atr = rma(tr, 14)
        ser = pd.Series(c); e9 = ser.ewm(span=9, adjust=False).mean().values; e21 = ser.ewm(span=21, adjust=False).mean().values
        on = e9 > e21; crossed = np.r_[False, on[1:] & ~on[:-1]]
        s.fresh = pd.Series(crossed).rolling(5, min_periods=1).max().values.astype(bool) & on
        s.PIV = np.array([i for i in range(N, n - N) if h[i] == h[i - N:i + N + 1].max() and h[i] > h[i - N:i].max()], int)
        s.PLOW = np.array([i for i in range(3, n - 3) if l[i] == l[i - 3:i + 4].min() and l[i] < l[i - 3:i].min()], int)


# ---------------------------------------------------------------- lines
def touches(s, ai, sl, P):
    pk = P[P >= ai]; dist = np.abs(s.h[pk] - (s.h[ai] + sl * (pk - ai))); tp = pk[dist <= TOL * s.atr[pk]]
    tb, last = [], -10 ** 9
    for x in tp:
        if x - last >= SPACING: tb.append(int(x)); last = x
    return tb


def find_line(s, t, mode):
    """mode 'cross': close[t] crossed above a valid falling line (best = most touches, then longest).
       mode 'watch': valid falling line still at/above close[t] (best = nearest to price)."""
    if t < 60: return None
    m = (s.PIV + N <= t - 1) & (s.PIV >= t - LOOKBACK); P = s.PIV[m]
    if len(P) < 2: return None
    ia, ib = np.triu_indices(len(P), 1); A, B = P[ia], P[ib]
    ok = (B - A >= SPACING) & (s.h[B] < s.h[A]); A, B = A[ok], B[ok]
    if len(A) == 0: return None
    sl_ = (s.h[B] - s.h[A]) / (B - A)
    L0 = s.h[A] + sl_ * (t - A); L1 = s.h[A] + sl_ * (t - 1 - A)
    if mode == "cross": sel = (s.c[t] > L0) & (s.c[t - 1] <= L1); end = t
    else: sel = s.c[t] <= L0; end = t + 1
    best = None
    for k in np.where(sel)[0]:
        ai, sl = A[k], sl_[k]; j = np.arange(ai, end); line = s.h[ai] + sl * (j - ai)
        if (s.c[j] > line).any() or ((s.h[j] - line) > POKE * s.atr[j]).any(): continue
        tb = touches(s, ai, sl, P); cnt = len(tb)
        if cnt < MINT: continue
        key = (cnt, t - ai) if mode == "cross" else (-(L0[k] - s.c[t]),)
        if best is None or key > best[0]:
            best = (key, dict(touches=cnt, tb=tb, anchor=ai, slope=sl, L_t=L0[k], L_next=s.h[ai] + sl * (t + 1 - ai)))
    return best[1] if best else None


# ---------------------------------------------------------------- positions
def trail(s, e, ent, j):
    """swing-low trail state after closed bar j (identical to line3_explore.walk 'swing')."""
    ae = s.atr[e - 1]; floor = ent - HARD * ae
    cand = s.PLOW[s.PLOW >= e]; ok = cand[cand + 3 <= j - 1]
    if len(ok):
        k = ok[np.argmax(s.l[ok])]; sw = s.l[k]
    else: k, sw = None, -np.inf
    lvl = max(floor, sw)
    return dict(level=lvl, floor=floor, swing=sw if k is not None else None, swing_bar=k, hit=s.c[j] <= lvl or (j - e) >= CAP)


def model_position(s, lookback=400):
    """What the rules (take every signal, one position at a time, swing-low exit) would be holding right now.  Returns entry bar index or None."""
    open_e = None; sig = None
    for j in range(max(60, s.n - lookback), s.n):
        if open_e is not None:
            if trail(s, open_e, s.o[open_e], j)["hit"]: open_e = None
            continue
        if j + 1 <= s.n - 1:
            g = find_line(s, j, "cross")
            if g: open_e = j + 1; sig = g
    return (open_e, sig) if open_e is not None else (None, None)


# ---------------------------------------------------------------- output
def tstr(ts, crypto, tf="4h"):
    if tf == "1d": return ts.strftime("%Y-%m-%d") + (" UTC" if crypto else "")
    return ts.tz_convert(ET).strftime("%Y-%m-%d %H:%M ET")


def report(label, tf, s, crypto, pos):
    t = s.n - 1; px = s.c[t]; ae = s.atr[t]; hdr = f"{label} {tf.upper()}"
    lines = [f"== {hdr}   last closed bar {tstr(s.idx[t], crypto, tf)}   close {px:.2f}   ATR {ae:.2f} ({ae / px * 100:.2f}%)   9/21: {'fresh cross' if s.fresh[t] else 'no fresh cross'} =="]
    action = []
    sig = find_line(s, t, "cross")
    if sig:
        lines.append(f"  ENTRY SIGNAL: closed above falling line {sig['L_t']:.2f} ({sig['touches']} touches, anchored {tstr(s.idx[sig['anchor']], crypto, tf)[:16]}). Buy at next open.")
        stop = px - HARD * ae; dist = HARD * ae / px
        lines.append(f"    fresh 9/21 cross: {'YES' if s.fresh[t] else 'no'}")
        lines.append(f"    SUGGESTED STOP {stop:.2f} (entry - 1.5 ATR, from ref close {px:.2f}; ATR {ae:.2f}). Distance {dist * 100:.1f}%; risk on a $1,000 stake ${1000 * dist:.0f} ({1000 * dist / 5000 * 100:.2f}% of a $5k pot).")
        lines.append(f"    After the fill, recompute: fill price - 1.5 x {ae:.2f}.  Disaster-stop option (wider, for close-based exits): fill - 2 ATR = fill - {2 * ae:.2f}.")
        if SHOW_WICKS: lines.append("    draw it through these wicks: " + ", ".join(f"{tstr(s.idx[b], crypto, tf)[:16]} high {s.h[b]:.2f}" for b in sig["tb"]))
        action.append(f"{label}: ENTRY SIGNAL{' (fresh 9/21)' if s.fresh[t] else ''}")
    else:
        w = find_line(s, t, "watch")
        if w: lines.append(f"  watch: nearest falling line (>=3 touches) {w['L_t']:.2f} now / {w['L_next']:.2f} next bar, {(w['L_t'] - px) / ae:+.1f} ATR ({(w['L_t'] / px - 1) * 100:+.1f}%) above close; {w['touches']} touches")
        else: lines.append("  watch: no valid falling line with >=3 touches above price")
    for p in pos:
        ts = p["ts"]; ent = p["px"]; tag = p.get("tag", "OPEN")
        e = p["e"] if "e" in p else int(s.idx.searchsorted(ts, side="right") - 1)
        if e < 1 or ts < s.idx[0]: lines.append(f"  {tag} @ {ent}: entry time is before the data window, cannot track"); continue
        if "e" not in p and ts >= bin_end(s.idx[-1], tf, crypto):
            lines.append(f"  {tag} @ {ent:.2f} ({tstr(ts, crypto, tf)}): entry bar not closed yet, trail starts after it closes  (1.5 ATR floor ~ {ent - HARD * s.atr[s.n - 1]:.2f})")
            action.append(f"{label}: open position, entry bar still forming"); continue
        if p.get("sig"):
            g = p["sig"]; ai = g["anchor"]
            if SHOW_WICKS: lines.append("    draw it through these wicks: " + ", ".join(f"{tstr(s.idx[b], crypto, tf)[:16]} high {s.h[b]:.2f}" for b in g["tb"]))
            lines.append(f"    signal bar {tstr(s.idx[e - 1], crypto, tf)}: closed above falling line {g['L_t']:.2f} ({g['touches']} touches; line starts at the swing high {tstr(s.idx[ai], crypto, tf)} high {s.h[ai]:.2f}; slope {g['slope']:+.3f}/bar); fresh 9/21: {'yes' if s.fresh[e - 1] else 'no'}")
        j = t; r = trail(s, e, ent, j)
        why = "swing low" if r["swing"] is not None and r["swing"] >= r["floor"] else "1.5 ATR floor"
        sw = f"swing low {r['swing']:.2f} @ {tstr(s.idx[r['swing_bar']], crypto, tf)[:16]}" if r["swing"] is not None else "no swing low confirmed yet"
        call = "EXIT at next open" if r["hit"] else "HOLD"
        lines.append(f"  {tag} @ {ent:.2f} ({tstr(ts, crypto, tf)}), bar {j - e + 1} of cap {CAP}, P&L {(px / ent - 1) * 100:+.2f}%")
        lines.append(f"    trail {r['level']:.2f} (binding: {why}; {sw}; floor {r['floor']:.2f})   close {px:.2f}   cushion {(px / r['level'] - 1) * 100:+.2f}%")
        lines.append(f"    >>> {call}" + ("   (cap reached)" if (j - e) >= CAP else ""))
        action.append(f"{label}: {call}" + (" (model position)" if tag != "OPEN" else ""))
    return lines, action


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbols", default="IAU:4h,PPLT:4h,BTC-USD:1d"); ap.add_argument("--positions", default=None, help="optional: your trade log CSV (Symbol,TF,EntryTime,EntryPx[,ExitTime]); rows with no ExitTime count as open")
    ap.add_argument("--no-model", action="store_true", help="skip the model position")
    ap.add_argument("--wicks", action="store_true", help="also print the wick touches of each signal line so you can draw it")
    ap.add_argument("--csv"); ap.add_argument("--label", default="TEST"); ap.add_argument("--tf", default="1d", choices=["1d", "4h"])
    a = ap.parse_args()
    global SHOW_WICKS; SHOW_WICKS = a.wicks
    pos_all = []
    if a.positions and os.path.exists(a.positions):
        pp = pd.read_csv(a.positions)
        if "ExitTime" in pp.columns: pp = pp[pp["ExitTime"].isna()]
        for _, r in pp.dropna(subset=["Symbol"]).iterrows():
            ts = pd.Timestamp(r["EntryTime"]); ts = ts.tz_localize(ET) if ts.tzinfo is None else ts
            pos_all.append(dict(sym=str(r["Symbol"]).strip(), tf=str(r.get("TF", "")).strip().lower(), ts=ts, px=float(r["EntryPx"])))
    jobs = [(a.label, a.tf, None)] if a.csv else [(LABEL.get(x.split(":")[0], x.split(":")[0]), x.split(":")[1].lower(), x.split(":")[0]) for x in a.symbols.split(",")]
    out, actions = [], []
    for label, tf, ysym in jobs:
        d, crypto = load_csv(a.csv) if a.csv else load_yahoo(ysym, tf)
        s = S(d); mine = [p for p in pos_all if p["sym"].upper() == label.upper()]
        me, sg = (None, None) if a.no_model else model_position(s)
        if me is not None: mine = mine + [dict(ts=s.idx[me], px=s.o[me], e=me, tag="MODEL", sig=sg)]
        lines, act = report(label, tf, s, crypto, mine); out += lines + [""]; actions += act or [f"{label}: nothing"]
    print("ACTIONS\n  " + "\n  ".join(actions) + "\n"); print("\n".join(out))
    print(f"(run {pd.Timestamp.now(tz=ET).strftime('%Y-%m-%d %H:%M ET')}; closed bars only; rules as tested in line3_explore.py)")


if __name__ == "__main__":
    main()
