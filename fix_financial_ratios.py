import sqlite3
import pandas as pd
from pathlib import Path

DB = Path("data/database/nifty100.db")
CSV = Path("data/processed/financial_ratios.csv")

print("Reading corrected CSV...")
df = pd.read_csv(CSV)

print("CSV shape:", df.shape)
print("CSV columns:")
print(df.columns.tolist())

expected_columns = [
    "id",
    "company_id",
    "year",
    "net_profit_margin_pct",
    "operating_profit_margin_pct",
    "return_on_equity_pct",
    "debt_to_equity",
    "interest_coverage",
    "asset_turnover",
    "free_cash_flow_cr",
    "capex_cr",
    "earnings_per_share",
    "book_value_per_share",
    "dividend_payout_ratio_pct",
    "total_debt_cr",
    "cash_from_operations_cr",
]

if df.columns.tolist() != expected_columns:
    raise ValueError(
        "CSV columns do not match expected schema.\n"
        f"Expected: {expected_columns}\n"
        f"Found:    {df.columns.tolist()}"
    )

print("\nConnecting to database...")
conn = sqlite3.connect(DB)

print("Replacing financial_ratios table...")

df.to_sql(
    "financial_ratios",
    conn,
    if_exists="replace",
    index=False,
)

conn.commit()

print("\nVerifying schema...")
schema = conn.execute(
    "PRAGMA table_info(financial_ratios)"
).fetchall()

for column in schema:
    print(column)

print("\nRow count:")
print(
    conn.execute(
        "SELECT COUNT(*) FROM financial_ratios"
    ).fetchone()[0]
)

print("\nFirst 2 rows:")
print(
    pd.read_sql_query(
        "SELECT * FROM financial_ratios LIMIT 2",
        conn,
    ).to_string(index=False)
)

conn.close()

print("\nSUCCESS: financial_ratios table repaired.")