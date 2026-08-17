import sqlite3
from pathlib import Path

import pandas as pd
from cashflow_kpis import *
from ratios import *

# =====================================================
# Database Connection
# =====================================================

BASE_DIR = Path(__file__).resolve().parents[2]
DB = BASE_DIR / "data" / "database" / "nifty100.db"

conn = sqlite3.connect(DB)

# =====================================================
# Read Tables
# =====================================================

profit = pd.read_sql(
    "SELECT * FROM profitandloss",
    conn,
)

balance = pd.read_sql(
    "SELECT * FROM balancesheet",
    conn,
)

cashflow = pd.read_sql(
    "SELECT * FROM cashflow",
    conn,
)

# =====================================================
# Make year datatype same
# =====================================================

profit["year"] = profit["year"].astype(str)
balance["year"] = balance["year"].astype(str)
cashflow["year"] = cashflow["year"].astype(str)

# =====================================================
# Base dataframe
# =====================================================

df = profit.copy()

# =====================================================
# Merge Balance Sheet
# =====================================================

df = df.merge(
    balance,
    on=["company_id", "year"],
    how="left",
    suffixes=("", "_b")
)

# =====================================================
# Merge Cashflow
# =====================================================

df = df.merge(
    cashflow,
    on=["company_id", "year"],
    how="left",
    suffixes=("", "_c")
)

# =====================================================
# Calculate Ratios
# =====================================================

df["net_profit_margin_pct"] = df.apply(
    lambda x: net_profit_margin(
        x["net_profit"],
        x["sales"]
    ),
    axis=1
)

df["operating_profit_margin_pct"] = df.apply(
    lambda x: operating_profit_margin(
        x["operating_profit"],
        x["sales"]
    ),
    axis=1
)

df["return_on_equity_pct"] = df.apply(
    lambda x: roe(
        x["net_profit"],
        x["equity_capital"],
        x["reserves"]
    ),
    axis=1
)

df["debt_to_equity"] = df.apply(
    lambda x: debt_to_equity(
        x["borrowings"],
        x["equity_capital"],
        x["reserves"]
    ),
    axis=1
)

df["interest_coverage"] = df.apply(
    lambda x: interest_coverage(
        x["operating_profit"],
        x["other_income"],
        x["interest"]
    ),
    axis=1
)

df["asset_turnover"] = df.apply(
    lambda x: asset_turnover(
        x["sales"],
        x["total_assets"]
    ),
    axis=1
)

df["free_cash_flow_cr"] = df.apply(
    lambda x: free_cash_flow(
        x["operating_activity"],
        x["investing_activity"]
    ),
    axis=1
)

df["cash_from_operations_cr"] = df.apply(
    lambda x: cash_from_operations(
        x["operating_activity"]
    ),
    axis=1
)

df["capex_cr"] = df["investing_activity"].abs()

# =====================================================
# Select Final Columns
# =====================================================

final = df[
    [
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
        "cash_from_operations_cr",
    ]
]

# =====================================================
# Replace financial_ratios table
# =====================================================

final.to_sql(
    "financial_ratios",
    conn,
    if_exists="replace",
    index=False
)

# =====================================================
# Verification
# =====================================================

print("\nfinancial_ratios updated successfully.")

count = pd.read_sql(
    """
    SELECT COUNT(*) AS total
    FROM financial_ratios
    """,
    conn,
)

print("\nTotal Rows")
print(count)

sample = pd.read_sql(
    """
    SELECT
        company_id,
        year,
        net_profit_margin_pct,
        return_on_equity_pct,
        debt_to_equity
    FROM financial_ratios
    LIMIT 10
    """,
    conn,
)

print("\nSample Data")
print(sample)

conn.close()