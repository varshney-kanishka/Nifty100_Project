import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

DB_PATH = BASE_DIR / "data" / "database" / "nifty100.db"

OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# DATABASE CONNECTION
# ============================================================

conn = sqlite3.connect(DB_PATH)


# ============================================================
# LOAD TABLES
# ============================================================

profit = pd.read_sql(
    "SELECT * FROM profitandloss",
    conn
)

balance = pd.read_sql(
    "SELECT * FROM balancesheet",
    conn
)

companies = pd.read_sql(
    "SELECT * FROM companies",
    conn
)

sectors = pd.read_sql(
    "SELECT * FROM sectors",
    conn
)


print("=" * 70)
print("DAY 34 - CASH CONVERSION CYCLE ANALYSIS")
print("=" * 70)


# ============================================================
# TABLE SUMMARY
# ============================================================

print("\nTables Loaded")

print("Profit    :", len(profit))
print("Balance   :", len(balance))
print("Companies :", len(companies))
print("Sectors   :", len(sectors))


# ============================================================
# DISPLAY AVAILABLE COLUMNS
# ============================================================

print("\nProfit Columns")
print(profit.columns.tolist())

print("\nBalance Columns")
print(balance.columns.tolist())


# ============================================================
# NORMALIZE YEAR
# ============================================================

balance["year"] = balance["year"].astype(str).str.strip()
profit["year"] = profit["year"].astype(str).str.strip()


# ============================================================
# GET LATEST BALANCE SHEET RECORD
# ============================================================

balance = balance.sort_values(
    ["company_id", "year"]
)

latest_balance = (
    balance
    .groupby("company_id")
    .tail(1)
    .reset_index(drop=True)
)


print("\nLatest Companies :", len(latest_balance))


# ============================================================
# GET LATEST PROFIT & LOSS RECORD
# ============================================================

profit = profit.sort_values(
    ["company_id", "year"]
)

latest_profit = (
    profit
    .groupby("company_id")
    .tail(1)
    .reset_index(drop=True)
)


# ============================================================
# MERGE PROFIT + BALANCE
# ============================================================

latest = latest_balance.merge(
    latest_profit[
        [
            "company_id",
            "year",
            "sales",
            "expenses",
            "operating_profit",
            "net_profit"
        ]
    ],
    on="company_id",
    how="left",
    suffixes=("_balance", "_profit")
)


# ============================================================
# MERGE SECTOR INFORMATION
# ============================================================

latest = latest.merge(
    sectors[
        [
            "company_id",
            "broad_sector",
            "sub_sector",
            "market_cap_category"
        ]
    ],
    on="company_id",
    how="left"
)


# ============================================================
# CASH CONVERSION CYCLE DATA AVAILABILITY
# ============================================================

print("\nCCC Data Availability")

ccc_fields = {
    "Inventory": "inventory",
    "Receivables": "receivables",
    "Trade Payables": "trade_payables"
}

for label, column in ccc_fields.items():

    if column in latest.columns:
        print(f"{label:20}: AVAILABLE")
    else:
        print(f"{label:20}: NOT AVAILABLE")


# ============================================================
# IDENTIFY MISSING CCC COMPONENTS
# ============================================================

latest["inventory_available"] = (
    "inventory" in latest.columns
)

latest["receivables_available"] = (
    "receivables" in latest.columns
)

latest["payables_available"] = (
    "trade_payables" in latest.columns
)


# ============================================================
# CCC COMPONENT STATUS
# ============================================================

latest["ccc_status"] = np.where(
    (
        latest["inventory_available"]
        & latest["receivables_available"]
        & latest["payables_available"]
    ),
    "CCC Calculable",
    "CCC Data Unavailable"
)


# ============================================================
# SALES / EXPENSE VALIDATION
# ============================================================

latest["sales"] = pd.to_numeric(
    latest["sales"],
    errors="coerce"
)

latest["expenses"] = pd.to_numeric(
    latest["expenses"],
    errors="coerce"
)


# ============================================================
# OPERATING EXPENSE PROXY
# ============================================================

latest["operating_expense_ratio"] = np.where(
    latest["sales"] > 0,
    latest["expenses"] / latest["sales"],
    np.nan
)


latest["operating_expense_ratio"] = (
    latest["operating_expense_ratio"]
    .replace([np.inf, -np.inf], np.nan)
    .round(4)
)


# ============================================================
# WORKING CAPITAL PROXY
# ============================================================

latest["current_assets_proxy"] = (
    latest["other_asset"]
    + latest["investments"]
)

latest["current_liabilities_proxy"] = (
    latest["borrowings"]
    + latest["other_liabilities"]
)

latest["working_capital_proxy"] = (
    latest["current_assets_proxy"]
    - latest["current_liabilities_proxy"]
)


# ============================================================
# CURRENT RATIO PROXY
# ============================================================

latest["current_ratio_proxy"] = np.where(
    latest["current_liabilities_proxy"] != 0,
    latest["current_assets_proxy"]
    / latest["current_liabilities_proxy"],
    np.nan
)

latest["current_ratio_proxy"] = (
    latest["current_ratio_proxy"]
    .replace([np.inf, -np.inf], np.nan)
    .round(2)
)


# ============================================================
# WORKING CAPITAL STATUS
# ============================================================

latest["working_capital_status"] = np.where(
    latest["working_capital_proxy"] >= 0,
    "Positive",
    "Negative"
)


# ============================================================
# TOP COMPANIES BY WORKING CAPITAL PROXY
# ============================================================

print("\nTop Companies by Working Capital Proxy")

top_wc = (
    latest[
        [
            "company_id",
            "broad_sector",
            "working_capital_proxy",
            "current_ratio_proxy",
            "working_capital_status"
        ]
    ]
    .sort_values(
        "working_capital_proxy",
        ascending=False
    )
    .head(10)
)

print(top_wc)


# ============================================================
# NEGATIVE WORKING CAPITAL
# ============================================================

negative_wc = latest[
    latest["working_capital_proxy"] < 0
].copy()


print("\nNegative Working Capital Companies")

print(
    negative_wc[
        [
            "company_id",
            "broad_sector",
            "working_capital_proxy",
            "current_ratio_proxy"
        ]
    ]
    .sort_values(
        "working_capital_proxy"
    )
)


# ============================================================
# SECTOR SUMMARY
# ============================================================

sector_summary = (
    latest
    .groupby("broad_sector", dropna=False)
    .agg(
        companies=("company_id", "count"),
        avg_working_capital=(
            "working_capital_proxy",
            "mean"
        ),
        avg_current_ratio=(
            "current_ratio_proxy",
            "mean"
        ),
        negative_wc_companies=(
            "working_capital_status",
            lambda x: (x == "Negative").sum()
        )
    )
    .reset_index()
)


sector_summary[
    [
        "avg_working_capital",
        "avg_current_ratio"
    ]
] = sector_summary[
    [
        "avg_working_capital",
        "avg_current_ratio"
    ]
].round(2)


print("\nSector Working Capital Summary")

print(
    sector_summary
    .sort_values(
        "avg_working_capital",
        ascending=False
    )
)


# ============================================================
# CCC FORMULA INFORMATION
# ============================================================

print("\nCash Conversion Cycle Formula")

print("CCC = DIO + DSO - DPO")

print("\nDIO = Days Inventory Outstanding")
print("DSO = Days Sales Outstanding")
print("DPO = Days Payables Outstanding")


# ============================================================
# FINAL CCC STATUS
# ============================================================

ccc_available_count = (
    latest["ccc_status"]
    == "CCC Calculable"
).sum()

ccc_unavailable_count = (
    latest["ccc_status"]
    == "CCC Data Unavailable"
).sum()


print("\nCCC Calculation Status")

print(
    "CCC Calculable      :",
    ccc_available_count
)

print(
    "CCC Data Unavailable:",
    ccc_unavailable_count
)


# ============================================================
# EXPORT MAIN ANALYSIS
# ============================================================

output_file = (
    OUTPUT_DIR /
    "cash_conversion_cycle_analysis.xlsx"
)

latest.to_excel(
    output_file,
    index=False
)


# ============================================================
# EXPORT NEGATIVE WC
# ============================================================

negative_file = (
    OUTPUT_DIR /
    "ccc_negative_working_capital.csv"
)

negative_wc.to_csv(
    negative_file,
    index=False
)


# ============================================================
# EXPORT SECTOR SUMMARY
# ============================================================

sector_file = (
    OUTPUT_DIR /
    "ccc_sector_summary.xlsx"
)

sector_summary.to_excel(
    sector_file,
    index=False
)


# ============================================================
# CLOSE DATABASE
# ============================================================

conn.close()


# ============================================================
# COMPLETION
# ============================================================

print("\nFiles Created")

print(output_file)
print(negative_file)
print(sector_file)


print("\n" + "=" * 70)
print("DAY 34 COMPLETED")
print("=" * 70)