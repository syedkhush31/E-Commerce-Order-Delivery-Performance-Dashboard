"""Streamlit dashboard: E-Commerce Order Fulfillment & Returns Analytics (Olist).
Run:  streamlit run dashboard/app.py
"""
from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Order Delivery Performance", page_icon="📦", layout="wide")
DATA = Path(__file__).parent / "dashboard_data.csv.gz"


@st.cache_data
def load():
    d = pd.read_csv(DATA)
    d["is_late"] = d.is_late.astype(bool)
    d["is_cancelled"] = d.is_cancelled.astype(bool)
    d["low_review"] = d.review_score <= 2
    d["return_risk"] = d.is_cancelled | d.low_review
    return d


df = load()

# ---------------- Sidebar filters ----------------
st.sidebar.header("Filters")
months = sorted(df.month.unique())
m_from, m_to = st.sidebar.select_slider("Order month range", options=months, value=("2017-01", "2018-08"))
states = sorted(df.customer_state.dropna().unique())
sel_states = st.sidebar.multiselect("Customer state", states, default=[])
cats = sorted(df.category.dropna().unique())
sel_cats = st.sidebar.multiselect("Product category", cats, default=[])

f = df[(df.month >= m_from) & (df.month <= m_to)]
if sel_states:
    f = f[f.customer_state.isin(sel_states)]
if sel_cats:
    f = f[f.category.isin(sel_cats)]
deliv = f[(f.order_status == "delivered") & (f.delivery_days >= 0)]

st.title("📦 E-Commerce Order Delivery Performance")
st.caption("Olist Brazilian marketplace · return risk = canceled/unavailable order or review score ≤ 2 "
           "(the dataset has no returns table)")
if f.empty:
    st.warning("No orders match the current filters.")
    st.stop()

# ---------------- KPI row ----------------
c = st.columns(6)
c[0].metric("Orders", f"{len(f):,}")
c[1].metric("Revenue (R$)", f"{f.loc[f.order_status != 'canceled', 'payment_value'].sum() / 1e6:.2f}M")
c[2].metric("Avg delivery (days)", f"{deliv.delivery_days.mean():.1f}")
c[3].metric("Late delivery", f"{deliv.is_late.mean() * 100:.1f}%")
c[4].metric("Avg review", f"{f.review_score.mean():.2f}")
c[5].metric("Return risk", f"{f.return_risk.mean() * 100:.1f}%")

tab1, tab2, tab3, tab4 = st.tabs(["Delivery performance", "Geography", "Returns & categories", "Sellers"])

# ---------------- Tab 1 ----------------
with tab1:
    l, r = st.columns(2)
    monthly = f.groupby("month").agg(orders=("order_id", "count")).reset_index()
    l.plotly_chart(px.line(monthly, x="month", y="orders", markers=True, title="Monthly orders"),
                   width='stretch')
    late = deliv.groupby("month").is_late.mean().mul(100).reset_index()
    r.plotly_chart(px.line(late, x="month", y="is_late", markers=True, title="Late delivery rate (%)",
                           labels={"is_late": "% late"}, color_discrete_sequence=["#d9534f"]),
                   width='stretch')
    l, r = st.columns(2)
    l.plotly_chart(px.histogram(deliv[deliv.delivery_days <= 60], x="delivery_days", nbins=60,
                                title="Delivery time distribution (days)"), width='stretch')
    stages = pd.DataFrame({"stage": ["Payment approval", "Seller handling", "Carrier transit"],
                           "days": [deliv.approval_hrs.mean() / 24, deliv.handling_days.mean(),
                                    deliv.transit_days.mean()]})
    r.plotly_chart(px.bar(stages, x="stage", y="days", title="Where delivery time goes (avg days)",
                          text=stages.days.round(1)), width='stretch')
    buckets = pd.cut(deliv.delay_days, [-1000, 0, 3, 7, 14, 1000],
                     labels=["On time/early", "1-3d late", "4-7d late", "8-14d late", "15d+ late"])
    rv = deliv.groupby(buckets, observed=True).review_score.mean().reset_index()
    st.plotly_chart(px.bar(rv, x="delay_days", y="review_score", text=rv.review_score.round(2),
                           title="Late deliveries destroy review scores",
                           labels={"delay_days": "", "review_score": "Avg review"},
                           color_discrete_sequence=["#5cb85c"]), width='stretch')

# ---------------- Tab 2 ----------------
with tab2:
    st_ = deliv.groupby("customer_state").agg(orders=("order_id", "count"), avg_days=("delivery_days", "mean"),
                                              late_pct=("is_late", lambda s: s.mean() * 100),
                                              avg_review=("review_score", "mean")).reset_index()
    l, r = st.columns(2)
    l.plotly_chart(px.bar(st_.sort_values("late_pct"), x="late_pct", y="customer_state", orientation="h",
                          title="Late delivery % by state", height=650,
                          color_discrete_sequence=["#d9534f"]), width='stretch')
    r.plotly_chart(px.scatter(st_, x="avg_days", y="late_pct", size="orders", text="customer_state",
                              title="Delivery time vs lateness (bubble = orders)", height=650),
                   width='stretch')
    same = deliv.groupby("same_state").delivery_days.mean().rename({True: "Same state", False: "Different state"})
    st.plotly_chart(px.bar(same.reset_index(), x="same_state", y="delivery_days",
                           text=same.round(1).values, title="Avg delivery days: seller & customer in same state?"),
                    width='stretch')
    st.dataframe(st_.sort_values("late_pct", ascending=False).round(2), width='stretch', hide_index=True)

# ---------------- Tab 3 ----------------
with tab3:
    cat = f.groupby("category").agg(orders=("order_id", "count"), revenue=("price", "sum"),
                                    risk_pct=("return_risk", lambda s: s.mean() * 100),
                                    avg_review=("review_score", "mean")).reset_index()
    min_orders = st.slider("Minimum orders per category", 50, 1000, 300, 50)
    cat = cat[cat.orders >= min_orders].sort_values("risk_pct", ascending=False)
    l, r = st.columns(2)
    l.plotly_chart(px.bar(cat.head(15).sort_values("risk_pct"), x="risk_pct", y="category", orientation="h",
                          title="Top 15 categories by return risk (%)", height=520,
                          color_discrete_sequence=["#f0ad4e"]), width='stretch')
    r.plotly_chart(px.scatter(cat, x="orders", y="risk_pct", size="revenue", hover_name="category",
                              title="Volume vs return risk (bubble = revenue)", height=520),
                   width='stretch')
    st.dataframe(cat.round(2), width='stretch', hide_index=True)

# ---------------- Tab 4 ----------------
with tab4:
    min_s = st.slider("Minimum delivered orders per seller", 10, 200, 30, 10)
    sel = deliv.groupby("seller_id").agg(orders=("order_id", "count"),
                                         late_pct=("is_late", lambda s: s.mean() * 100),
                                         avg_review=("review_score", "mean")).reset_index()
    sel = sel[sel.orders >= min_s].sort_values("late_pct", ascending=False)
    st.plotly_chart(px.scatter(sel, x="late_pct", y="avg_review", size="orders", hover_name="seller_id",
                               title=f"Seller late rate vs review score ({len(sel)} sellers)"),
                    width='stretch')
    st.subheader("Worst sellers by late-delivery rate")
    st.dataframe(sel.head(25).round(2), width='stretch', hide_index=True)
