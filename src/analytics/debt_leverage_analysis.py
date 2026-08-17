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

balance = pd.read_sql(
    "SELECT * FROM balancesheet",
    conn
)

profit = pd.read_sql(
    "SELECT * FROM profitandloss",
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
print("DAY 35 - DEBT & LEVERAGE ANALYSIS")
print("=" * 70)


print("\nTables Loaded")

print("Balance   :", len(balance))
print("Profit    :", len(profit))
print("Companies :", len(companies))
print("Sectors   :", len(sectors))


# ============================================================
# NORMALIZE COMPANY ID
# ============================================================

balance["company_id"] = (
    balance["company_id"]
    .astype(str)
    .str.strip()
)

profit["company_id"] = (
    profit["company_id"]
    .astype(str)
    .str.strip()
)


# ============================================================
# SORT BY REPORTING PERIOD
# ============================================================

balance = balance.sort_values(
    ["company_id", "year"]
)

profit = profit.sort_values(
    ["company_id", "year"]
)


# ============================================================
# GET LATEST BALANCE SHEET RECORD
# ============================================================

latest_balance = (
    balance
    .groupby("company_id")
    .tail(1)
    .reset_index(drop=True)
)


# ============================================================
# GET LATEST PROFIT & LOSS RECORD
# ============================================================

latest_profit = (
    profit
    .groupby("company_id")
    .tail(1)
    .reset_index(drop=True)
)


print("\nLatest Balance Records :", len(latest_balance))
print("Latest Profit Records  :", len(latest_profit))


# ============================================================
# CALCULATE EQUITY
# ============================================================

latest_balance["equity"] = (
    latest_balance["equity_capital"]
    + latest_balance["reserves"]
)


# ============================================================
# MERGE BALANCE + PROFIT
# ============================================================

latest = latest_balance.merge(
    latest_profit[
        [
            "company_id",
            "sales",
            "operating_profit",
            "interest",
            "net_profit"
        ]
    ],
    on="company_id",
    how="inner"
)


# ============================================================
# DEBT-TO-EQUITY RATIO
# ============================================================

latest["debt_to_equity"] = np.where(
    latest["equity"] != 0,
    latest["borrowings"] / latest["equity"],
    np.nan
)


# ============================================================
# DEBT RATIO
# ============================================================

latest["debt_ratio"] = np.where(
    latest["total_assets"] != 0,
    latest["borrowings"] / latest["total_assets"],
    np.nan
)


# ============================================================
# EQUITY RATIO
# ============================================================

latest["equity_ratio"] = np.where(
    latest["total_assets"] != 0,
    latest["equity"] / latest["total_assets"],
    np.nan
)


# ============================================================
# INTEREST COVERAGE RATIO
# ============================================================

latest["interest_coverage"] = np.where(
    latest["interest"] > 0,
    latest["operating_profit"] / latest["interest"],
    np.nan
)


# ============================================================
# FINANCIAL LEVERAGE
# ============================================================

latest["financial_leverage"] = np.where(
    latest["equity"] != 0,
    latest["total_assets"] / latest["equity"],
    np.nan
)


# ============================================================
# CLEAN EXTREME VALUES
# ============================================================

ratio_columns = [
    "debt_to_equity",
    "debt_ratio",
    "equity_ratio",
    "interest_coverage",
    "financial_leverage"
]

for column in ratio_columns:

    latest[column] = (
        latest[column]
        .replace([np.inf, -np.inf], np.nan)
        .round(2)
    )


# ============================================================
# LEVERAGE RISK CLASSIFICATION
# ============================================================

latest["leverage_risk"] = np.select(

    [
        latest["debt_to_equity"] <= 0.5,

        (
            (latest["debt_to_equity"] > 0.5)
            &
            (latest["debt_to_equity"] <= 1.0)
        ),

        latest["debt_to_equity"] > 1.0
    ],

    [
        "Low",
        "Moderate",
        "High"
    ],

    default="Unknown"
)


# ============================================================
# INTEREST COVERAGE CLASSIFICATION
# ============================================================

latest["interest_coverage_status"] = np.select(

    [
        latest["interest_coverage"] >= 5,

        (
            (latest["interest_coverage"] >= 2)
            &
            (latest["interest_coverage"] < 5)
        ),

        (
            (latest["interest_coverage"] >= 1)
            &
            (latest["interest_coverage"] < 2)
        ),

        latest["interest_coverage"] < 1
    ],

    [
        "Strong",
        "Adequate",
        "Weak",
        "Critical"
    ],

    default="Not Available"
)


# ============================================================
# MERGE COMPANY INFORMATION
# ============================================================

# companies uses "id" as the company identifier
companies_info = companies.rename(
    columns={
        "id": "company_id"
    }
)


latest = latest.merge(
    companies_info[
        [
            "company_id",
            "company_name",
            "roe_percentage",
            "roce_percentage"
        ]
    ],
    on="company_id",
    how="left"
)


# ============================================================
# DISPLAY TOP COMPANIES BY DEBT-TO-EQUITY
# ============================================================

print("\nTop Companies by Debt-to-Equity")


print(
    latest[
        [
            "company_id",
            "debt_to_equity",
            "debt_ratio",
            "financial_leverage",
            "leverage_risk"
        ]
    ]
    .sort_values(
        "debt_to_equity",
        ascending=False
    )
    .head(10)
)


# ============================================================
# LOW DEBT COMPANIES
# ============================================================

print("\nLowest Debt-to-Equity Companies")


print(
    latest[
        [
            "company_id",
            "debt_to_equity",
            "debt_ratio",
            "leverage_risk"
        ]
    ]
    .sort_values(
        "debt_to_equity",
        ascending=True
    )
    .head(10)
)


# ============================================================
# INTEREST COVERAGE
# ============================================================

print("\nCompanies With Weak Interest Coverage")


weak_interest = latest[
    latest["interest_coverage_status"].isin(
        ["Weak", "Critical"]
    )
]


print(
    weak_interest[
        [
            "company_id",
            "interest",
            "operating_profit",
            "interest_coverage",
            "interest_coverage_status"
        ]
    ]
    .sort_values(
        "interest_coverage",
        ascending=True
    )
)


# ============================================================
# LEVERAGE RISK SUMMARY
# ============================================================

print("\nLeverage Risk Summary")

print(
    latest["leverage_risk"]
    .value_counts()
)


# ============================================================
# SECTOR ANALYSIS
# ============================================================

sector_info = sectors[
    [
        "company_id",
        "broad_sector"
    ]
].drop_duplicates(
    "company_id"
)


latest = latest.merge(
    sector_info,
    on="company_id",
    how="left"
)


sector_summary = (
    latest
    .groupby("broad_sector", dropna=False)
    .agg(
        companies=("company_id", "count"),
        avg_debt_to_equity=("debt_to_equity", "mean"),
        avg_debt_ratio=("debt_ratio", "mean"),
        avg_interest_coverage=("interest_coverage", "mean"),
        high_leverage_companies=(
            "leverage_risk",
            lambda x: (x == "High").sum()
        )
    )
    .reset_index()
)


sector_summary[
    [
        "avg_debt_to_equity",
        "avg_debt_ratio",
        "avg_interest_coverage"
    ]
] = sector_summary[
    [
        "avg_debt_to_equity",
        "avg_debt_ratio",
        "avg_interest_coverage"
    ]
].round(2)


print("\nSector Leverage Summary")

print(
    sector_summary.sort_values(
        "avg_debt_to_equity",
        ascending=False
    )
)


# ============================================================
# SAVE OUTPUT
# ============================================================

analysis_file = (
    OUTPUT_DIR
    / "debt_leverage_analysis.xlsx"
)

risk_file = (
    OUTPUT_DIR
    / "high_leverage_companies.csv"
)

sector_file = (
    OUTPUT_DIR
    / "leverage_sector_summary.xlsx"
)


latest.to_excel(
    analysis_file,
    index=False
)


latest[
    latest["leverage_risk"] == "High"
].to_csv(
    risk_file,
    index=False
)


sector_summary.to_excel(
    sector_file,
    index=False
)


# ============================================================
# FINAL OUTPUT
# ============================================================

print("\nFiles Created")

print(analysis_file)
print(risk_file)
print(sector_file)


conn.close()


print("\n" + "=" * 70)
print("DAY 35 COMPLETED")
print("=" * 70)