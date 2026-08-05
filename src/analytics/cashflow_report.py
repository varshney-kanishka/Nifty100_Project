import sqlite3
from pathlib import Path

import pandas as pd

print("=" * 70)
print("DAY 31 - CASH FLOW INTELLIGENCE")
print("=" * 70)

BASE_DIR = Path(__file__).resolve().parents[2]

DB = BASE_DIR / "data/database/nifty100.db"
OUTPUT = BASE_DIR / "output"

conn = sqlite3.connect(DB)

cashflow = pd.read_sql(
    "SELECT * FROM cashflow",
    conn,
)

profit = pd.read_sql(
    "SELECT * FROM profitandloss",
    conn,
)

balance = pd.read_sql(
    "SELECT * FROM balancesheet",
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

print("\nTables Loaded")
print("Cashflow :", len(cashflow))
print("Profit   :", len(profit))
print("Balance  :", len(balance))
print("Companies:", len(companies))
df = cashflow.copy()

df = df.merge(
    profit[
        [
            "company_id",
            "year",
            "sales",
            "operating_profit",
            "net_profit",
        ]
    ],
    on=["company_id", "year"],
    how="left",
)

df = df.merge(
    balance[
        [
            "company_id",
            "year",
            "borrowings",
        ]
    ],
    on=["company_id", "year"],
    how="left",
)

df = df.merge(
    sectors[
        [
            "company_id",
            "broad_sector",
        ]
    ],
    on="company_id",
    how="left",
)

df = df.merge(
    companies[
        [
            "id",
            "company_name",
        ]
    ],
    left_on="company_id",
    right_on="id",
    how="left",
)

df.drop(
    columns=["id_x", "id_y", "id"],
    errors="ignore",
    inplace=True,
)
# Fix inconsistent ticker names

df["company_id"] = (
    df["company_id"]
    .astype(str)
    .str.strip()
    .replace({
        "AGTL": "ATGL"
    })
)

profit["company_id"] = (
    profit["company_id"]
    .astype(str)
    .str.strip()
    .replace({
        "AGTL": "ATGL"
    })
)

balance["company_id"] = (
    balance["company_id"]
    .astype(str)
    .str.strip()
    .replace({
        "AGTL": "ATGL"
    })
)

companies["id"] = (
    companies["id"]
    .astype(str)
    .str.strip()
)

sectors["company_id"] = (
    sectors["company_id"]
    .astype(str)
    .str.strip()
)
# --------------------------------------------------
# Remove TTM
# --------------------------------------------------

df = df[
    df["year"].notna()
].copy()

df = df[
    ~df["year"].str.upper().eq("TTM")
].copy()


# --------------------------------------------------
# Extract Year
# Works for:
# Mar-24
# Mar 2024
# Dec 2023
# Sep 2024
# --------------------------------------------------

df["year_num"] = (
    df["year"]
    .str.extract(r"(\d{2,4})")[0]
)

df["year_num"] = pd.to_numeric(
    df["year_num"],
    errors="coerce",
)


# Convert 2-digit years to 2000+

df.loc[
    df["year_num"] < 100,
    "year_num"
] += 2000


df = df.dropna(
    subset=["year_num"]
)

df["year_num"] = (
    df["year_num"]
    .astype(int)
)


# --------------------------------------------------
# Keep only companies present in master table
# --------------------------------------------------

valid_companies = (
    companies["id"]
    .astype(str)
    .str.strip()
    .unique()
)

df = df[
    df["company_id"].isin(valid_companies)
]


# --------------------------------------------------
# Latest financial year per company
# --------------------------------------------------

latest = (
    df
    .sort_values(
        ["company_id", "year_num"]
    )
    .drop_duplicates(
        subset="company_id",
        keep="last",
    )
)

print(
    "\nLatest Companies :",
    latest["company_id"].nunique()
)
# --------------------------------------------------
# CFO / PAT Ratio
# --------------------------------------------------

df["cfo_pat_ratio"] = (
    df["operating_activity"]
    /
    df["net_profit"]
)

quality = (
    df.groupby("company_id")[
        "cfo_pat_ratio"
    ]
    .mean()
    .reset_index()
)

quality.columns = [
    "company_id",
    "cfo_quality_score",
]


def cfo_label(score):

    if pd.isna(score):
        return "Unknown"

    if score > 1:
        return "High Quality"

    if score >= 0.5:
        return "Moderate"

    return "Accrual Risk"


quality["cfo_quality_label"] = (
    quality["cfo_quality_score"]
    .apply(cfo_label)
)

latest = latest.merge(
    quality,
    on="company_id",
    how="left",
)
# --------------------------------------------------
# CapEx Intensity
# --------------------------------------------------

latest["capex_intensity_pct"] = (
    latest["investing_activity"].abs()
    / latest["sales"]
) * 100


def capex_label(value):

    if pd.isna(value):
        return "Unknown"

    if value < 3:
        return "Asset Light"

    elif value <= 8:
        return "Moderate"

    else:
        return "Capital Intensive"


latest["capex_label"] = (
    latest["capex_intensity_pct"]
    .apply(capex_label)
)


# --------------------------------------------------
# Distress Signal
# --------------------------------------------------

latest["distress_flag"] = (
    (latest["operating_activity"] < 0)
    &
    (latest["financing_activity"] > 0)
)


# --------------------------------------------------
# Deleveraging Flag
# --------------------------------------------------

latest["deleveraging_flag"] = (
    latest["financing_activity"] < 0
)


# --------------------------------------------------
# Capital Allocation
# --------------------------------------------------

def capital_allocation(row):

    cfo = row["operating_activity"]
    cfi = row["investing_activity"]
    cff = row["financing_activity"]

    if pd.isna(cfo) or pd.isna(cfi) or pd.isna(cff):
        return "Unknown"

    if cfo > 0 and cfi < 0 and cff < 0:
        return "Reinvestor"

    elif cfo > 0 and cfi > 0 and cff < 0:
        return "Liquidating Assets"

    elif cfo < 0 and cfi > 0 and cff > 0:
        return "Distress Signal"

    elif cfo < 0 and cfi < 0 and cff > 0:
        return "Growth Funded by Debt"

    elif cfo > 0 and cfi > 0 and cff > 0:
        return "Cash Accumulator"

    elif cfo < 0 and cfi < 0 and cff < 0:
        return "Pre-Revenue"

    elif cfo > 0 and cfi < 0 and cff > 0:
        return "Mixed"

    else:
        return "Neutral"


latest["capital_allocation_label"] = (
    latest.apply(
        capital_allocation,
        axis=1,
    )
)


# --------------------------------------------------
# Final Report
# --------------------------------------------------

report = latest[
    [
        "company_id",
        "company_name",
        "broad_sector",
        "cfo_quality_score",
        "cfo_quality_label",
        "capex_intensity_pct",
        "capex_label",
        "distress_flag",
        "deleveraging_flag",
        "capital_allocation_label",
    ]
].copy()


report = report.sort_values("company_id")


# --------------------------------------------------
# Save Excel
# --------------------------------------------------

report.to_excel(
    OUTPUT / "cashflow_intelligence.xlsx",
    index=False,
)


# --------------------------------------------------
# Distress Alerts
# --------------------------------------------------

alerts = latest[
    latest["distress_flag"]
][
    [
        "company_id",
        "company_name",
        "operating_activity",
        "financing_activity",
        "net_profit",
    ]
]

alerts.to_csv(
    OUTPUT / "distress_alerts.csv",
    index=False,
)


# --------------------------------------------------
# Summary
# --------------------------------------------------

print("\nFiles Created")

print(
    OUTPUT / "cashflow_intelligence.xlsx"
)

print(
    OUTPUT / "distress_alerts.csv"
)

print("\nCompanies :", len(report))

print("Distress Companies :", len(alerts))

print("\nLatest Companies :", report["company_id"].nunique())

print("\n" + "=" * 70)
print("DAY 31 COMPLETED")
print("=" * 70)

conn.close()

