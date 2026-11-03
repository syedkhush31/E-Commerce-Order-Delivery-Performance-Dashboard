# E-Commerce Order Fulfillment & Returns Analytics

Analysis of ~99K orders from the Olist Brazilian e-commerce marketplace (2016–2018) to understand
**delivery performance, fulfillment bottlenecks and return risk**, and how they drive customer satisfaction.

## Business questions
1. How fast and how reliable is delivery? Where are orders late?
2. Which regions, sellers and product categories cause the most problems?
3. How much does late delivery hurt customer reviews?
4. Which categories carry the highest return risk?

> **Note on "returns":** Olist has no returns table. Return risk is proxied as an order that was
> **canceled/unavailable** or received a **review score ≤ 2**.

## Key results
| KPI | Value |
|---|---|
| Total orders | 99,441 |
| Revenue (non-canceled) | R$ 15.87M |
| Avg order value | R$ 160.99 |
| Avg / median delivery time | 12.6 / 10.2 days |
| Late delivery rate | 8.1% |
| Cancellation rate | 1.2% |
| Avg review score | 4.09 |
| Return-risk rate | 14.8% |

## Insights
- **Lateness destroys satisfaction:** average review is 4.29 on time, 3.77 for 1–3 days late, and ~1.7 when 8+ days late.
- **Geography drives delay:** northeast states (AL 23.9%, MA 19.7%, PI 16.0%, CE 15.3%, SE 15.2%) have the highest late rates,
  with ~21–25 day average delivery.
- **Same-state orders arrive ~2x faster** (8.0 vs 15.2 days) – seller distribution/regional fulfillment is a clear lever.
- **Highest return-risk categories:** office_furniture (22.5%), audio (21.4%), home_confort (18.4%), bed_bath_table (16.4%, high volume).

## Recommendations
- Set realistic estimated delivery dates for northeast states, or add regional fulfillment hubs.
- Proactively notify customers of delays before the promised date; the review penalty begins at 1–3 days late.
- Review quality/packaging/description for office furniture and audio categories.
- Put chronically late sellers (see `outputs/seller_scorecard.csv`) on improvement plans.

## Project structure
```
analysis.py            # full pipeline: load -> clean -> KPIs -> tables -> charts
data/raw/              # Olist CSVs (not committed)
outputs/               # KPI summary, tables and figures/
```

## Run it
```bash
pip install pandas matplotlib seaborn
# place the Olist CSVs in data/raw/ (Kaggle: Brazilian E-Commerce Public Dataset by Olist)
python analysis.py
```

## Charts
![Late rate by state](outputs/figures/04_late_by_state.png)
![Review vs delay](outputs/figures/05_review_vs_delay.png)
![Risk by category](outputs/figures/06_risk_by_category.png)

## Tools
Python · pandas · matplotlib · seaborn
