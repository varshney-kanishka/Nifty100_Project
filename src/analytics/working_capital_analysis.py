import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
BASE_DIR = Path(__file__).resolve().parents[2]

DB_PATH = BASE_DIR / "data" / "database" / "nifty100.db"

OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)
conn = sqlite3.connect(DB_PATH)

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
print("\nCompanies Columns:")
print(companies.columns.tolist())

print("\nSectors Columns:")
print(sectors.columns.tolist())

print("\nCompanies Sample:")
print(companies.head())

print("\nSectors Sample:")
print(sectors.head())

print("=" * 70)
print("DAY 33 - WORKING CAPITAL ANALYSIS")
print("=" * 70)

print("\nTables Loaded")

print("Profit   :", len(profit))
print("Balance  :", len(balance))
print("Companies:", len(companies))
print("Sectors  :", len(sectors))
balance = balance.sort_values("year")

latest_balance = (
    balance
    .groupby("company_id")
    .tail(1)
    .reset_index(drop=True)
)

print("\nLatest Companies :", len(latest_balance))
latest_balance["current_assets"] = (
    latest_balance["other_asset"] +
    latest_balance["investments"]
)
latest_balance["current_liabilities"] = (
    latest_balance["borrowings"] +
    latest_balance["other_liabilities"]
)
latest_balance["working_capital"] = (
    latest_balance["current_assets"] -
    latest_balance["current_liabilities"]
)
latest_balance["current_ratio"] = (
    latest_balance["current_assets"] /
    latest_balance["current_liabilities"]
)

latest_balance["current_ratio"] = (
    latest_balance["current_ratio"]
    .replace([np.inf, -np.inf], np.nan)
    .round(2)
)
latest_balance["wc_status"] = np.where(
    latest_balance["working_capital"] > 0,
    "Positive",
    "Negative"
)
#latest = latest_balance.merge(
    #companies,
    #on="company_id",
    #how="left"
#)
latest = latest_balance.copy()
print("\nTop Working Capital Companies")

print(
    latest[
        [
            "company_id",
            "working_capital",
            "current_ratio",
            "wc_status"
        ]
    ]
    .sort_values(
        "working_capital",
        ascending=False
    )
    .head(10)
)
weak = latest[
    latest["working_capital"] < 0
]

print("\nNegative Working Capital")

print(
    weak[
        [
            "company_id",
            "working_capital",
            "current_ratio"
        ]
    ]
)
latest.to_excel(
    OUTPUT_DIR / "working_capital_analysis.xlsx",
    index=False
)

weak.to_csv(
    OUTPUT_DIR / "negative_working_capital.csv",
    index=False
)
print("\nFiles Created")

print(OUTPUT_DIR / "working_capital_analysis.xlsx")
print(OUTPUT_DIR / "negative_working_capital.csv")

conn.close()

print("\n" + "=" * 70)
print("DAY 33 COMPLETED")
print("=" * 70)