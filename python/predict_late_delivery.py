"""Predict which delivered orders will arrive late, using ONLY information known at purchase time
(no leakage from shipping/handling/transit timestamps).

Features: customer/seller state, same-state flag, product category, price, freight, #items,
promised delivery window (estimated - purchase, in days), purchase month / weekday.
Validation: (a) stratified random split, (b) out-of-time split (train before 2018-05, test 2018-05+).

Run:  python python/predict_late_delivery.py     (needs data/processed/orders_clean.csv from analysis.py)
"""
import os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (average_precision_score, precision_recall_curve, precision_score,
                             recall_score, roc_auc_score, roc_curve)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

os.chdir(Path(__file__).resolve().parents[1])
FIG, TAB = Path("outputs/figures"), Path("outputs/tables")
SEED = 42

d = pd.read_csv("data/processed/orders_clean.csv",
                parse_dates=["order_purchase_timestamp", "order_estimated_delivery_date"])
d = d[(d.order_status == "delivered") & d.delay_days.notna() & d.customer_state.notna()].copy()
d["promised_days"] = (d.order_estimated_delivery_date - d.order_purchase_timestamp).dt.total_seconds() / 86400
d["purchase_month"] = d.order_purchase_timestamp.dt.month
d["purchase_dow"] = d.order_purchase_timestamp.dt.dayofweek
d["same_state"] = d.same_state.astype(int)
d["category"] = d.category.fillna("unknown")
d["seller_state"] = d.seller_state.fillna("unknown")
d = d.dropna(subset=["price", "freight", "items", "promised_days"])
y = d.is_late.astype(int)

CAT = ["customer_state", "seller_state", "category"]
NUM = ["same_state", "price", "freight", "items", "promised_days", "purchase_month", "purchase_dow"]
X = d[CAT + NUM]
print(f"{len(d):,} delivered orders, late rate {y.mean():.1%}")


def make(model, scale=False):
    num = StandardScaler() if scale else "passthrough"
    pre = ColumnTransformer([("cat", OneHotEncoder(handle_unknown="ignore", min_frequency=30, sparse_output=False), CAT),
                             ("num", num, NUM)])
    return Pipeline([("pre", pre), ("model", model)])


models = {
    "Baseline (predict base rate)": make(DummyClassifier(strategy="prior")),
    "Logistic regression": make(LogisticRegression(max_iter=1000, class_weight="balanced"), scale=True),
    "Gradient boosting": make(HistGradientBoostingClassifier(max_depth=6, learning_rate=0.08, max_iter=300,
                                                             class_weight="balanced", random_state=SEED)),
}


def evaluate(split_name, Xtr, Xte, ytr, yte):
    rows, fitted = [], {}
    for name, m in models.items():
        m.fit(Xtr, ytr)
        p = m.predict_proba(Xte)[:, 1]
        # operating point: flag the 20% of orders with the highest predicted risk
        thr = np.quantile(p, 0.80)
        flag = p >= thr
        rows.append({"split": split_name, "model": name, "roc_auc": roc_auc_score(yte, p),
                     "pr_auc": average_precision_score(yte, p), "base_late_rate": yte.mean(),
                     "precision_top20pct": precision_score(yte, flag, zero_division=0),
                     "recall_top20pct": recall_score(yte, flag)})
        fitted[name] = (m, p)
    return rows, fitted


# (a) random split
Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.25, stratify=y, random_state=SEED)
rows_a, fit_a = evaluate("random 75/25", Xtr, Xte, ytr, yte)
# (b) out-of-time split
cut = pd.Timestamp("2018-05-01")
tr, te = d.order_purchase_timestamp < cut, d.order_purchase_timestamp >= cut
rows_b, fit_b = evaluate("out-of-time (test: May-Aug 2018)", X[tr], X[te], y[tr], y[te])

res = pd.DataFrame(rows_a + rows_b).round(3)
res.to_csv(TAB / "model_metrics.csv", index=False)
print(res.to_string(index=False))

# ---- Charts (random split, best model) ----
best = "Gradient boosting"
m, p = fit_a[best]
fpr, tpr, _ = roc_curve(yte, p)
prec, rec, _ = precision_recall_curve(yte, p)
fig, ax = plt.subplots(1, 2, figsize=(12, 4.5))
ax[0].plot(fpr, tpr, label=f"{best} (AUC {roc_auc_score(yte, p):.2f})")
lr_p = fit_a["Logistic regression"][1]
ax[0].plot(*roc_curve(yte, lr_p)[:2], label=f"Logistic (AUC {roc_auc_score(yte, lr_p):.2f})")
ax[0].plot([0, 1], [0, 1], "k--", label="Random")
ax[0].set(xlabel="False positive rate", ylabel="True positive rate", title="ROC curve"); ax[0].legend()
ax[1].plot(rec, prec, label=f"{best} (AP {average_precision_score(yte, p):.2f})")
ax[1].axhline(yte.mean(), color="k", ls="--", label=f"Base rate {yte.mean():.1%}")
ax[1].set(xlabel="Recall", ylabel="Precision", title="Precision-recall curve"); ax[1].legend()
plt.tight_layout(); plt.savefig(FIG / "09_model_roc_pr.png", dpi=130); plt.close()

imp = permutation_importance(m, Xte, yte, scoring="roc_auc", n_repeats=5, random_state=SEED, n_jobs=1)
imp = pd.Series(imp.importances_mean, index=X.columns).sort_values()
fig, ax = plt.subplots(figsize=(8, 4.5))
imp.plot.barh(ax=ax, color="#2a6fdb")
ax.set_title("Permutation importance (drop in ROC-AUC when shuffled)")
plt.tight_layout(); plt.savefig(FIG / "10_feature_importance.png", dpi=130); plt.close()
imp.sort_values(ascending=False).round(4).to_csv(TAB / "model_feature_importance.csv", header=["auc_drop"])
print("\nFeature importance:\n", imp.sort_values(ascending=False).round(4).to_string())
