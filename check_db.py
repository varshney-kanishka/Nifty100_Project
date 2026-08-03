import sqlite3
import pandas as pd

conn = sqlite3.connect("data/database/nifty100.db")

tables = pd.read_sql(
    "SELECT name FROM sqlite_master WHERE type='table';",
    conn
)

print("TABLES")
print(tables)

for table in tables["name"]:
    print("\n" + "=" * 60)
    print(table)
    print(pd.read_sql(f"PRAGMA table_info({table})", conn)[["name"]])

conn.close()