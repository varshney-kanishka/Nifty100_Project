import sqlite3
from pathlib import Path

import pandas as pd

print("=" * 70)
print("DAY 26 - VALUATION MODULE")
print("=" * 70)

BASE_DIR = Path(__file__).resolve().parents[2]

DB = BASE_DIR / "data/database/nifty100.db"

OUTPUT = BASE_DIR / "output"
OUTPUT.mkdir(exist_ok=True)

conn = sqlite3.connect(DB)

ratios = pd.read_sql(
    "SELECT * FROM financial_ratios",
    conn,
)

market = pd.read_sql(
    "SELECT * FROM market_cap",
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
print("Ratios    :", len(ratios))
print("MarketCap :", len(market))
print("Companies :", len(companies))
print("Sectors   :", len(sectors))
# Get latest market cap for each company
market_latest = (
    market.sort_values("year")
          .groupby("company_id")
          .tail(1)
)
# Keep only companies present in companies table
valid_companies = companies["id"].astype(str).str.strip().unique()

ratios["company_id"] = ratios["company_id"].astype(str).str.strip()

ratios = ratios[
    ratios["company_id"].isin(valid_companies)
]

print("\nAfter Filtering")
print("Unique Ratio Companies :", ratios["company_id"].nunique())

# Merge using company_id only
df = ratios.merge(
    market_latest,
    on="company_id",
    how="left",
)


# Merge Company Names
df = df.merge(
    companies[["id", "company_name"]],
    left_on="company_id",
    right_on="id",
    how="left",
)

# Merge Sector
df = df.merge(
    sectors[["company_id", "broad_sector"]],
    on="company_id",
    how="left",
)

print("\nMerged Successfully")
print(df.head())
# Remove TTM
df = df[df["year_x"] != "TTM"].copy()

# Extract year
df["year_num"] = (
    df["year_x"]
      .str.extract(r"(\d{4})")[0]
      .astype(int)
)

# Latest annual record for each company
latest = (
    df.sort_values("year_num")
      .drop_duplicates(subset="company_id", keep="last")
)

print("\nLatest Records")
print("Rows :", len(latest))
print("Unique Companies :", latest["company_id"].nunique())
# FCF Yield
latest["FCF_yield_pct"] = (
    latest["free_cash_flow_cr"]
    / latest["market_cap_crore"]
) * 100

print("\nFCF Yield Calculated")

# -------------------------------
# Sector Median P/E
# -------------------------------
sector_pe = (
    latest.groupby("broad_sector")["pe_ratio"]
    .median()
    .reset_index()
    .rename(columns={"pe_ratio": "sector_median_pe"})
)

latest = latest.merge(
    sector_pe,
    on="broad_sector",
    how="left",
)

# -------------------------------
# P/E vs Sector Median
# -------------------------------
latest["PE_vs_sector_median_pct"] = (
    latest["pe_ratio"]
    / latest["sector_median_pe"]
) * 100

# -------------------------------
# Valuation Flag
# -------------------------------
def get_flag(row):
    if pd.isna(row["pe_ratio"]) or pd.isna(row["sector_median_pe"]):
        return "N/A"
    elif row["pe_ratio"] > row["sector_median_pe"] * 1.5:
        return "Caution"
    elif row["pe_ratio"] < row["sector_median_pe"] * 0.7:
        return "Discount"
    else:
        return "Fair"

latest["flag"] = latest.apply(get_flag, axis=1)

# -------------------------------
# Final Report
# -------------------------------
valuation = latest[
    [
        "company_id",
        "company_name",
        "broad_sector",
        "pe_ratio",
        "pb_ratio",
        "ev_ebitda",
        "FCF_yield_pct",
        "sector_median_pe",
        "PE_vs_sector_median_pct",
        "flag",
    ]
]

# Rename column for deliverable
valuation = valuation.rename(
    columns={
        "broad_sector": "sector",
        "sector_median_pe": "5yr_median_PE",
    }
)

# -------------------------------
# Export Excel
# -------------------------------
valuation.to_excel(
    OUTPUT / "valuation_summary.xlsx",
    index=False,
)

# -------------------------------
# Export Flagged Companies
# -------------------------------
flags = valuation[
    valuation["flag"].isin(["Caution", "Discount"])
]

flags.to_csv(
    OUTPUT / "valuation_flags.csv",
    index=False,
)

# -------------------------------
# Summary
# -------------------------------
print("\nFiles Created")
print(OUTPUT / "valuation_summary.xlsx")
print(OUTPUT / "valuation_flags.csv")

print("\nFlag Summary")
print(valuation["flag"].value_counts())

print("\n" + "=" * 70)
print("\nRows in valuation_summary :", len(valuation))
print("Rows in valuation_flags   :", len(flags))
print("DAY 26 COMPLETED")
print("=" * 70)
conn.close()
