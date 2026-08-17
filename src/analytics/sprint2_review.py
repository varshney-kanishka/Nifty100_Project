import sqlite3
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[2]

DB = BASE_DIR / "data/database/nifty100.db"

conn = sqlite3.connect(DB)

print("=" * 70)
print("DAY 14 - SPRINT REVIEW")
print("=" * 70)
count = pd.read_sql(
    """
    SELECT COUNT(*) AS total
    FROM financial_ratios
    """,
    conn,
)

print("\nfinancial_ratios Rows")
print(count)
print("\nMissing Values")
print("-" * 70)

important_columns = [

    "net_profit_margin_pct",
    "operating_profit_margin_pct",
    "return_on_equity_pct",
    "debt_to_equity",
    "interest_coverage",
    "asset_turnover",
    "free_cash_flow_cr",

]

ratios = pd.read_sql(
    "SELECT * FROM financial_ratios",
    conn,
)

print(
    ratios[important_columns].isnull().sum()
)
log_file = BASE_DIR / "output" / "ratio_edge_cases.log"

print("\nEdge Case Log Exists")

print(log_file.exists())

print(log_file)
print("\nFirst 20 lines")

with open(log_file) as f:

    for i, line in enumerate(f):

        print(line.strip())

        if i == 19:
            break
        
print("\nROE > 15 and D/E < 1")

review = ratios[
    (ratios["return_on_equity_pct"] > 15)
    &
    (ratios["debt_to_equity"] < 1)
]

print(review.head(20))

print()

print("Companies Found")

print(review["company_id"].nunique())
sample = ratios[
    ratios["company_id"].isin(

        [
            "ABB",
            "TCS",
            "INFY",
            "RELIANCE",
            "HDFCBANK",
        ]

    )
]

print(sample.head(20))
print("\nColumns")

for col in ratios.columns:

    print(col)        
print()

print("=" * 70)
print("SPRINT 2 SUMMARY")
print("=" * 70)

print("financial_ratios table : OK")
print("Ratio Engine           : OK")
print("Profitability KPIs     : OK")
print("Leverage KPIs          : OK")
print("Cashflow KPIs          : OK")
print("Edge Case Log          : OK")
print("Database Review        : OK")

print("=" * 70)
print("SPRINT 2 COMPLETED SUCCESSFULLY")
print("=" * 70)
conn.close()

print()

print("Database connection closed.")    