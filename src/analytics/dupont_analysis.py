import math
import sqlite3
from pathlib import Path

import pandas as pd

print("=" * 70)
print("DAY 32 - DUPONT ANALYSIS")
print("=" * 70)

# --------------------------------------------------
# Paths
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]

DB = BASE_DIR / "data/database/nifty100.db"

OUTPUT = BASE_DIR / "output"

# --------------------------------------------------
# Database Connection
# --------------------------------------------------

conn = sqlite3.connect(DB)

# --------------------------------------------------
# Load Tables
# --------------------------------------------------

profit = pd.read_sql(
    "SELECT * FROM profitandloss",
    conn,
)

# Load raw P&L values without unconditional unit conversion.
profit["sales"] = pd.to_numeric(profit["sales"], errors="coerce").astype(float)
profit["net_profit"] = pd.to_numeric(profit["net_profit"], errors="coerce").astype(float)
profit["year"] = profit["year"].astype("string").str.replace(r"\.0$", "", regex=True).str.strip()

# Use only annual March reporting periods to avoid interim statement duplicates like Sep 2024.
profit = profit[profit["year"].str.startswith("Mar", na=False)].copy()

balance = pd.read_sql(
    "SELECT * FROM balancesheet",
    conn,
)
balance["year"] = balance["year"].astype("string").str.replace(r"\.0$", "", regex=True).str.strip()

# Use only annual March reporting periods to avoid interim statement duplicates like Sep 2024.
balance = balance[balance["year"].str.startswith("Mar", na=False)].copy()

companies = pd.read_sql(
    "SELECT * FROM companies",
    conn,
)

sectors = pd.read_sql(
    "SELECT * FROM sectors",
    conn,
)

print("\nTables Loaded")

print("Profit    :", len(profit))
print("Balance   :", len(balance))
print("Companies :", len(companies))
print("Sectors   :", len(sectors))


def _describe_series(name, series):
    numeric = pd.to_numeric(series, errors="coerce")
    print(
        f"{name}: count={numeric.count()} min={numeric.min()} max={numeric.max()} "
        f"median={numeric.median()} mean={numeric.mean():.2f} std={numeric.std():.2f}"
    )


def _select_year_column(df):
    if "year" in df.columns:
        return "year"
    if "Year" in df.columns:
        return "Year"
    return None


def _load_raw_sheet(sheet_name):
    path = BASE_DIR / "data" / "raw" / f"{sheet_name}.xlsx"
    df = pd.read_excel(path, header=1)
    year_col = _select_year_column(df)
    if year_col is not None:
        df[year_col] = df[year_col].astype("string").str.strip()
        df = df[df[year_col].str.startswith("Mar", na=False)].copy()
    return df


def _best_scaling_factor(sales, total_assets):
    if pd.isna(sales) or pd.isna(total_assets) or sales <= 0 or total_assets <= 0:
        return 1.0, 1.0

    target_low = 0.2
    target_high = 3.0
    best_score = abs(math.log10(sales / total_assets))
    best_factors = (1.0, 1.0)

    profit_factors = [1.0, 0.1, 0.01, 0.001]
    balance_factors = [1.0, 10.0, 100.0, 1000.0]

    for profit_factor in profit_factors:
        for balance_factor in balance_factors:
            scaled_sales = sales * profit_factor
            scaled_assets = total_assets * balance_factor
            if scaled_assets <= 0:
                continue
            turnover = scaled_sales / scaled_assets
            if turnover <= 0:
                continue

            if target_low <= turnover <= target_high:
                return profit_factor, balance_factor

            score = min(
                abs(math.log10(turnover / target_low)),
                abs(math.log10(turnover / target_high)),
            )
            if score < best_score:
                best_score = score
                best_factors = (profit_factor, balance_factor)

    return best_factors


def _detect_unit_scaling(df):
    candidate_sales = [1.0, 0.1, 0.01, 0.001]
    candidate_assets = [1.0, 10.0, 100.0, 1000.0]

    def score(turnover):
        if turnover <= 0:
            return float("inf")
        low, high = 0.2, 3.0
        if low <= turnover <= high:
            return 0.0
        return min(abs(math.log10(turnover / low)), abs(math.log10(turnover / high)))

    scaling = {}
    for company_id, group in df.groupby("company_id"):
        working = group[
            group["sales"].gt(0)
            & group["total_assets"].gt(0)
            & group["year"].astype(str).str.startswith("Mar", na=False)
        ].copy()

        if working.empty:
            scaling[company_id] = (1.0, 1.0)
            continue

        best = (1.0, 1.0, float("inf"))
        for sales_factor in candidate_sales:
            for assets_factor in candidate_assets:
                scaled_turnovers = (working["sales"] * sales_factor) / (
                    working["total_assets"] * assets_factor
                )
                median_turnover = scaled_turnovers.median()
                current_score = score(median_turnover)
                if current_score < best[2]:
                    best = (sales_factor, assets_factor, current_score)

        scaling[company_id] = (best[0], best[1])

    return scaling


def _apply_unit_normalization(df, scaling_map):
    df["sales_raw"] = df["sales"].copy()
    df["net_profit_raw"] = df["net_profit"].copy()
    df["equity_capital_raw"] = df["equity_capital"].copy()
    df["reserves_raw"] = df["reserves"].copy()
    df["total_assets_raw"] = df["total_assets"].copy()

    sales_factors = {k: v[0] for k, v in scaling_map.items()}
    assets_factors = {k: v[1] for k, v in scaling_map.items()}

    df["sales_factor"] = df["company_id"].map(sales_factors).fillna(1.0)
    df["assets_factor"] = df["company_id"].map(assets_factors).fillna(1.0)

    df["sales"] = df["sales"] * df["sales_factor"]
    df["net_profit"] = df["net_profit"] * df["sales_factor"]
    df["equity_capital"] = df["equity_capital"] * df["assets_factor"]
    df["reserves"] = df["reserves"] * df["assets_factor"]
    df["total_assets"] = df["total_assets"] * df["assets_factor"]

    return df


def _print_raw_vs_db_stats():
    print("\nRAW EXCEL VS SQLITE VALUE STATS")
    raw_profit = _load_raw_sheet("profitandloss")
    raw_balance = _load_raw_sheet("balancesheet")

    for label, raw_df, cols in [
        ("profit", raw_profit, ["sales", "net_profit"]),
        ("balance", raw_balance, ["equity_capital", "reserves", "total_assets"]),
    ]:
        print(f"\nRaw {label} stats")
        for col in cols:
            if col in raw_df.columns:
                _describe_series(col, raw_df[col])

    print("\nSQLite profit stats")
    _describe_series("sales", profit["sales"])
    _describe_series("net_profit", profit["net_profit"])
    print("\nSQLite balance stats")
    _describe_series("total_assets", balance["total_assets"])
    _describe_series("equity_capital", balance["equity_capital"])
    _describe_series("reserves", balance["reserves"])

_print_raw_vs_db_stats()
# --------------------------------------------------
# Merge Profit & Balance Sheet
# --------------------------------------------------

df = profit.merge(
    balance[
        [
            "company_id",
            "year",
            "equity_capital",
            "reserves",
            "borrowings",
            "total_assets",
        ]
    ],
    on=["company_id", "year"],
    how="left",
)

# Convert merged balance values to numeric.
df["equity_capital"] = pd.to_numeric(df["equity_capital"], errors="coerce").astype(float)
df["reserves"] = pd.to_numeric(df["reserves"], errors="coerce").astype(float)
df["total_assets"] = pd.to_numeric(df["total_assets"], errors="coerce").astype(float)

df["sales"] = pd.to_numeric(df["sales"], errors="coerce").astype(float)
df["net_profit"] = pd.to_numeric(df["net_profit"], errors="coerce").astype(float)

# Detect and normalize unit mismatch between profit and balance sheet values.
# This uses company-specific scaling factors so asset turnover lands in the
# expected range for each issuer before computing DuPont metrics.
scaling_map = _detect_unit_scaling(df)
print("\nApplied unit scaling factors:")
for company_id, (sales_factor, assets_factor) in sorted(scaling_map.items()):
    if sales_factor != 1.0 or assets_factor != 1.0:
        print(f"  {company_id}: sales_factor={sales_factor}, assets_factor={assets_factor}")

print("\nBefore scaling sample")
pre_debug = df.copy()
pre_debug["asset_turnover"] = pre_debug["sales"] / pre_debug["total_assets"]
print(
    pre_debug[
        ["company_id", "year", "sales", "total_assets", "asset_turnover"]
    ]
    .sort_values(["company_id", "year"])
    .head(20)
    .to_string(index=False)
)

df = _apply_unit_normalization(df, scaling_map)
print("\nAfter scaling sample")
after_debug = df.copy()
after_debug["asset_turnover"] = after_debug["sales"] / after_debug["total_assets"]
print(
    after_debug[
        ["company_id", "year", "sales", "total_assets", "asset_turnover"]
    ]
    .sort_values(["company_id", "year"])
    .head(20)
    .to_string(index=False)
)

# --------------------------------------------------
# Remove TTM Rows
# --------------------------------------------------

df = df[df["year"] != "TTM"].copy()

# --------------------------------------------------
# Extract Year Number
# --------------------------------------------------

df["year_num"] = pd.to_numeric(
    df["year"].str.extract(r"(\d{4})")[0],
    errors="coerce",
)

df = df.dropna(subset=["year_num"])

df["year_num"] = df["year_num"].astype(int)

# --------------------------------------------------
# Keep Latest Financial Record
# --------------------------------------------------

latest = (
    df.sort_values("year_num")
      .drop_duplicates(
          subset="company_id",
          keep="last",
      )
)

# --------------------------------------------------
# Merge Company Name
# --------------------------------------------------

latest = latest.merge(
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

# --------------------------------------------------
# Merge Sector
# --------------------------------------------------

latest = latest.merge(
    sectors[
        [
            "company_id",
            "broad_sector",
        ]
    ],
    on="company_id",
    how="left",
)

print("\nLatest Companies :", latest["company_id"].nunique())
# --------------------------------------------------
# Calculate DuPont Metrics
# --------------------------------------------------

# Profit Margin
latest["profit_margin"] = (
    latest["net_profit"] / latest["sales"]
)

# Asset Turnover
latest["asset_turnover"] = (
    latest["sales"] / latest["total_assets"]
)

# Shareholders' Equity
latest["equity"] = (
    latest["equity_capital"] +
    latest["reserves"]
)

# Keep only valid companies
latest = latest[
    latest["company_id"].isin(companies["id"])
]

# Remove invalid equity
latest = latest[
    latest["equity"] > 0
]
# Equity Multiplier
latest["equity_multiplier"] = (
    latest["total_assets"] / latest["equity"]
)


latest["roe"] = (
    latest["profit_margin"] *
    latest["asset_turnover"] *
    latest["equity_multiplier"]
) * 100


print(
    latest[
        [
            "company_id",
            "equity_capital",
            "reserves",
            "equity",
            "roe"
        ]
    ].sort_values(
        "roe",
        ascending=False
    ).head(10)
)

print(
    latest[
        latest["company_id"].isin(["BEL", "HAL", "INDIGO"])
    ][[
        "company_id",
        "total_assets",
        "borrowings",
        "equity",
        "net_profit"
    ]]
)

# Round values
latest["profit_margin"] = latest["profit_margin"].round(4)
latest["asset_turnover"] = latest["asset_turnover"].round(4)
latest["equity_multiplier"] = latest["equity_multiplier"].round(2)
latest["roe"] = latest["roe"].round(2)

print("\nDebug values for target companies:")
print(
    latest[
        latest["company_id"].isin(["BEL", "HAL", "LT", "TCS", "INDIGO"])
    ][[
        "company_id",
        "sales",
        "net_profit",
        "total_assets",
        "equity",
        "profit_margin",
        "asset_turnover",
        "equity_multiplier",
        "roe",
    ]]
    .sort_values("company_id")
    .to_string(index=False)
)

print("\nDebug values for key companies:")
print(
    latest[
        latest["company_id"].isin(["BEL", "HAL", "LT", "TCS", "INDIGO"])
    ][[
        "company_id",
        "sales",
        "net_profit",
        "total_assets",
        "equity",
        "profit_margin",
        "asset_turnover",
        "equity_multiplier",
        "roe",
    ]]
    .sort_values("company_id")
    .to_string(index=False)
)

print("\nDuPont Metrics Calculated")
print(
    latest[
        [
            "company_id",
            "profit_margin",
            "asset_turnover",
            "equity_multiplier",
            "roe",
        ]
    ].head()
)
# --------------------------------------------------
# ROE Label
# --------------------------------------------------

def roe_label(x):

    if pd.isna(x):
        return "Unknown"

    if x > 20:
        return "Excellent"

    elif x >= 15:
        return "Strong"

    elif x >= 10:
        return "Average"

    else:
        return "Weak"


latest["roe_label"] = latest["roe"].apply(
    roe_label
)

# --------------------------------------------------
# Leverage Label
# --------------------------------------------------

def leverage_label(x):

    if pd.isna(x):
        return "Unknown"

    if x < 1.5:
        return "Low"

    elif x <= 2.5:
        return "Moderate"

    else:
        return "High"


latest["leverage_label"] = latest[
    "equity_multiplier"
].apply(
    leverage_label
)

# --------------------------------------------------
# Weak ROE Flag
# --------------------------------------------------

latest["weak_roe_flag"] = latest["roe"] < 10

# --------------------------------------------------
# Final Report
# --------------------------------------------------

report = latest[
    [
        "company_id",
        "company_name",
        "broad_sector",
        "profit_margin",
        "asset_turnover",
        "equity_multiplier",
        "roe",
        "roe_label",
        "leverage_label",
    ]
]

print("\nROE Summary")
print(
    report[
        [
            "company_id",
            "roe",
            "roe_label",
            "leverage_label",
        ]
    ].head()
)
# --------------------------------------------------
# Export Reports
# --------------------------------------------------

report.to_excel(
    OUTPUT / "dupont_analysis.xlsx",
    index=False,
)

weak_roe = report[
    report["roe_label"] == "Weak"
]

weak_roe.to_csv(
    OUTPUT / "weak_roe_companies.csv",
    index=False,
)

# --------------------------------------------------
# Summary
# --------------------------------------------------

print("\nFiles Created")

print(
    OUTPUT / "dupont_analysis.xlsx"
)

print(
    OUTPUT / "weak_roe_companies.csv"
)

print("\nCompanies :", len(report))

print(
    "Weak ROE Companies :",
    len(weak_roe),
)

print(
    "\nLatest Companies :",
    report["company_id"].nunique(),
)

print("\nTop 10 ROE Companies")

print(
    report.sort_values(
        "roe",
        ascending=False,
    )[
        [
            "company_id",
            "roe",
            "roe_label",
        ]
    ].head(10)
)

print("\n" + "=" * 70)
print("DAY 32 COMPLETED")
print("=" * 70)
print(
    latest.sort_values(
        "roe",
        ascending=False
    )[
        [
            "company_id",
            "sales",
            "net_profit",
            "total_assets",
           "equity_capital",
            "reserves",
            "equity",
            "profit_margin",
            "asset_turnover",
            "equity_multiplier",
            "roe",
        ]
    ].head(10)
)
print(
    balance[
        balance["company_id"] == "BEL"
    ].T
)
print(
    balance[
        balance["company_id"] == "HAL"
    ].T
)
print(
    balance[
        balance["company_id"] == "LT"
    ].T
)

conn.close()
