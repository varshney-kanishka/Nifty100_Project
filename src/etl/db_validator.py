from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine

BASE_DIR = Path(__file__).resolve().parents[2]

DB_PATH = BASE_DIR / "data" / "database" / "nifty100.db"

engine = create_engine(f"sqlite:///{DB_PATH}")

with engine.connect() as conn:

    tables = pd.read_sql(
        "SELECT name FROM sqlite_master WHERE type='table';",
        conn,
    )

print("=" * 70)
print("DATABASE TABLES")
print("=" * 70)

print(tables)

print("\n" + "=" * 70)
print("ROW COUNTS")
print("=" * 70)

with engine.connect() as conn:

    for table in tables["name"]:

        rows = pd.read_sql(
            f"SELECT COUNT(*) AS total FROM {table}",
            conn,
        )

        print(f"{table:<20} {rows.iloc[0,0]}")
        
print("\n" + "=" * 70)
print("TABLE SCHEMAS")
print("=" * 70)

with engine.connect() as conn:

    for table in tables["name"]:

        print(f"\n{table}")

        schema = pd.read_sql(
            f"PRAGMA table_info({table});",
            conn,
        )

        print(schema[["name", "type"]])
query = """
SELECT id, company_name
FROM companies
LIMIT 10;
"""

print(pd.read_sql(query, engine))

query = """
SELECT company_id,
       market_cap_crore
FROM market_cap
ORDER BY market_cap_crore DESC
LIMIT 10;
"""

print(pd.read_sql(query, engine))

query = """
SELECT company_id,
       COUNT(*) AS records
FROM stock_prices
GROUP BY company_id
ORDER BY records DESC
LIMIT 10;
"""

print(pd.read_sql(query, engine))

print("\n" + "=" * 70)
print("PRIMARY KEY CHECK")
print("=" * 70)

with engine.connect() as conn:

    for table in tables["name"]:

        columns = pd.read_sql(
            f"PRAGMA table_info({table});",
            conn,
        )

        if "id" in columns["name"].values:

            duplicate = pd.read_sql(
                f"""
                SELECT COUNT(*)
                FROM (
                    SELECT id
                    FROM {table}
                    GROUP BY id
                    HAVING COUNT(*) > 1
                );
                """,
                conn,
            )

            print(f"{table:<20} {duplicate.iloc[0,0]} duplicate IDs")                