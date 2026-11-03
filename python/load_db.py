"""Load the raw Olist CSVs into a local SQLite database (data/olist.db)."""
import sqlite3
import os
from pathlib import Path
import pandas as pd

os.chdir(Path(__file__).resolve().parents[1])  # run from project root, wherever launched

RAW = Path("data/raw")
db = Path("data/olist.db")
db.unlink(missing_ok=True)
con = sqlite3.connect(db)
names = {
    "olist_customers_dataset": "customers", "olist_orders_dataset": "orders",
    "olist_order_items_dataset": "order_items", "olist_order_payments_dataset": "payments",
    "olist_order_reviews_dataset": "reviews", "olist_products_dataset": "products",
    "olist_sellers_dataset": "sellers", "product_category_name_translation": "category_translation",
}
for f, t in names.items():
    df = pd.read_csv(RAW / f"{f}.csv")
    df.to_sql(t, con, index=False)
    print(f"{t}: {len(df):,} rows")
con.executescript(Path("sql/00_views.sql").read_text())
con.commit()
con.close()
print("Built", db)
