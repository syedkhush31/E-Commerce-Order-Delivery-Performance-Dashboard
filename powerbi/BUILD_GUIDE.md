# Power BI build guide (~30–45 min)

Everything is prepared: a star schema in `powerbi/data/`, 30+ DAX measures in `measures.dax`, and `theme.json`.
Save the finished report as `powerbi/Order_Delivery_Performance.pbix` and add screenshots to `powerbi/screenshots/`.

## 1. Load the data
1. Power BI Desktop → **Home → Get data → Text/CSV**, load all 5 files from `powerbi/data/`
   (`fact_orders`, `dim_date`, `dim_state`, `dim_category`, `dim_seller`). Click **Load** (no transform needed).
2. **View → Themes → Browse for themes** → select `powerbi/theme.json`.

## 2. Model (Model view)
Create these relationships (all many-to-one, single direction, dimension → fact):

| From (dimension, "one") | To (fact_orders, "many") |
|---|---|
| dim_date[date] | fact_orders[order_date] |
| dim_state[state_code] | fact_orders[customer_state] |
| dim_category[category] | fact_orders[category] |
| dim_seller[seller_id] | fact_orders[seller_id] |

Then:
- Select `dim_date` → **Table tools → Mark as date table** → choose `date`.
- Sort `dim_date[month_name]` by `month_num`, `dim_date[day_of_week]` by `dow_num`.
- Sort `fact_orders[delay_bucket]` by `delay_bucket_sort`.
- `dim_state[state_label]` → Data category **Place/State or Province**; `state_name` → same (for the map).
- Hide the raw numeric columns you don't want in the field list (`is_late`, `delivered`, etc.).

## 3. Measures
Open `measures.dax` and create each measure (**Modeling → New measure**) in `fact_orders`.
Format: `%` measures → percentage (1 decimal), `Revenue`/`Avg Order Value` → currency (R$), days → 1 decimal.

**Validate before building visuals** – with no filters, a card for each must show:

| Measure | Expected |
|---|---|
| Total Orders | 99,441 |
| Revenue | 15,865,616.52 |
| Avg Order Value | 160.99 |
| Avg Delivery Days | 12.56 |
| Late Delivery % | 8.11% |
| Avg Review Score | 4.09 |
| Cancellation % | 1.24% |
| Return Risk % | 14.84% |

## 4. Report pages
Use slicers synced across pages: **dim_date[year_month] (or date range)**, **dim_state[region]**, **dim_category[category]**.

### Page 1 – Executive Overview
- 6 KPI cards: Total Orders, Revenue, Avg Delivery Days, Late Delivery %, Avg Review Score, Return Risk %.
  Add `Late % Color` as conditional formatting (Field value) on the Late % card font.
- Line chart: `dim_date[year_month]` × `Total Orders` (+ `Revenue` secondary axis).
- Line chart: `year_month` × `Late Delivery %`. (Filter visual to 2017-01 … 2018-08; edge months are sparse.)
- Title text box bound to `Dynamic Title`.

### Page 2 – Delivery Performance
- Clustered bar: stages – use a small calculated table or 3 cards: `Avg Approval Days`, `Avg Handling Days`, `Avg Transit Days`
  (shows carrier transit ≈ 9.3 of 12.6 days).
- Column chart: `fact_orders[delay_bucket]` × `Avg Review Score` (the "lateness kills reviews" chart; 4.29 → 1.7).
- Histogram-style: column chart of `delivery_days` binned (right-click field → **New group → Bins**, size 2).
- Card pair: `Same-State Avg Days` vs `Cross-State Avg Days` (≈ 8 vs 15).

### Page 3 – Geography
- Filled map or shape map: location `dim_state[state_label]`, color saturation `Late Delivery %`
  (diverging green→red, midpoint = overall 8.1%).
- Bar chart: `dim_state[state_name]` × `Late Delivery %` sorted descending (AL, MA, PI, CE, SE on top).
- Matrix: `region` → `state_name` with `Delivered Orders`, `Avg Delivery Days`, `Late Delivery %`, `Avg Review Score`
  (data bars on Late %).

### Page 4 – Returns & Categories
- Bar chart: `category` × `Return Risk %`, Top N = 15 by `Return Risk %`
  with a visual-level filter `Total Orders ≥ 300`.
- Scatter: X `Total Orders`, Y `Return Risk %`, size `Revenue`, details `category`.
- Cards: `Cancellation %`, `Low Review %`, `Revenue at Risk`.

### Page 5 – Seller Scorecard
- Table: `dim_seller[seller_id]`, `seller_state`, `Delivered Orders`, `Late Delivery %`, `Avg Review Score`, `Seller Late Rank`;
  filter `Delivered Orders ≥ 30`, sort by `Late Delivery %` desc, color scale on Late %.
- Scatter: X `Late Delivery %`, Y `Avg Review Score`, size `Delivered Orders`, details `seller_id`.
- **Drill-through** page from Seller → orders list.

### Finishing touches
- Add **bookmarks/page navigator** (Insert → Buttons → Navigator → Page navigator).
- Tooltips: add `Avg Delivery Days` and `Avg Review Score` to chart tooltips.
- Turn off "Show items with no data" in visuals where Dec-2016 / Sep-2018 sparse months distort trends.
- Insights text box on each page (2 bullets – copy from the README insights).

## 5. Publish / share
- Save `.pbix` into `powerbi/` and commit it (typically ~10–15 MB).
- **Home → Publish** to Power BI Service (free account needs a work/school email); or export PDF and add screenshots to the README.
