# Data dictionary

## Source tables (`data/raw/`)
| File | Rows | Key columns |
|---|---|---|
| olist_orders_dataset | 99,441 | `order_id`, `customer_id`, `order_status`, purchase / approved / carrier / delivered / estimated timestamps |
| olist_order_items_dataset | 112,650 | `order_id`, `order_item_id`, `product_id`, `seller_id`, `price`, `freight_value` |
| olist_order_payments_dataset | 103,886 | `order_id`, `payment_type`, `payment_installments`, `payment_value` |
| olist_order_reviews_dataset | 99,224 | `order_id`, `review_score` (1–5), comment fields |
| olist_customers_dataset | 99,441 | `customer_id`, `customer_unique_id`, `customer_state`, city, zip prefix |
| olist_sellers_dataset | 3,095 | `seller_id`, `seller_state`, city, zip prefix |
| olist_products_dataset | 32,951 | `product_id`, category (Portuguese), dimensions, weight |
| product_category_name_translation | 71 | Portuguese → English category |
| olist_geolocation_dataset | ~1M | zip prefix → lat/lng (not used in the analysis) |

`customer_id` is unique per order; `customer_unique_id` identifies the real customer (used for repeat-purchase rate).

## Derived order-level table (`data/processed/orders_clean.csv`, not committed)
| Column | Meaning |
|---|---|
| `price`, `freight`, `items` | Summed / counted over the order's items |
| `payment_value` | Total paid for the order |
| `review_score` | Latest review score (1–5), null if none |
| `category`, `seller_id`, `seller_state` | From the order's first item |
| `approval_hrs` | Hours from purchase to payment approval |
| `handling_days` | Approval → carrier pickup |
| `transit_days` | Carrier pickup → delivery |
| `delivery_days` | Purchase → delivery |
| `delay_days` | Delivery − estimated delivery (positive = late) |
| `is_late`, `is_cancelled`, `low_review`, `return_risk` | Boolean flags (see METHODOLOGY) |
| `same_state` | Customer and seller in the same state |
| `month` | Purchase month |

## Dashboard / Power BI datasets
- `dashboard/dashboard_data.csv.gz` – compact subset of the above for the Streamlit app (gzip; do not open in a text editor).
- `powerbi/data/` – `fact_orders` plus `dim_date`, `dim_state` (with region), `dim_category`, `dim_seller`.
