from pathlib import Path
import sqlite3
import pandas as pd

from src.analytics.ratios import *
from src.analytics.cagr import *
from src.analytics.cashflow_kpis import *

# =====================================================
# DATABASE CONNECTION
# =====================================================

BASE_DIR = Path(__file__).resolve().parents[2]

DB = BASE_DIR / "data/database/nifty100.db"

conn = sqlite3.connect(DB)

print("=" * 70)
print("CONNECTED TO DATABASE")
print("=" * 70)

# =====================================================
# READ TABLES
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

companies = pd.read_sql(
    "SELECT * FROM companies",
    conn,
)

sectors = pd.read_sql(
    "SELECT * FROM sectors",
    conn,
)

print("\nTABLES LOADED SUCCESSFULLY")
print("-" * 70)

print(f"profitandloss : {len(profit)} rows")
print(f"balancesheet  : {len(balance)} rows")
print(f"cashflow      : {len(cashflow)} rows")
print(f"companies     : {len(companies)} rows")
print(f"sectors       : {len(sectors)} rows")
# =====================================================
# STANDARDIZE YEAR COLUMN
# =====================================================

profit["year"] = profit["year"].astype(str).str.strip()
balance["year"] = balance["year"].astype(str).str.strip()
cashflow["year"] = cashflow["year"].astype(str).str.strip()

print("\nYEAR COLUMN STANDARDIZED")
# =====================================================
# REMOVE DUPLICATES
# =====================================================

profit = profit.drop_duplicates(
    subset=["company_id", "year"]
)

balance = balance.drop_duplicates(
    subset=["company_id", "year"]
)

cashflow = cashflow.drop_duplicates(
    subset=["company_id", "year"]
)

print("\nAFTER REMOVING DUPLICATES")
print("-" * 70)

print(f"profitandloss : {len(profit)} rows")
print(f"balancesheet  : {len(balance)} rows")
print(f"cashflow      : {len(cashflow)} rows")
# =====================================================
# CREATE MASTER DATAFRAME
# =====================================================

df = profit.copy()

print("\nMASTER DATAFRAME CREATED")
print(f"Rows : {len(df)}")
# =====================================================
# MERGE BALANCE SHEET
# =====================================================

df = df.merge(

    balance,

    on=["company_id", "year"],

    how="left",

    suffixes=("", "_balance"),

    validate="one_to_one",

)

print("\nBALANCE SHEET MERGED")
print(f"Rows : {len(df)}")
# =====================================================
# MERGE CASHFLOW
# =====================================================

df = df.merge(

    cashflow,

    on=["company_id", "year"],

    how="left",

    suffixes=("", "_cashflow"),

    validate="one_to_one",

)

print("\nCASHFLOW MERGED")
print(f"Rows : {len(df)}")
# =====================================================
# MERGE SECTOR
# =====================================================

df = df.merge(

    sectors[
        [
            "company_id",
            "broad_sector"
        ]
    ],

    on="company_id",

    how="left",

)

print("\nSECTOR MERGED")
print(f"Rows : {len(df)}")
# =====================================================
# VERIFY DATAFRAME
# =====================================================

print("\nFINAL DATAFRAME")
print("=" * 70)

print(df.head())

print("\nShape")
print(df.shape)

print("\nColumns")
print(df.columns.tolist())
# =====================================================
# PROFITABILITY RATIOS
# =====================================================

df["net_profit_margin_pct"] = df.apply(
    lambda x: net_profit_margin(
        x["net_profit"],
        x["sales"],
    ),
    axis=1,
)

df["operating_profit_margin_pct"] = df.apply(
    lambda x: operating_profit_margin(
        x["operating_profit"],
        x["sales"],
    ),
    axis=1,
)

df["return_on_equity_pct"] = df.apply(
    lambda x: roe(
        x["net_profit"],
        x["equity_capital"],
        x["reserves"],
    ),
    axis=1,
)

df["return_on_capital_employed_pct"] = df.apply(
    lambda x: roce(
        x["operating_profit"],
        x["equity_capital"],
        x["reserves"],
        x["borrowings"],
    ),
    axis=1,
)

df["return_on_assets_pct"] = df.apply(
    lambda x: roa(
        x["net_profit"],
        x["total_assets"],
    ),
    axis=1,
)

print("\nProfitability ratios calculated.")
# =====================================================
# LEVERAGE RATIOS
# =====================================================

df["debt_to_equity"] = df.apply(
    lambda x: debt_to_equity(
        x["borrowings"],
        x["equity_capital"],
        x["reserves"],
    ),
    axis=1,
)

df["interest_coverage"] = df.apply(
    lambda x: interest_coverage(
        x["operating_profit"],
        x["other_income"],
        x["interest"],
    ),
    axis=1,
)

df["asset_turnover"] = df.apply(
    lambda x: asset_turnover(
        x["sales"],
        x["total_assets"],
    ),
    axis=1,
)

df["net_debt"] = df.apply(
    lambda x: net_debt(
        x["borrowings"],
        x["investments"],
    ),
    axis=1,
)

print("Leverage ratios calculated.")
# =====================================================
# CASH FLOW KPIs
# =====================================================

df["free_cash_flow_cr"] = df.apply(
    lambda x: free_cash_flow(
        x["operating_activity"],
        x["investing_activity"],
    ),
    axis=1,
)

df["cash_from_operations_cr"] = df["operating_activity"]

df["capex_cr"] = df["investing_activity"].abs()

print("Cashflow KPIs calculated.")
# =====================================================
# VERIFY KPI COLUMNS
# =====================================================

print("\nCalculated KPI Sample")

print(
    df[
        [
            "company_id",
            "year",
            "net_profit_margin_pct",
            "return_on_equity_pct",
            "debt_to_equity",
            "interest_coverage",
            "asset_turnover",
            "free_cash_flow_cr",
        ]
    ].head(10)
)
# =====================================================
# SELECT FINAL COLUMNS
# =====================================================

final = df[
    [
        "id",
        "company_id",
        "year",

        "net_profit_margin_pct",
        "operating_profit_margin_pct",
        "return_on_equity_pct",
        "return_on_capital_employed_pct",

        "debt_to_equity",
        "interest_coverage",
        "asset_turnover",

        "free_cash_flow_cr",
        "capex_cr",
        "cash_from_operations_cr",

        "eps",

        "dividend_payout",

        "borrowings",
    ]
].copy()

# Rename columns to match the financial_ratios table

final.rename(
    columns={
        "eps": "earnings_per_share",
        "dividend_payout": "dividend_payout_ratio_pct",
        "borrowings": "total_debt_cr",
    },
    inplace=True,
)

print("\nFinal DataFrame Created")
print("-" * 70)
print(final.head())
print("\nShape:", final.shape)
# =====================================================
# SAVE TO SQLITE
# =====================================================

final.to_sql(

    "financial_ratios",

    conn,

    if_exists="replace",

    index=False,

)

print("\nfinancial_ratios table updated successfully.")
# =====================================================
# VERIFY DATABASE
# =====================================================

count = pd.read_sql(

    """
    SELECT COUNT(*) AS total
    FROM financial_ratios
    """,

    conn,

)

print("\nTotal Rows in financial_ratios")
print(count)

sample = pd.read_sql(

    """
    SELECT
        company_id,
        year,
        return_on_equity_pct,
        debt_to_equity,
        net_profit_margin_pct
    FROM financial_ratios
    LIMIT 10
    """,

    conn,

)

print("\nSample Records")
print(sample)
# =====================================================
# CLOSE DATABASE
# =====================================================

conn.close()

print("\nDatabase connection closed.")
print("=" * 70)
print("DAY 12 COMPLETED SUCCESSFULLY")
print("=" * 70)