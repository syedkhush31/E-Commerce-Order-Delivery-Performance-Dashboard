"""E-Commerce Order Fulfillment & Returns Analytics (Olist).

Builds a clean order-level table, computes delivery/fulfillment KPIs,
return-risk proxies (cancellations + low reviews), saves charts and summary tables.
Run:  python analysis.py
"""
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

RAW = Path("data/raw")
OUT = Path("outputs")
FIG = OUT / "figures"
PROC = Path("data/processed")
for p in (FIG, PROC):
    p.mkdir(parents=True, exist_ok=True)
sns.set_theme(style="whitegrid")

# ---------- Load ----------
dates = ["order_purchase_timestamp", "order_approved_at", "order_delivered_carrier_date",
         "order_delivered_customer_date", "order_estimated_delivery_date"]
orders = pd.read_csv(RAW / "olist_orders_dataset.csv", parse_dates=dates)
items = pd.read_csv(RAW / "olist_order_items_dataset.csv")
pay = pd.read_csv(RAW / "olist_order_payments_dataset.csv")
rev = pd.read_csv(RAW / "olist_order_reviews_dataset.csv")
cust = pd.read_csv(RAW / "olist_customers_dataset.csv")
sell = pd.read_csv(RAW / "olist_sellers_dataset.csv")
prod = pd.read_csv(RAW / "olist_products_dataset.csv")
trans = pd.read_csv(RAW / "product_category_name_translation.csv")

# ---------- Clean / aggregate to order grain ----------
rev = rev.sort_values("review_answer_timestamp").drop_duplicates("order_id", keep="last")
pay_o = pay.groupby("order_id").agg(payment_value=("payment_value", "sum"),
                                    payment_type=("payment_type", "first")).reset_index()
prod = prod.merge(trans, on="product_category_name", how="left")
prod["category"] = prod["product_category_name_english"].fillna(prod["product_category_name"]).fillna("unknown")
items = items.merge(prod[["product_id", "category"]], on="product_id", how="left")
item_o = items.groupby("order_id").agg(items=("order_item_id", "count"), price=("price", "sum"),
                                       freight=("freight_value", "sum"),
                                       seller_id=("seller_id", "first"),
                                       category=("category", "first")).reset_index()

df = (orders.merge(cust[["customer_id", "customer_unique_id", "customer_state"]], on="customer_id", how="left")
      .merge(item_o, on="order_id", how="left")
      .merge(pay_o, on="order_id", how="left")
      .merge(rev[["order_id", "review_score"]], on="order_id", how="left")
      .merge(sell[["seller_id", "seller_state"]], on="seller_id", how="left"))

# ---------- Features ----------
d = df
d["approval_hrs"] = (d.order_approved_at - d.order_purchase_timestamp).dt.total_seconds() / 3600
d["handling_days"] = (d.order_delivered_carrier_date - d.order_approved_at).dt.total_seconds() / 86400
d["transit_days"] = (d.order_delivered_customer_date - d.order_delivered_carrier_date).dt.total_seconds() / 86400
d["delivery_days"] = (d.order_delivered_customer_date - d.order_purchase_timestamp).dt.total_seconds() / 86400
d["delay_days"] = (d.order_delivered_customer_date - d.order_estimated_delivery_date).dt.total_seconds() / 86400
d["is_late"] = d.delay_days > 0
d["is_cancelled"] = d.order_status.isin(["canceled", "unavailable"])
d["low_review"] = d.review_score <= 2
d["return_risk"] = d.is_cancelled | d.low_review.fillna(False)
d["month"] = d.order_purchase_timestamp.dt.to_period("M").dt.to_timestamp()
d["same_state"] = d.customer_state == d.seller_state
d.to_csv(PROC / "orders_clean.csv", index=False)

deliv = d[(d.order_status == "delivered") & d.delivery_days.notna()].copy()
deliv = deliv[deliv.delivery_days >= 0]
# Drop incomplete first/last months for trends
trend = d[(d.month >= "2017-01-01") & (d.month <= "2018-08-01")]

# ---------- KPIs ----------
kpi = {
    "total_orders": len(d),
    "delivered_orders": int((d.order_status == "delivered").sum()),
    "total_revenue_BRL": round(d.loc[d.order_status != "canceled", "payment_value"].sum(), 2),
    "avg_order_value_BRL": round(d.payment_value.mean(), 2),
    "avg_delivery_days": round(deliv.delivery_days.mean(), 2),
    "median_delivery_days": round(deliv.delivery_days.median(), 2),
    "late_delivery_rate_pct": round(deliv.is_late.mean() * 100, 2),
    "cancellation_rate_pct": round(d.is_cancelled.mean() * 100, 2),
    "low_review_rate_pct": round(d.low_review[d.review_score.notna()].mean() * 100, 2),
    "avg_review_score": round(d.review_score.mean(), 2),
    "return_risk_rate_pct": round(d.return_risk.mean() * 100, 2),
}
pd.Series(kpi).to_csv(OUT / "kpi_summary.csv", header=["value"])

# ---------- Tables ----------
state = deliv.groupby("customer_state").agg(orders=("order_id", "count"),
        avg_days=("delivery_days", "mean"), late_pct=("is_late", lambda s: s.mean() * 100),
        avg_review=("review_score", "mean")).round(2).sort_values("late_pct", ascending=False)
state.to_csv(OUT / "delivery_by_state.csv")

cat = d.groupby("category").agg(orders=("order_id", "count"), revenue=("price", "sum"),
        risk_pct=("return_risk", lambda s: s.mean() * 100),
        avg_review=("review_score", "mean")).round(2)
cat_top = cat[cat.orders >= 300].sort_values("risk_pct", ascending=False)
cat_top.to_csv(OUT / "return_risk_by_category.csv")

sel = deliv.groupby("seller_id").agg(orders=("order_id", "count"),
        late_pct=("is_late", lambda s: s.mean() * 100),
        avg_review=("review_score", "mean")).round(2)
sel = sel[sel.orders >= 30].sort_values("late_pct", ascending=False)
sel.to_csv(OUT / "seller_scorecard.csv")

rev_by_late = deliv.groupby(pd.cut(deliv.delay_days, [-100, 0, 3, 7, 14, 500],
        labels=["On time/early", "1-3 days late", "4-7 late", "8-14 late", "15+ late"]),
        observed=True).review_score.mean().round(2)
rev_by_late.to_csv(OUT / "review_by_delay.csv")

# ---------- Charts ----------
def save(name):
    plt.tight_layout(); plt.savefig(FIG / name, dpi=130); plt.close()

m = trend.groupby("month").agg(orders=("order_id", "count"), revenue=("payment_value", "sum"))
fig, ax = plt.subplots(figsize=(10, 4.5))
ax.plot(m.index, m.orders, marker="o", color="#2a6fdb"); ax.set_title("Monthly Orders"); ax.set_ylabel("Orders")
save("01_monthly_orders.png")

fig, ax = plt.subplots(figsize=(8, 4.5))
sns.histplot(deliv.delivery_days.clip(upper=60), bins=60, ax=ax, color="#2a6fdb")
ax.axvline(deliv.delivery_days.median(), color="red", ls="--", label=f"median {deliv.delivery_days.median():.1f}d")
ax.set_title("Delivery Time Distribution (days, capped 60)"); ax.legend()
save("02_delivery_distribution.png")

lm = deliv[(deliv.month >= "2017-01-01") & (deliv.month <= "2018-08-01")].groupby("month").is_late.mean() * 100
fig, ax = plt.subplots(figsize=(10, 4.5))
ax.plot(lm.index, lm.values, marker="o", color="#d9534f"); ax.set_title("Late Delivery Rate by Month (%)")
save("03_late_rate_trend.png")

fig, ax = plt.subplots(figsize=(8, 7))
state.sort_values("late_pct").plot.barh(y="late_pct", ax=ax, legend=False, color="#d9534f")
ax.set_title("Late Delivery % by Customer State"); ax.set_xlabel("%")
save("04_late_by_state.png")

fig, ax = plt.subplots(figsize=(7, 4.5))
rev_by_late.plot.bar(ax=ax, color="#5cb85c", rot=20)
ax.set_title("Avg Review Score vs Delivery Delay"); ax.set_ylabel("Avg score")
save("05_review_vs_delay.png")

fig, ax = plt.subplots(figsize=(9, 6))
cat_top.head(15).sort_values("risk_pct").plot.barh(y="risk_pct", ax=ax, legend=False, color="#f0ad4e")
ax.set_title("Top 15 Categories by Return-Risk % (cancel or review ≤2)"); ax.set_xlabel("%")
save("06_risk_by_category.png")

fig, ax = plt.subplots(figsize=(7, 4.5))
sns.barplot(data=deliv, x="same_state", y="delivery_days", ax=ax, errorbar=None)
ax.set_title("Avg Delivery Days: Seller & Customer in Same State?")
save("07_same_state.png")

fig, ax = plt.subplots(figsize=(7, 4.5))
d.review_score.value_counts().sort_index().plot.bar(ax=ax, color="#2a6fdb", rot=0)
ax.set_title("Review Score Distribution")
save("08_review_distribution.png")

# ---------- Compact dataset for the Streamlit dashboard (committed to the repo) ----------
dash_cols = ["order_id", "order_status", "customer_state", "seller_id", "category", "month",
             "price", "freight", "payment_value", "review_score", "approval_hrs", "handling_days",
             "transit_days", "delivery_days", "delay_days", "is_late", "is_cancelled", "same_state"]
dash = d[dash_cols].copy()
dash["month"] = dash["month"].dt.strftime("%Y-%m")
for c in ["price", "freight", "payment_value", "approval_hrs", "handling_days", "transit_days",
          "delivery_days", "delay_days"]:
    dash[c] = dash[c].round(2)
Path("dashboard").mkdir(exist_ok=True)
dash.to_csv("dashboard/dashboard_data.csv.gz", index=False, compression="gzip")

print(pd.Series(kpi).to_string())
print("\nReview by delay:\n", rev_by_late.to_string())
print("\nWorst states:\n", state.head(5).to_string())
print("\nRiskiest categories:\n", cat_top.head(5).to_string())
print("\nSame-state delivery days:\n", deliv.groupby("same_state").delivery_days.mean().round(2).to_string())
