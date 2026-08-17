import sqlite3
from pathlib import Path

import pandas as pd

# =====================================================
# DATABASE
# =====================================================

BASE_DIR = Path(__file__).resolve().parents[2]
DB = BASE_DIR / "data/database/nifty100.db"

conn = sqlite3.connect(DB)

print("=" * 80)
print("KPI AUDIT - HDFC BANK & TCS")
print("=" * 80)

# =====================================================
# LOAD TABLES
# =====================================================

companies = pd.read_sql(
    "SELECT * FROM companies",
    conn
)

profit = pd.read_sql(
    "SELECT * FROM profitandloss",
    conn
)

balance = pd.read_sql(
    "SELECT * FROM balancesheet",
    conn
)

print("\nTABLES LOADED")
print("-" * 80)

# =====================================================
# FIND COMPANY IDs
# =====================================================

targets = companies[
    companies["company_name"].str.contains(
        "HDFC Bank|Tata Consultancy Services",
        case=False,
        na=False
    )
][["id", "company_name"]]

print("\nTARGET COMPANIES")
print(targets.to_string(index=False))

# =====================================================
# AUDIT EACH COMPANY
# =====================================================

for _, company in targets.iterrows():

    company_id = company["id"]
    company_name = company["company_name"]

    print("\n")
    print("=" * 80)
    print(company_name)
    print("company_id:", company_id)
    print("=" * 80)

    # -------------------------------------------------
    # PROFIT & LOSS
    # -------------------------------------------------

    p = profit[
        profit["company_id"] == company_id
    ].copy()

    p = p.sort_values("year")

    print("\nPROFIT & LOSS")
    print("-" * 80)

    print(
        p[
            [
                "company_id",
                "year",
                "sales",
                "net_profit",
                "operating_profit"
            ]
        ].tail(5).to_string(index=False)
    )

    # -------------------------------------------------
    # BALANCE SHEET
    # -------------------------------------------------

    b = balance[
        balance["company_id"] == company_id
    ].copy()

    b = b.sort_values("year")

    print("\nBALANCE SHEET")
    print("-" * 80)

    print(
        b[
            [
                "company_id",
                "year",
                "equity_capital",
                "reserves",
                "borrowings",
                "total_assets"
            ]
        ].tail(5).to_string(index=False)
    )

    # -------------------------------------------------
    # LATEST P&L
    # -------------------------------------------------

    latest_p = p.iloc[-1]

    sales = latest_p["sales"]
    net_profit = latest_p["net_profit"]
    operating_profit = latest_p["operating_profit"]

    # -------------------------------------------------
    # LATEST BALANCE SHEET
    # -------------------------------------------------

    latest_b = b.iloc[-1]

    equity_capital = latest_b["equity_capital"]
    reserves = latest_b["reserves"]

    # -------------------------------------------------
    # CALCULATE OPM
    # -------------------------------------------------

    if sales != 0:
        opm = (operating_profit / sales) * 100
    else:
        opm = None

    # -------------------------------------------------
    # CALCULATE ROE
    # -------------------------------------------------

    equity = equity_capital + reserves

    if equity != 0:
        roe = (net_profit / equity) * 100
    else:
        roe = None

    # -------------------------------------------------
    # SHOW CALCULATIONS
    # -------------------------------------------------

    print("\nLATEST YEAR CALCULATION")
    print("-" * 80)

    print("Year              :", latest_p["year"])
    print("Sales             :", sales)
    print("Operating Profit  :", operating_profit)
    print("Net Profit        :", net_profit)

    print("Equity Capital    :", equity_capital)
    print("Reserves          :", reserves)
    print("Total Equity      :", equity)

    print("\nCalculated OPM    :", opm)
    print("Calculated ROE    :", roe)

    print("\nFormula check:")
    print(
        f"OPM = ({operating_profit} / {sales}) * 100"
    )

    print(
        f"ROE = ({net_profit} / "
        f"({equity_capital} + {reserves})) * 100"
    )

conn.close()

print("\n")
print("=" * 80)
print("AUDIT COMPLETED")
print("=" * 80)