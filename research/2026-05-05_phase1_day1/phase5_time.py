"""Phase 5: Time-of-Day Analysis."""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

df = pd.read_csv("/tmp/research/outcomes.csv")
binary = df[df["net_outcome"].isin(["TP_HIT","SL_HIT"])].copy()
binary["target"] = (binary["net_outcome"] == "TP_HIT").astype(int)

# A. Win rate by ScanTime hour
if "Hour" in binary.columns:
    hour_stats = binary.groupby("Hour").agg(
        count=("target","count"),
        tp_rate=("target","mean"),
        sl_rate=("target", lambda x: 1-x.mean()),
        avg_drop=("drop_max_pct","mean")
    ).reset_index()
    print("=== Win rate by Hour ===")
    print(hour_stats.to_string(index=False))
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    axes[0].bar(hour_stats["Hour"], hour_stats["tp_rate"], color="green", alpha=0.7, label="TP_HIT rate")
    axes[0].bar(hour_stats["Hour"], -hour_stats["sl_rate"], color="red", alpha=0.7, label="SL_HIT rate")
    axes[0].set_xlabel("Hour (Peru time)")
    axes[0].set_ylabel("Rate")
    axes[0].set_title("TP_HIT vs SL_HIT by Hour")
    axes[0].legend()
    
    axes[1].bar(hour_stats["Hour"], hour_stats["avg_drop"], color="blue", alpha=0.7)
    axes[1].set_xlabel("Hour (Peru time)")
    axes[1].set_ylabel("Avg MaxDrop%")
    axes[1].set_title("Average MaxDrop% by Scan Hour")
    
    plt.tight_layout()
    plt.savefig("/tmp/research/univariate_plots/time_analysis.png", dpi=100)
    plt.close()

# B. First-scan vs Best-scan
if "ScoreAtFirst" in binary.columns and "ScoreMax" in binary.columns:
    print(f"\n=== First-scan vs Best-scan ===")
    binary["first_is_best"] = (binary["ScoreAtFirst"] >= binary["ScoreMax"] * 0.95)
    
    fb_stats = binary.groupby("first_is_best").agg(
        count=("target","count"),
        tp_rate=("target","mean"),
        avg_drop=("drop_max_pct","mean"),
        avg_score_first=("ScoreAtFirst","mean"),
        avg_score_max=("ScoreMax","mean"),
    ).reset_index()
    print(fb_stats.to_string(index=False))

# C. Score evolution — use FirstScanTime vs PeakScoreTime
if "FirstScanTime" in binary.columns and "PeakScoreTime" in binary.columns:
    print(f"\n=== Peak Score Timing ===")
    def time_to_min(t):
        try:
            parts = str(t).split(":")
            return int(parts[0]) * 60 + int(parts[1])
        except:
            return np.nan
    
    binary["first_min"] = binary["FirstScanTime"].apply(time_to_min)
    binary["peak_min"] = binary["PeakScoreTime"].apply(time_to_min)
    binary["peak_delay"] = binary["peak_min"] - binary["first_min"]
    
    for outcome in ["TP_HIT","SL_HIT"]:
        sub = binary[binary["net_outcome"]==outcome]
        mean_delay = sub["peak_delay"].mean()
        mean_first = sub["first_min"].mean()
        print(f"  {outcome}: avg first scan = {mean_first:.0f} min from midnight, avg peak delay = {mean_delay:.0f} min")

# Save time analysis
time_results = []
if "Hour" in binary.columns:
    for _, row in hour_stats.iterrows():
        time_results.append({
            "hour": int(row["Hour"]),
            "count": int(row["count"]),
            "tp_rate": round(row["tp_rate"], 4),
            "sl_rate": round(row["sl_rate"], 4),
            "avg_drop": round(row["avg_drop"], 2),
        })

pd.DataFrame(time_results).to_csv("/tmp/research/time_analysis.csv", index=False)

with open("/tmp/research/checkpoints/phase5.done","w") as f:
    f.write("done\n")
print("\n✓ Phase 5 complete")
