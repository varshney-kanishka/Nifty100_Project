"""
Sprint 5 - Day 31
Cash Flow Intelligence Module

Generates:
output/cashflow_intelligence.xlsx
output/distress_alerts.csv
"""

import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

DB = BASE_DIR / "data/database/nifty100.db"
OUTPUT = BASE_DIR / "output"

OUTPUT.mkdir(parents=True, exist_ok=True)


# ============================================================
# CAPITAL ALLOCATION MAPPING
# ============================================================

CAPITAL_ALLOCATION_MAP = {
    ("+", "-", "-"): "Reinvestor",
    ("+", "+", "-"): "Liquidating Assets",
    ("-", "+", "+"): "Distress Signal",
    ("-", "-", "+"): "Growth Funded by Debt",
    ("+", "+", "+"): "Cash Accumulator",
    ("-", "-", "-"): "Pre-Revenue",
    ("+", "-", "+"): "Mixed",
    ("-", "+", "-"): "Unknown",
}


# ============================================================
# HELPERS
# ============================================================

def sign(value):
    """Return + for non-negative values and - for negative values."""

    if pd.isna(value):
        return None

    return "+" if value >= 0 else "-"


def capital_allocation_pattern(cfo, cfi, cff):
    """
    Classify capital allocation using CFO / CFI / CFF signs.
    """

    if pd.isna(cfo) or pd.isna(cfi) or pd.isna(cff):
        return None

    pattern = (
        sign(cfo),
        sign(cfi),
        sign(cff),
    )

    return CAPITAL_ALLOCATION_MAP.get(pattern, "Unknown")


def safe_cagr(first_value, last_value, years=5):
    """
    CAGR = (Ending / Beginning)^(1/years) - 1

    Returns percentage.
    """

    if pd.isna(first_value) or pd.isna(last_value):
        return np.nan

    if first_value <= 0 or last_value <= 0:
        return np.nan

    return ((last_value / first_value) ** (1 / years) - 1) * 100


def extract_year(value):
    """
    Extract a 4-digit year from a value.
    """

    match = pd.Series([str(value)]).str.extract(r"(\d{4})")[0].iloc[0]

    if pd.isna(match):
        return np.nan

    return int(match)


def remove_duplicate_company_year(df, name):
    """
    Remove duplicate company-year records.
    """

    before = len(df)

    # Remove completely identical rows
    df = df.drop_duplicates()

    # Keep only one record per company + year
    df = (
        df.sort_values(["company_id", "year"])
        .drop_duplicates(
            subset=["company_id", "year"],
            keep="last"
        )
        .reset_index(drop=True)
    )

    after = len(df)

    print(
        f"{name}: {before} -> {after} rows "
        f"(removed {before - after} duplicates)"
    )

    return df


def cfo_quality_label(value):
    """
    Classify CFO quality.
    """

    if pd.isna(value):
        return "Unknown"

    if value > 1.0:
        return "High Quality"

    if value >= 0.5:
        return "Moderate"

    return "Accrual Risk"


def capex_label(value):
    """
    Classify CapEx intensity.
    """

    if pd.isna(value):
        return "Unknown"

    if value < 3:
        return "Asset Light"

    if value <= 8:
        return "Moderate"

    return "Capital Intensive"


# ============================================================
# START
# ============================================================

print("=" * 70)
print("DAY 31 - CASH FLOW INTELLIGENCE")
print("=" * 70)

print("\nDatabase:")
print(DB)


# ============================================================
# CHECK DATABASE
# ============================================================

if not DB.exists():
    raise FileNotFoundError(
        f"Database not found:\n{DB}"
    )


# ============================================================
# LOAD DATABASE
# ============================================================

conn = sqlite3.connect(DB)

try:

    companies = pd.read_sql(
        "SELECT * FROM companies",
        conn,
    )

    profit = pd.read_sql(
        "SELECT * FROM profitandloss",
        conn,
    )

    cashflow = pd.read_sql(
        "SELECT * FROM cashflow",
        conn,
    )

    balance = pd.read_sql(
        "SELECT * FROM balancesheet",
        conn,
    )

    sectors = pd.read_sql(
        "SELECT company_id, broad_sector FROM sectors",
        conn,
    )

    print("\nTables Loaded")
    print("Companies :", len(companies))
    print("Profit    :", len(profit))
    print("Cash Flow :", len(cashflow))
    print("Balance   :", len(balance))
    print("Sectors   :", len(sectors))


    # ========================================================
    # CLEAN COMPANY IDs
    # ========================================================

    companies["id"] = (
        companies["id"]
        .astype(str)
        .str.strip()
    )

    profit["company_id"] = (
        profit["company_id"]
        .astype(str)
        .str.strip()
    )

    cashflow["company_id"] = (
        cashflow["company_id"]
        .astype(str)
        .str.strip()
    )

    balance["company_id"] = (
        balance["company_id"]
        .astype(str)
        .str.strip()
    )

    sectors["company_id"] = (
        sectors["company_id"]
        .astype(str)
        .str.strip()
    )


    # ========================================================
    # REMOVE DUPLICATES
    # ========================================================

    print("\nDuplicate Check")

    profit = remove_duplicate_company_year(
        profit,
        "P&L"
    )

    cashflow = remove_duplicate_company_year(
        cashflow,
        "Cash Flow"
    )

    balance = remove_duplicate_company_year(
        balance,
        "Balance Sheet"
    )


    # ========================================================
    # CLEAN YEARS
    # ========================================================

    profit["year_num"] = (
        profit["year"]
        .apply(extract_year)
    )

    cashflow["year_num"] = (
        cashflow["year"]
        .apply(extract_year)
    )

    balance["year_num"] = (
        balance["year"]
        .apply(extract_year)
    )


    # ========================================================
    # MERGE PROFIT + CASH FLOW
    # ========================================================

    profit_cols = [
        "company_id",
        "year",
        "year_num",
        "sales",
        "net_profit",
        "operating_profit",
    ]

    profit_data = profit[profit_cols].copy()


    cashflow_cols = [
        "company_id",
        "year",
        "year_num",
        "operating_activity",
        "investing_activity",
        "financing_activity",
        "net_cash_flow",
    ]

    cashflow_data = cashflow[cashflow_cols].copy()


    df = profit_data.merge(
        cashflow_data,
        on=[
            "company_id",
            "year",
            "year_num",
        ],
        how="left",
    )

    print(
        "\nMerged Profit + Cash Flow :",
        len(df)
    )


    # ========================================================
    # MERGE BALANCE SHEET
    # ========================================================

    balance_cols = [
        "company_id",
        "year",
        "year_num",
        "borrowings",
    ]

    balance_data = balance[balance_cols].copy()


    df = df.merge(
        balance_data,
        on=[
            "company_id",
            "year",
            "year_num",
        ],
        how="left",
    )

    print(
        "Merged Balance Sheet     :",
        len(df)
    )


    # ========================================================
    # FREE CASH FLOW
    # ========================================================

    df["fcf"] = (
        df["operating_activity"]
        + df["investing_activity"]
    )


    # ========================================================
    # CFO QUALITY
    # CFO / PAT
    # ========================================================

    df["cfo_pat_ratio"] = np.where(
        df["net_profit"].notna()
        & (df["net_profit"] != 0),

        df["operating_activity"]
        / df["net_profit"],

        np.nan,
    )


    # ========================================================
    # LATEST 5 YEARS
    # ========================================================

    df = df.sort_values(
        [
            "company_id",
            "year_num",
        ]
    )


    latest_5 = (
        df
        .groupby(
            "company_id",
            group_keys=False
        )
        .tail(5)
        .copy()
    )


    # ========================================================
    # CFO QUALITY SCORE
    # ========================================================

    cfo_quality = (
        latest_5
        .groupby("company_id")["cfo_pat_ratio"]
        .mean()
        .reset_index(
            name="cfo_quality_score"
        )
    )


    cfo_quality["cfo_quality_label"] = (
        cfo_quality[
            "cfo_quality_score"
        ]
        .apply(cfo_quality_label)
    )


    # ========================================================
    # LATEST YEAR
    # ========================================================

    latest = (
        df
        .sort_values("year_num")
        .groupby("company_id")
        .tail(1)
        .copy()
    )


    # ========================================================
    # CAPEX INTENSITY
    # abs(CFI) / Sales * 100
    # ========================================================

    latest["capex_intensity_pct"] = np.where(

        latest["sales"].notna()
        & (latest["sales"] != 0),

        abs(latest["investing_activity"])
        / latest["sales"]
        * 100,

        np.nan,
    )


    latest["capex_label"] = (
        latest[
            "capex_intensity_pct"
        ]
        .apply(capex_label)
    )


    # ========================================================
    # 5-YEAR FCF CAGR
    # ========================================================

    fcf_cagr_records = []


    for company_id, group in df.groupby(
        "company_id"
    ):

        group = (
            group
            .sort_values("year_num")
            .dropna(subset=["fcf"])
        )

        if len(group) < 6:

            fcf_cagr = np.nan

        else:

            beginning = group.iloc[-6]["fcf"]
            ending = group.iloc[-1]["fcf"]

            fcf_cagr = safe_cagr(
                beginning,
                ending,
                years=5,
            )


        fcf_cagr_records.append(
            {
                "company_id": company_id,
                "fcf_cagr_5yr": fcf_cagr,
            }
        )


    fcf_cagr_df = pd.DataFrame(
        fcf_cagr_records
    )


    # ========================================================
    # FCF CONVERSION
    # FCF / OPERATING PROFIT * 100
    # ========================================================

    latest["fcf_conversion_pct"] = np.where(

        latest["operating_profit"].notna()
        & (
            latest["operating_profit"] != 0
        ),

        latest["fcf"]
        / latest["operating_profit"]
        * 100,

        np.nan,
    )


    # ========================================================
    # DISTRESS SIGNAL
    # CFO < 0 AND CFF > 0
    # ========================================================

    latest["distress_flag"] = (

        latest["operating_activity"].notna()

        & latest["financing_activity"].notna()

        & (
            latest["operating_activity"] < 0
        )

        & (
            latest["financing_activity"] > 0
        )
    )


    # ========================================================
    # DELEVERAGING FLAG
    # CFF < 0 AND BORROWINGS DECLINING YOY
    # ========================================================

    balance_sorted = (
        balance
        .sort_values(
            [
                "company_id",
                "year_num",
            ]
        )
        .copy()
    )


    balance_sorted[
        "previous_borrowings"
    ] = (
        balance_sorted
        .groupby("company_id")[
            "borrowings"
        ]
        .shift(1)
    )


    latest_balance = (
        balance_sorted
        .groupby("company_id")
        .tail(1)
        .copy()
    )


    latest_balance[
        "borrowings_declining"
    ] = (

        latest_balance[
            "borrowings"
        ]

        <

        latest_balance[
            "previous_borrowings"
        ]
    )


    latest = latest.merge(

        latest_balance[
            [
                "company_id",
                "borrowings_declining",
            ]
        ],

        on="company_id",

        how="left",
    )


    latest["deleveraging_flag"] = (

        latest["financing_activity"].notna()

        & (
            latest["financing_activity"] < 0
        )

        & latest[
            "borrowings_declining"
        ].fillna(False)
    )


    # ========================================================
    # CAPITAL ALLOCATION
    # ========================================================

    latest["capital_allocation_label"] = (
        latest.apply(

            lambda row:
            capital_allocation_pattern(

                row["operating_activity"],

                row["investing_activity"],

                row["financing_activity"],
            ),

            axis=1,
        )
    )


    # ========================================================
    # KEEP MASTER COMPANY UNIVERSE
    # ========================================================

    latest = latest[
        latest["company_id"].isin(
            companies["id"]
        )
    ].copy()


    # ========================================================
    # SECTOR MAPPING
    # ========================================================

    company_sector = (
        sectors[
            [
                "company_id",
                "broad_sector",
            ]
        ]
        .rename(
            columns={
                "broad_sector": "sector"
            }
        )
    )


    print(
        "\nSector Mapping Loaded :",
        len(company_sector)
    )


    # ========================================================
    # FINAL DATASET
    # ========================================================

    final = latest[
        [
            "company_id",
            "capex_intensity_pct",
            "capex_label",
            "fcf_conversion_pct",
            "distress_flag",
            "deleveraging_flag",
            "capital_allocation_label",
        ]
    ].copy()


    # ========================================================
    # ADD CFO QUALITY
    # ========================================================

    final = final.merge(

        cfo_quality,

        on="company_id",

        how="left",
    )


    # ========================================================
    # ADD FCF CAGR
    # ========================================================

    final = final.merge(

        fcf_cagr_df,

        on="company_id",

        how="left",
    )


    # ========================================================
    # ADD SECTOR
    # ========================================================

    final = final.merge(

        company_sector,

        on="company_id",

        how="left",
    )


    # ========================================================
    # REQUIRED COLUMN ORDER
    # ========================================================

    final = final[
        [
            "company_id",
            "sector",
            "cfo_quality_score",
            "cfo_quality_label",
            "capex_intensity_pct",
            "capex_label",
            "fcf_cagr_5yr",
            "fcf_conversion_pct",
            "distress_flag",
            "deleveraging_flag",
            "capital_allocation_label",
        ]
    ]


    # ========================================================
    # SAVE CASH FLOW INTELLIGENCE
    # ========================================================

    excel_path = (
        OUTPUT
        / "cashflow_intelligence.xlsx"
    )


    final.to_excel(
        excel_path,
        index=False,
    )


    print(
        "\nCash Flow Intelligence:"
    )

    print(
        final.head()
        .to_string(index=False)
    )


    print(
        "\nRows :",
        len(final)
    )

    print(
        "Companies :",
        final["company_id"].nunique()
    )


    # ========================================================
    # SUMMARY
    # ========================================================

    print("\nCFO Quality:")

    print(
        final[
            "cfo_quality_label"
        ]
        .value_counts(
            dropna=False
        )
    )


    print("\nCapEx:")

    print(
        final[
            "capex_label"
        ]
        .value_counts(
            dropna=False
        )
    )


    print("\nCapital Allocation:")

    print(
        final[
            "capital_allocation_label"
        ]
        .value_counts(
            dropna=False
        )
    )


    # ========================================================
    # DISTRESS ALERTS
    # ========================================================

    distress = latest[
        latest["distress_flag"]
    ].copy()


    distress_alerts = distress[
        [
            "company_id",
            "operating_activity",
            "financing_activity",
            "net_profit",
        ]
    ].rename(
        columns={
            "operating_activity": "cfo",
            "financing_activity": "cff",
            "net_profit": "latest_net_profit",
        }
    )


    alerts_path = (
        OUTPUT
        / "distress_alerts.csv"
    )


    distress_alerts.to_csv(
        alerts_path,
        index=False,
    )


    # ========================================================
    # FINAL OUTPUT
    # ========================================================

    print("\nFiles Created:")

    print(excel_path)

    print(alerts_path)

    print(
        "\nDistress Alerts :",
        len(distress_alerts)
    )


finally:

    conn.close()


print("\n" + "=" * 70)
print("DAY 31 CASH FLOW INTELLIGENCE COMPLETED")
print("=" * 70)