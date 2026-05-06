"""Phase 3: Univariate Analysis — distributions, predictive power, thresholds, plots."""
import pandas as pd
import numpy as np
from scipy import stats
from sklearn.metrics import roc_auc_score, roc_curve, f1_score, precision_score, recall_score
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

df = pd.read_csv("/tmp/research/outcomes.csv")

# Binary target
binary = df[df["net_outcome"].isin(["TP_HIT","SL_HIT"])].copy()
binary["target"] = (binary["net_outcome"] == "TP_HIT").astype(int)
print(f"Binary dataset: {len(binary)} rows, {binary['target'].sum()} TP_HIT, {(1-binary['target']).sum()} SL_HIT")

metrics = ["Score","MxV","RunUp","REL_VOL","RSI","ATRX","Gap","VWAP_dev","Volume","MarketCap","ScanPrice","Hour"]
# Rename ScanPrice for display
metric_display = {"ScanPrice": "Price"}

results = []

for metric in metrics:
    col = metric
    if col not in binary.columns:
        print(f"SKIP {metric}: not in columns")
        continue
    
    data = binary[[col,"target","drop_max_pct","net_outcome"]].dropna(subset=[col])
    if len(data) < 20:
        print(f"SKIP {metric}: only {len(data)} non-null")
        continue
    
    tp = data[data["target"]==1][col]
    sl = data[data["target"]==0][col]
    
    # A. Distribution stats
    def qstats(s):
        return {
            "mean": s.mean(), "median": s.median(), "std": s.std(),
            "q10": s.quantile(0.1), "q25": s.quantile(0.25), "q50": s.quantile(0.5),
            "q75": s.quantile(0.75), "q90": s.quantile(0.9)
        }
    tp_stats = qstats(tp)
    sl_stats = qstats(sl)
    
    # B. Predictive power
    pearson_r, _ = stats.pearsonr(data[col], data["drop_max_pct"])
    spearman_r, _ = stats.spearmanr(data[col], data["drop_max_pct"])
    mann_whitney_u, mann_whitney_p = stats.mannwhitneyu(tp, sl, alternative='two-sided')
    
    try:
        auc = roc_auc_score(data["target"], data[col])
    except:
        auc = 0.5
    
    # For metrics where LOWER value = more likely TP, flip AUC
    # AUC < 0.5 means the metric is inversely predictive
    auc_display = auc
    
    # C. Threshold optimization (F1 for hit_tp10)
    # Try many thresholds
    vals_sorted = np.sort(data[col].unique())
    best_f1 = 0
    best_thr = None
    best_prec = 0
    best_rec = 0
    best_n = 0
    
    for thr in vals_sorted:
        # Try both directions: >= thr and <= thr
        for direction in [">=", "<="]:
            if direction == ">=":
                pred = (data[col] >= thr).astype(int)
            else:
                pred = (data[col] <= thr).astype(int)
            
            n_qual = pred.sum()
            if n_qual < 5:
                continue
            
            f1 = f1_score(data["target"], pred, zero_division=0)
            if f1 > best_f1:
                best_f1 = f1
                best_thr = f"{direction} {thr:.2f}"
                best_prec = precision_score(data["target"], pred, zero_division=0)
                best_rec = recall_score(data["target"], pred, zero_division=0)
                best_n = n_qual
    
    insufficient = best_n < 20
    
    results.append({
        "metric": metric,
        "n_total": len(data),
        "n_tp": len(tp),
        "n_sl": len(sl),
        "mean_tp": round(tp_stats["mean"], 4),
        "mean_sl": round(sl_stats["mean"], 4),
        "median_tp": round(tp_stats["median"], 4),
        "median_sl": round(sl_stats["median"], 4),
        "pearson_r": round(pearson_r, 4),
        "spearman_r": round(spearman_r, 4),
        "mann_whitney_p": round(mann_whitney_p, 6),
        "auc": round(auc_display, 4),
        "best_threshold": best_thr if not insufficient else "insufficient data",
        "precision_at_thr": round(best_prec, 4) if not insufficient else None,
        "recall_at_thr": round(best_rec, 4) if not insufficient else None,
        "n_qualified": best_n,
        "best_f1": round(best_f1, 4),
    })
    
    # D. Plot
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # Histogram by outcome
    ax = axes[0]
    ax.hist(tp, bins=20, alpha=0.6, label=f"TP_HIT (n={len(tp)})", color="green")
    ax.hist(sl, bins=20, alpha=0.6, label=f"SL_HIT (n={len(sl)})", color="red")
    ax.set_xlabel(metric)
    ax.set_ylabel("Count")
    ax.set_title(f"{metric} Distribution by Outcome")
    ax.legend()
    ax.axvline(tp.mean(), color="green", linestyle="--", alpha=0.5)
    ax.axvline(sl.mean(), color="red", linestyle="--", alpha=0.5)
    
    # ROC curve
    ax = axes[1]
    try:
        fpr, tpr, _ = roc_curve(data["target"], data[col])
        ax.plot(fpr, tpr, 'b-', label=f"AUC = {auc_display:.3f}")
        ax.plot([0,1],[0,1],'k--', alpha=0.3)
    except:
        ax.text(0.5, 0.5, "Cannot compute ROC", ha='center')
    ax.set_xlabel("FPR")
    ax.set_ylabel("TPR")
    ax.set_title(f"{metric} ROC Curve")
    ax.legend()
    
    plt.tight_layout()
    plt.savefig(f"/tmp/research/univariate_plots/{metric}.png", dpi=100)
    plt.close()
    
    print(f"{metric:>15}: AUC={auc_display:.3f}, p={mann_whitney_p:.4f}, mean_tp={tp_stats['mean']:.2f}, mean_sl={sl_stats['mean']:.2f}")

# Save results
res_df = pd.DataFrame(results)
res_df.to_csv("/tmp/research/univariate_analysis.csv", index=False)

print(f"\n{'='*60}")
print("UNIVARIATE ANALYSIS SUMMARY")
print(f"{'='*60}")
print(res_df.sort_values("auc", ascending=False)[["metric","auc","mann_whitney_p","best_threshold","best_f1","n_qualified"]].to_string(index=False))

# Checkpoint
with open("/tmp/research/checkpoints/phase3.done","w") as f:
    f.write("done\n")
print("\n✓ Phase 3 complete")
