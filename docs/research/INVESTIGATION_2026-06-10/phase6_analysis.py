#!/usr/bin/env python3
"""Phase 6 — research validity & economics on decided v2 rows (local CSVs only)."""
import os
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.expanduser("~/RidingHighPro"))
from config import TP_THRESHOLD_FRAC, SL_THRESHOLD_FRAC

BASE = os.path.expanduser("~/RidingHighPro/docs/research/INVESTIGATION_2026-06-10")
rng = np.random.default_rng(42)

frames = []
for p in [f"{BASE}/post_analysis_2026-04.csv", f"{BASE}/post_analysis_2026-05.csv",
          "/tmp/rh_artifact/post_analysis_27312259524/post_analysis_2026-06-10_18-09.csv"]:
    frames.append(pd.read_csv(p, dtype=str))
df = pd.concat(frames, ignore_index=True)
df = df[df["score_version"] == "v2"].copy()

def num(s):
    return pd.to_numeric(s.astype(str).str.replace('%', '').str.replace(',', '').str.replace('$', ''), errors="coerce")

for c in ["ScanPrice", "Score", "MxV", "RunUp", "RSI", "ATRX", "REL_VOL", "Volume_raw",
          "RealFloat_M", "Float%", "PriceToHigh", "D1_Open"] + \
         [f"D{i}_{k}" for i in range(1, 6) for k in ("High", "Low")]:
    df[c + "_n"] = num(df[c])

def classify_walk(sp, row, pref=""):
    """Return (cls, resolution_day). Mirrors utils.classify_trade."""
    if sp is None or not np.isfinite(sp) or sp <= 0:
        return "PENDING", None
    for i in range(1, 6):
        if not np.isfinite(row[f"D{i}_Low_n"]) or not np.isfinite(row[f"D{i}_High_n"]):
            return "PENDING", None
    tp, sl = sp * (1 - TP_THRESHOLD_FRAC), sp * (1 + SL_THRESHOLD_FRAC)
    for i in range(1, 6):
        lo, hi = row[f"D{i}_Low_n"], row[f"D{i}_High_n"]
        tp_hit, sl_hit = lo <= tp, hi >= sl
        if tp_hit and sl_hit: return "WHIPSAW", i
        if sl_hit: return "LOSS", i
        if tp_hit: return "WIN", i
    return "NO_TOUCH", 5

res = df.apply(lambda r: classify_walk(r["ScanPrice_n"], r), axis=1)
df["cls"] = [a for a, b in res]; df["rday"] = [b for a, b in res]
dec = df[df["cls"].isin(["WIN", "LOSS"])].copy()
dec["win"] = (dec["cls"] == "WIN").astype(int)
n = len(dec); wr = dec["win"].mean()
print(f"=== decided v2: n={n}, WR={wr:.4f} (WHIPSAW excluded: {len(df[df.cls=='WHIPSAW'])})")

# ── (א) Pearson r Score vs win + permutation p ──────────────────────────
x = dec["Score_n"].values.astype(float); y = dec["win"].values.astype(float)
r_obs = np.corrcoef(x, y)[0, 1]
perm = np.empty(10000)
for k in range(10000):
    perm[k] = np.corrcoef(x, rng.permutation(y))[0, 1]
p_perm = (np.abs(perm) >= abs(r_obs)).mean()
print(f"\n(א) Pearson r(Score,WIN)={r_obs:.4f} | permutation p (10000 shuffles, two-sided)={p_perm:.4f}")

# ── (ב) random-within-passers vs Score-selection, Wilson 95% ────────────
def wilson(k, m, z=1.96):
    if m == 0: return (float('nan'),) * 2
    ph = k / m
    den = 1 + z*z/m
    ctr = (ph + z*z/(2*m)) / den
    hw = z*np.sqrt(ph*(1-ph)/m + z*z/(4*m*m)) / den
    return ctr-hw, ctr+hw

med = dec["Score_n"].median()
top = dec[dec["Score_n"] >= med]; rest = dec[dec["Score_n"] < med]
k1, m1 = top["win"].sum(), len(top)
k0, m0 = dec["win"].sum(), len(dec)
lo1, hi1 = wilson(k1, m1); lo0, hi0 = wilson(k0, m0)
print(f"\n(ב) baseline random-within-passers: WR={k0/m0:.3f} [{lo0:.3f},{hi0:.3f}] n={m0}")
print(f"    Score>=median({med:.1f}): WR={k1/m1:.3f} [{lo1:.3f},{hi1:.3f}] n={m1}")
for q, lbl in [(0.75, "top quartile"), (0.9, "top decile")]:
    thr = dec["Score_n"].quantile(q)
    sub = dec[dec["Score_n"] >= thr]
    l, h = wilson(sub["win"].sum(), len(sub))
    print(f"    Score>=q{int(q*100)}({thr:.1f}): WR={sub['win'].mean():.3f} [{l:.3f},{h:.3f}] n={len(sub)}")
# permutation diff test top-half vs all
d_obs = k1/m1 - k0/m0
dperm = np.empty(10000)
yv = dec["win"].values
for k in range(10000):
    pick = rng.choice(n, size=m1, replace=False)
    dperm[k] = yv[pick].mean() - wr
p_d = (np.abs(dperm) >= abs(d_obs)).mean()
print(f"    diff(top-half - random)={d_obs:+.3f}, permutation p={p_d:.4f}")

# ── (ג) cost model ──────────────────────────────────────────────────────
SLIP = 0.01
out = {}
for borrow in (0.5, 2.0, 5.0):
    pnls = []
    for _, r in dec.iterrows():
        sp = r["ScanPrice_n"]; d = int(r["rday"])
        fill = sp * (1 - SLIP)                      # short entry, adverse
        exitp = sp * (1 - TP_THRESHOLD_FRAC) if r["win"] else sp * (1 + SL_THRESHOLD_FRAC)
        cover = exitp * (1 + SLIP)                  # cover, adverse
        gross = (fill - cover) / fill               # short pnl fraction
        bcost = borrow * d / 365.0
        pnls.append(gross - bcost)
    pnls = np.array(pnls)
    out[borrow] = pnls
    print(f"\n(ג) borrow {borrow*100:.0f}%/yr: expectancy/trade={pnls.mean()*100:+.2f}% "
          f"(median {np.median(pnls)*100:+.2f}%), total on $1000/trade=${pnls.sum()*1000:+,.0f}, "
          f"share>0: {(pnls>0).mean()*100:.0f}%")
zero = dec.apply(lambda r: ((r['ScanPrice_n']*(1-SLIP)) - ((r['ScanPrice_n']*(1-TP_THRESHOLD_FRAC) if r['win'] else r['ScanPrice_n']*(1+SL_THRESHOLD_FRAC))*(1+SLIP)))/(r['ScanPrice_n']*(1-SLIP)), axis=1)
print(f"(ג) slippage-only (no borrow): expectancy={zero.mean()*100:+.2f}%/trade")
print(f"(ג) avg holding days={dec['rday'].mean():.2f}")

# ── (ד) look-ahead: ScanPrice entry vs D1_Open entry ────────────────────
res2 = df.apply(lambda r: classify_walk(r["D1_Open_n"], r), axis=1)
df["cls_d1"] = [a for a, b in res2]
both = df[df["cls"].isin(["WIN","LOSS"]) & df["cls_d1"].isin(["WIN","LOSS"])]
wr_scan = (both["cls"] == "WIN").mean(); wr_d1 = (both["cls_d1"] == "WIN").mean()
print(f"\n(ד) same {len(both)} rows decided under both entries: WR scan-entry={wr_scan:.3f} vs D1_Open-entry={wr_d1:.3f} (Δ={wr_scan-wr_d1:+.3f})")
d1all = df[df["cls_d1"].isin(["WIN","LOSS"])]
print(f"    all D1-decided n={len(d1all)}: WR={(d1all['cls_d1']=='WIN').mean():.3f} | scan-decided n={n}: WR={wr:.3f}")

# ── (ה) ROCKET_GUARD out-of-sample (ScanDate >= 2026-05-16) ─────────────
oos = dec[dec["ScanDate"] >= "2026-05-16"]
blk = oos[(oos["RunUp_n"] >= 50) & (oos["PriceToHigh_n"] >= -10)]
print(f"\n(ה) ROCKET_GUARD OOS (>=2026-05-16): n={len(oos)}, blocked={len(blk)} "
      f"-> correct(LOSS)={int((blk['win']==0).sum())}, wrong(WIN)={int((blk['win']==1).sum())}")
print(blk[["Ticker","ScanDate","RunUp_n","PriceToHigh_n","cls"]].to_string() if len(blk) else "    (none blocked)")

# ── (ו) metric correlations + Bonferroni ────────────────────────────────
from math import erf, sqrt
metrics = {"Volume": "Volume_raw_n", "Price": "ScanPrice_n", "Float%": "Float%_n",
           "RSI": "RSI_n", "ATRX": "ATRX_n", "REL_VOL": "REL_VOL_n",
           "RunUp": "RunUp_n", "MxV": "MxV_n"}
M = len(metrics)
print(f"\n(ו) metric vs WIN correlations (n per metric varies w/ NaN), Bonferroni x{M}:")
for name, col in metrics.items():
    sub = dec[[col, "win"]].dropna()
    if len(sub) < 10: print(f"  {name}: insufficient"); continue
    r = np.corrcoef(sub[col], sub["win"])[0, 1]
    # permutation p
    xv, yv2 = sub[col].values, sub["win"].values.astype(float)
    pp = np.mean([abs(np.corrcoef(xv, rng.permutation(yv2))[0, 1]) >= abs(r) for _ in range(2000)])
    p_bonf = min(1.0, pp * M)
    sig = "**" if p_bonf < 0.05 else ""
    print(f"  {name:<8} r={r:+.3f}  p_perm={pp:.4f}  p_bonf={p_bonf:.4f} {sig} (n={len(sub)})")

# ── (ז) market regime split (May-June only) ─────────────────────────────
mc = pd.concat([pd.read_csv(f"{BASE}/market_context_2026-05.csv", dtype=str),
                pd.read_csv(f"{BASE}/market_context_2026-06.csv", dtype=str)], ignore_index=True)
mc["date"] = mc["Timestamp"].astype(str).str[:10]
mc["VIX"] = num(mc["VIX_Close"])
daily = mc.groupby("date").agg(spy_dir=("SPY_Direction", "last"), vix=("VIX", "last")).reset_index()
dj = dec.merge(daily, left_on="ScanDate", right_on="date", how="inner")
print(f"\n(ז) regime join (May-June rows matched: {len(dj)}/{len(dec[dec['ScanDate']>='2026-05-01'])}):")
if len(dj):
    print(dj.groupby("spy_dir")["win"].agg(["count", "mean"]).to_string())
    dj["vix_b"] = pd.cut(dj["vix"], [0, 15, 20, 100], labels=["VIX<15", "15-20", ">20"])
    print(dj.groupby("vix_b", observed=True)["win"].agg(["count", "mean"]).to_string())

# sensitivity: exclude reverse-split suspects
sus = {("TDIC","2026-05-12"), ("INHD","2026-06-08"), ("PAVS","2026-06-08"),
       ("PBM","2026-04-16"), ("WNW","2026-04-16"), ("ELPW","2026-04-22"), ("GNLN","2026-04-22")}
mask = ~dec.apply(lambda r: (r["Ticker"], r["ScanDate"]) in sus, axis=1)
print(f"\nsensitivity excl split-suspects: n={mask.sum()}, WR={dec[mask]['win'].mean():.3f} (was {wr:.3f})")
EOF_MARKER = None
