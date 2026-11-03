"""Run every sql/NN_*.sql query against data/olist.db and save results to outputs/sql/."""
import sqlite3
from pathlib import Path
import pandas as pd

out = Path("outputs/sql")
out.mkdir(parents=True, exist_ok=True)
con = sqlite3.connect("data/olist.db")
for f in sorted(Path("sql").glob("0[1-9]_*.sql")):
    df = pd.read_sql_query(f.read_text(), con)
    df.to_csv(out / f"{f.stem}.csv", index=False)
    print(f"\n=== {f.stem} ===\n{df.head(8).to_string(index=False)}")
