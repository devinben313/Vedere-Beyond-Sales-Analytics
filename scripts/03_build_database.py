"""
03_build_database.py
--------------------
Creates the SQLite database data/vedere_beyond.db from the processed CSVs:
applies sql/schema.sql, bulk-loads every table, creates the analytical views
in sql/views.sql and runs integrity checks.

Usage:  python scripts/03_build_database.py
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
DB_PATH = ROOT / "data" / "vedere_beyond.db"

# load order respects foreign keys
TABLES = ["products", "ad_campaigns", "customers", "orders", "order_items", "ad_performance_daily"]
DATE_COLS = {"products": ["launch_date"], "ad_campaigns": ["start_date", "end_date"],
             "customers": ["first_order_date"], "orders": ["order_date"],
             "ad_performance_daily": ["date"]}


def main() -> None:
    if DB_PATH.exists():
        DB_PATH.unlink()
    con = sqlite3.connect(DB_PATH)
    con.executescript((ROOT / "sql" / "schema.sql").read_text())

    for t in TABLES:
        df = pd.read_csv(PROCESSED / f"{t}.csv")
        for c in DATE_COLS.get(t, []):  # store dates as ISO 'YYYY-MM-DD' text
            df[c] = pd.to_datetime(df[c]).dt.strftime("%Y-%m-%d")
        for c in df.columns[df.dtypes == bool]:
            df[c] = df[c].astype(int)
        cols = [r[1] for r in con.execute(f"PRAGMA table_info({t})")]
        df[cols].to_sql(t, con, if_exists="append", index=False)
        print(f"  loaded {t:<22} {len(df):>6,} rows")

    con.executescript((ROOT / "sql" / "views.sql").read_text())

    # integrity checks
    fk = con.execute("PRAGMA foreign_key_check").fetchall()
    assert not fk, f"foreign key violations: {fk[:5]}"
    rev_lines = con.execute("SELECT SUM(net_line_revenue) FROM v_order_lines").fetchone()[0]
    rev_orders = con.execute("SELECT SUM(net_sales) FROM orders WHERE is_refunded = 0").fetchone()[0]
    assert abs(rev_lines - rev_orders) < 0.05, "line-level revenue does not reconcile to orders"
    con.commit()
    con.close()
    print(f"\nSQLite database ready -> {DB_PATH.relative_to(ROOT)} (FK + revenue reconciliation checks passed)")


if __name__ == "__main__":
    main()
