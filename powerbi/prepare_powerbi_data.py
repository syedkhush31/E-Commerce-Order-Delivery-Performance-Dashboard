"""Export a Power BI-ready star schema to powerbi/data/ (run analysis.py first).

fact_orders (1 row per order) -> dim_date, dim_state, dim_category, dim_seller
"""
from pathlib import Path
import pandas as pd

OUT = Path("powerbi/data")
OUT.mkdir(parents=True, exist_ok=True)

STATE_NAMES = {
    "AC": "Acre", "AL": "Alagoas", "AM": "Amazonas", "AP": "Amapá", "BA": "Bahia", "CE": "Ceará",
    "DF": "Distrito Federal", "ES": "Espírito Santo", "GO": "Goiás", "MA": "Maranhão",
    "MG": "Minas Gerais", "MS": "Mato Grosso do Sul", "MT": "Mato Grosso", "PA": "Pará",
    "PB": "Paraíba", "PE": "Pernambuco", "PI": "Piauí", "PR": "Paraná", "RJ": "Rio de Janeiro",
    "RN": "Rio Grande do Norte", "RO": "Rondônia", "RR": "Roraima", "RS": "Rio Grande do Sul",
    "SC": "Santa Catarina", "SE": "Sergipe", "SP": "São Paulo", "TO": "Tocantins",
}
REGION = {
    **dict.fromkeys(["AC", "AM", "AP", "PA", "RO", "RR", "TO"], "North"),
    **dict.fromkeys(["AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"], "Northeast"),
    **dict.fromkeys(["DF", "GO", "MS", "MT"], "Central-West"),
    **dict.fromkeys(["ES", "MG", "RJ", "SP"], "Southeast"),
    **dict.fromkeys(["PR", "RS", "SC"], "South"),
}

d = pd.read_csv("data/processed/orders_clean.csv", parse_dates=["order_purchase_timestamp"])
d["order_date"] = d.order_purchase_timestamp.dt.normalize()
d["delivered"] = d.order_status.eq("delivered")
d["delay_days"] = d.delay_days.where(d.delivered)
d["delivery_days"] = d.delivery_days.where(d.delivered & (d.delivery_days >= 0))
d["is_late"] = (d.is_late & d.delivered).astype(int)
d["is_cancelled"] = d.is_cancelled.astype(int)
d["low_review"] = (d.review_score <= 2).astype(int)
d["return_risk"] = d.return_risk.astype(int)
d["same_state"] = d.same_state.astype(int)
d["has_review"] = d.review_score.notna().astype(int)
d["delivered"] = d.delivered.astype(int)

bucket_order = ["On time/early", "1-3 days late", "4-7 days late", "8-14 days late", "15+ days late"]
d["delay_bucket"] = pd.cut(d.delay_days, [-1e4, 0, 3, 7, 14, 1e4], labels=bucket_order).astype("string")
d["delay_bucket_sort"] = d.delay_bucket.map({b: i + 1 for i, b in enumerate(bucket_order)})

fact_cols = ["order_id", "order_date", "order_status", "customer_state", "seller_id", "category",
             "price", "freight", "payment_value", "payment_type", "review_score", "has_review",
             "approval_hrs", "handling_days", "transit_days", "delivery_days", "delay_days",
             "delay_bucket", "delay_bucket_sort", "delivered", "is_late", "is_cancelled",
             "low_review", "return_risk", "same_state"]
fact = d[fact_cols].copy()
for c in ["price", "freight", "payment_value", "approval_hrs", "handling_days", "transit_days",
          "delivery_days", "delay_days"]:
    fact[c] = fact[c].round(2)
fact.to_csv(OUT / "fact_orders.csv", index=False, date_format="%Y-%m-%d")

dates = pd.DataFrame({"date": pd.date_range(d.order_date.min(), d.order_date.max())})
dates["year"] = dates.date.dt.year
dates["quarter"] = "Q" + dates.date.dt.quarter.astype(str)
dates["month_num"] = dates.date.dt.month
dates["month_name"] = dates.date.dt.strftime("%b")
dates["year_month"] = dates.date.dt.strftime("%Y-%m")
dates["day_of_week"] = dates.date.dt.day_name()
dates["dow_num"] = dates.date.dt.dayofweek + 1
dates.to_csv(OUT / "dim_date.csv", index=False, date_format="%Y-%m-%d")

states = pd.DataFrame({"state_code": list(STATE_NAMES)})
states["state_name"] = states.state_code.map(STATE_NAMES)
states["region"] = states.state_code.map(REGION)
states["state_label"] = states.state_name + ", Brazil"   # helps Power BI map geocoding
states.to_csv(OUT / "dim_state.csv", index=False, encoding="utf-8")

pd.DataFrame({"category": sorted(fact.category.dropna().unique())}).to_csv(OUT / "dim_category.csv", index=False)

sellers = pd.read_csv("data/raw/olist_sellers_dataset.csv")[["seller_id", "seller_city", "seller_state"]]
sellers.to_csv(OUT / "dim_seller.csv", index=False, encoding="utf-8")

# Integrity checks for the relationships Power BI will create
assert fact.order_id.is_unique
assert fact.customer_state.dropna().isin(states.state_code).all()
assert fact.seller_id.dropna().isin(sellers.seller_id).all()
assert fact.order_date.between(dates.date.min(), dates.date.max()).all()
print({p.name: f"{len(pd.read_csv(p)):,} rows" for p in sorted(OUT.glob("*.csv"))})
