"""Phase 7: Feature Importance via LogisticRegression."""
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score
import warnings
warnings.filterwarnings('ignore')

df = pd.read_csv("/tmp/research/outcomes.csv")
binary = df[df["net_outcome"].isin(["TP_HIT","SL_HIT"])].copy()
binary["target"] = (binary["net_outcome"] == "TP_HIT").astype(int)

# Exclude Hour due to 46% missing
features = ["Score","MxV","RunUp","REL_VOL","RSI","ATRX","Gap","VWAP_dev","Volume","MarketCap","ScanPrice"]
features = [f for f in features if f in binary.columns]

data = binary[features + ["target"]].dropna()
n = len(data)
print(f"Sample size: {n} (TP={data['target'].sum()}, SL={int((1-data['target']).sum())})")

if n < 50:
    print("ABORT: n < 50, insufficient for ML")
    exit(1)

X = data[features].values
y = data["target"].values

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Logistic Regression
lr = LogisticRegression(random_state=42, max_iter=1000, C=1.0)
cv_scores = cross_val_score(lr, X_scaled, y, cv=5, scoring='roc_auc')
print(f"\nLogistic Regression 5-fold CV AUC: {cv_scores.mean():.4f} +/- {cv_scores.std():.4f}")
print(f"  Per fold: {[f'{s:.4f}' for s in cv_scores]}")

lr.fit(X_scaled, y)
coefs = pd.DataFrame({
    "feature": features,
    "lr_coef": lr.coef_[0],
    "lr_abs_coef": np.abs(lr.coef_[0]),
})
coefs = coefs.sort_values("lr_abs_coef", ascending=False)
coefs["lr_rank"] = range(1, len(coefs)+1)

print(f"\nLR Coefficients (standardized):")
for _, row in coefs.iterrows():
    direction = "higher=more TP" if row["lr_coef"] > 0 else "higher=more SL"
    print(f"  {row['feature']:>15}: coef={row['lr_coef']:+.4f} ({direction})")

coefs.to_csv("/tmp/research/lr_coefs.csv", index=False)

# Combined
uni = pd.read_csv("/tmp/research/univariate_analysis.csv")
uni_auc = dict(zip(uni["metric"], uni["auc"]))
combined = coefs.copy()
combined["univariate_auc"] = combined["feature"].map(uni_auc)
combined["rf_imp"] = None
combined["rf_rank"] = None

if n >= 150:
    from sklearn.ensemble import RandomForestClassifier
    rf = RandomForestClassifier(n_estimators=200, max_depth=5, random_state=42)
    rf_cv = cross_val_score(rf, X_scaled, y, cv=5, scoring='roc_auc')
    print(f"\nRandom Forest CV AUC: {rf_cv.mean():.4f} +/- {rf_cv.std():.4f}")
    rf.fit(X_scaled, y)
    combined["rf_imp"] = rf.feature_importances_
    combined = combined.sort_values("rf_imp", ascending=False)
    combined["rf_rank"] = range(1, len(combined)+1)
    combined.to_csv("/tmp/research/rf_importance.csv", index=False)
else:
    print(f"\nSkipping RF: n={n} < 150")

combined.to_csv("/tmp/research/feature_importance.csv", index=False)

print(f"\n{'='*60}")
print("COMBINED FEATURE IMPORTANCE")
print(f"{'='*60}")
print(combined[["feature","lr_coef","lr_rank","univariate_auc"]].to_string(index=False))

with open("/tmp/research/checkpoints/phase7.done","w") as f:
    f.write("done\n")
print("\n✓ Phase 7 complete")
