"""Phase 4: Bivariate / Interactions Analysis."""
import pandas as pd
import numpy as np
from scipy import stats
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

df = pd.read_csv("/tmp/research/outcomes.csv")
binary = df[df["net_outcome"].isin(["TP_HIT","SL_HIT"])].copy()
binary["target"] = (binary["net_outcome"] == "TP_HIT").astype(int)

metrics = ["Score","MxV","RunUp","REL_VOL","RSI","ATRX","Gap","VWAP_dev","Volume","MarketCap","ScanPrice","Hour"]
available = [m for m in metrics if m in binary.columns and binary[m].notna().sum() > 20]

# A. Correlation matrix
corr_data = binary[available].dropna()
fig, axes = plt.subplots(1, 2, figsize=(18, 7))

# Pearson
pearson_corr = corr_data.corr(method='pearson')
sns.heatmap(pearson_corr, annot=True, fmt=".2f", cmap="RdBu_r", center=0, ax=axes[0], vmin=-1, vmax=1)
axes[0].set_title("Pearson Correlation")

# Spearman
spearman_corr = corr_data.corr(method='spearman')
sns.heatmap(spearman_corr, annot=True, fmt=".2f", cmap="RdBu_r", center=0, ax=axes[1], vmin=-1, vmax=1)
axes[1].set_title("Spearman Correlation")

plt.tight_layout()
plt.savefig("/tmp/research/correlation_matrix.png", dpi=100)
plt.close()

# Report high correlations
print("=== Highly correlated pairs (|r| > 0.7) ===")
for i in range(len(available)):
    for j in range(i+1, len(available)):
        r = pearson_corr.iloc[i,j]
        if abs(r) > 0.7:
            print(f"  {available[i]} x {available[j]}: Pearson={r:.3f}")
        r_s = spearman_corr.iloc[i,j]
        if abs(r_s) > 0.7:
            print(f"  {available[i]} x {available[j]}: Spearman={r_s:.3f}")

# B. Top 5 metrics by AUC — from Phase 3
# AUC order: ATRX, REL_VOL, RunUp, Volume, MarketCap
top5 = ["ATRX","REL_VOL","RunUp","Volume","MarketCap"]
top5 = [m for m in top5 if m in available]

print(f"\n=== Interaction analysis for top pairs ===")
interactions = []

for i in range(len(top5)):
    for j in range(i+1, len(top5)):
        a, b = top5[i], top5[j]
        pair_data = binary[[a, b, "target"]].dropna()
        if len(pair_data) < 20:
            continue
        
        # Bucket by quartiles
        try:
            pair_data[f"{a}_q"] = pd.qcut(pair_data[a], 4, labels=["Q1","Q2","Q3","Q4"], duplicates='drop')
            pair_data[f"{b}_q"] = pd.qcut(pair_data[b], 4, labels=["Q1","Q2","Q3","Q4"], duplicates='drop')
        except:
            continue
        
        # Heatmap of TP_HIT rate
        pivot = pair_data.groupby([f"{a}_q", f"{b}_q"])["target"].agg(["mean","count"]).reset_index()
        pivot_mean = pivot.pivot(index=f"{a}_q", columns=f"{b}_q", values="mean")
        pivot_count = pivot.pivot(index=f"{a}_q", columns=f"{b}_q", values="count")
        
        fig, ax = plt.subplots(figsize=(8, 6))
        # Annotate with both rate and count
        annot = pivot_mean.copy()
        for ri in annot.index:
            for ci in annot.columns:
                rate = pivot_mean.loc[ri, ci] if not pd.isna(pivot_mean.loc[ri, ci]) else 0
                cnt = pivot_count.loc[ri, ci] if not pd.isna(pivot_count.loc[ri, ci]) else 0
                annot.loc[ri, ci] = f"{rate:.0%}\n(n={cnt:.0f})"
        
        sns.heatmap(pivot_mean, annot=annot, fmt="", cmap="RdYlGn", vmin=0, vmax=1, ax=ax)
        ax.set_title(f"TP_HIT Rate: {a} x {b}")
        plt.tight_layout()
        plt.savefig(f"/tmp/research/interactions/{a}_{b}.png", dpi=100)
        plt.close()
        
        # Best cell
        best_cell = pivot.loc[pivot["mean"].idxmax()] if len(pivot) > 0 else None
        if best_cell is not None:
            interactions.append({
                "pair": f"{a} x {b}",
                "best_bucket": f"{a}={best_cell[f'{a}_q']}, {b}={best_cell[f'{b}_q']}",
                "tp_rate": round(best_cell["mean"], 4),
                "n": int(best_cell["count"]),
            })
            print(f"  {a} x {b}: best bucket = {best_cell[f'{a}_q']},{best_cell[f'{b}_q']} → TP rate={best_cell['mean']:.1%} (n={best_cell['count']:.0f})")

# C. MarketCap stratification
print(f"\n=== MarketCap Stratification ===")
mcap_col = "MarketCap"
if mcap_col in binary.columns:
    mc = binary.copy()
    mc[mcap_col] = mc[mcap_col].fillna(0)
    
    def mcap_bucket(v):
        if v < 50e6: return "<$50M"
        elif v < 500e6: return "$50M-$500M"
        elif v < 5e9: return "$500M-$5B"
        else: return "$5B+"
    
    mc["mcap_bucket"] = mc[mcap_col].apply(mcap_bucket)
    
    for bucket in ["<$50M", "$50M-$500M", "$500M-$5B", "$5B+"]:
        sub = mc[mc["mcap_bucket"] == bucket]
        if len(sub) < 5:
            print(f"  {bucket}: n={len(sub)} (insufficient)")
            continue
        tp_rate = sub["target"].mean()
        avg_score = sub["Score"].mean() if "Score" in sub.columns else None
        avg_mxv = sub["MxV"].mean() if "MxV" in sub.columns else None
        avg_runup = sub["RunUp"].mean() if "RunUp" in sub.columns else None
        print(f"  {bucket}: n={len(sub)}, TP rate={tp_rate:.1%}, avg Score={avg_score:.1f}, avg MxV={avg_mxv:.0f}, avg RunUp={avg_runup:.1f}")
        
        interactions.append({
            "pair": f"MarketCap_strat",
            "best_bucket": bucket,
            "tp_rate": round(tp_rate, 4),
            "n": len(sub),
        })

pd.DataFrame(interactions).to_csv("/tmp/research/interactions.csv", index=False)

with open("/tmp/research/checkpoints/phase4.done","w") as f:
    f.write("done\n")
print("\n✓ Phase 4 complete")
