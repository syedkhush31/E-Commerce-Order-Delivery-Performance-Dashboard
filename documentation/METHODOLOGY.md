# Methodology

## Data
Olist Brazilian E-Commerce Public Dataset (Kaggle): 9 CSVs, 99,441 orders (Sep 2016 – Oct 2018), 112,650 order items,
3,095 sellers, 32,951 products. Raw files are not committed (see README).

## Grain & joins
Analysis is at **order level** (one row per `order_id`). Child tables are aggregated *before* joining to avoid double counting:
- **Payments:** summed per order (an order can have several payment rows).
- **Reviews:** latest review per order (some orders have more than one).
- **Items:** count, price and freight summed per order; `seller_id` and `category` taken from the first item.
  Multi-seller / multi-category orders (a small minority) are therefore attributed to their first item.
- Category names translated to English; products without a category become `unknown`.

An assertion in the notebook and pipeline checks the joined table still has exactly one row per order.

## Definitions
| Metric | Definition |
|---|---|
| Delivery days | delivered-to-customer date − purchase timestamp (delivered orders only, negatives dropped) |
| Delay days | delivered date − estimated delivery date |
| Late | delay days > 0 (delivered orders) |
| Handling days | carrier pickup − payment approval |
| Transit days | delivered − carrier pickup |
| Cancellation | status `canceled` or `unavailable` |
| Low review | review score ≤ 2 |
| **Return risk (proxy)** | cancellation **or** low review. Olist has no returns table. |
| Revenue | sum of payment value for non-canceled orders |

Trend charts use Jan 2017 – Aug 2018 only; the first and last months of the dataset are sparse.

## Late-delivery model
- **Target:** `is_late` for delivered orders (8.1% positive).
- **Features (known at purchase):** customer state, seller state, same-state flag, category, price, freight, item count,
  promised window (estimated − purchase date), purchase month and weekday.
  Excluded on purpose: approval time, handling time, transit time and anything derived from post-purchase timestamps.
- **Models:** baseline (base rate), logistic regression, histogram gradient boosting (class-weighted).
- **Validation:** stratified random 75/25 split, plus an out-of-time split (train < 2018-05-01, test ≥ 2018-05-01).
  The out-of-time result is the one to trust; random-split scores are optimistic because the model can learn
  month-specific disruption.
- **Operating point:** flag the 20% of orders with the highest predicted risk; report precision/recall there versus the base rate.
- **Interpretation:** permutation importance (drop in ROC-AUC) on the random-split test set.

## Reproducibility
All scripts run from the project root or from any folder (they change to the project root themselves). Random seed 42.
