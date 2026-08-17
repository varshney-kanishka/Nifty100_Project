import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "data" / "database" / "nifty100.db"
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

YEAR = "2024"
EXPECTED_COMPANIES = 92

COMPANY_OUTPUT_FILE = OUTPUT_DIR / "cashflow_intelligence_v4.csv"
CFO_QUALITY_SUMMARY_FILE = OUTPUT_DIR / "cfo_quality_summary_v4.csv"
CAPEX_SUMMARY_FILE = OUTPUT_DIR / "capex_intensity_summary_v4.csv"
SECTOR_SUMMARY_FILE = OUTPUT_DIR / "sector_cashflow_summary_v4.csv"
RISK_COMPANIES_FILE = OUTPUT_DIR / "cashflow_risk_companies_v4.csv"


# ============================================================
# HELPER FUNCTIONS
# ============================================================


def safe_divide(numerator, denominator):
    """Return NaN where denominator is zero, missing, or invalid."""
    numerator = pd.to_numeric(numerator, errors="coerce")
    denominator = pd.to_numeric(denominator, errors="coerce")
    valid = pd.notna(numerator) & pd.notna(denominator) & (denominator != 0)
    result = np.full(len(numerator), np.nan, dtype=float)
    if isinstance(numerator, pd.Series) and isinstance(denominator, pd.Series):
        result = np.where(valid, numerator.to_numpy(dtype=float) / denominator.to_numpy(dtype=float), np.nan)
    return pd.Series(result, index=numerator.index if hasattr(numerator, "index") else None)


def ensure_numeric(frame, columns):
    for column in columns:
        if column in frame.columns:
            frame.loc[:, column] = pd.to_numeric(frame[column], errors="coerce")
    frame.replace([np.inf, -np.inf], np.nan, inplace=True)
    return frame


def classify_cfo_quality(value):
    """Classify based on CFO/PAT."""
    if pd.isna(value):
        return np.nan
    if value < 0:
        return "Negative"
    if value < 0.5:
        return "Poor"
    if value < 0.8:
        return "Weak"
    if value < 1.2:
        return "Healthy"
    return "Strong"


def classify_capex_intensity(value):
    """Classify based on CapEx intensity percentage."""
    if pd.isna(value):
        return np.nan
    if value < 5:
        return "Low"
    if value < 10:
        return "Moderate"
    if value < 20:
        return "High"
    return "Very High"


def classify_cash_profit_alignment(value):
    """Three-band cash-profit alignment flag based on CFO/PAT."""
    if pd.isna(value):
        return np.nan
    if value >= 1.2:
        return "Strong"
    if value >= 0.8:
        return "Moderate"
    return "Weak"


def classify_fcf_status(value):
    """Positive or negative FCF flag."""
    if pd.isna(value):
        return np.nan
    return "Positive" if value >= 0 else "Negative"


def compute_cash_flow_score(cfo_pat_ratio, fcf_conversion_pct, fcf_status, capex_intensity_pct):
    """
    Transparent 0-100 score built from weighted sub-scores.

    Components:
    - CFO quality: 40%
      0 for Negative CFO/PAT, 30 for Poor, 60 for Weak, 80 for Healthy, 100 for Strong
    - FCF conversion: 30%
      Normalized from -100 to +100 using a clipped range and a linear transform
    - FCF status: 15%
      100 if positive, 0 if negative
    - CapEx efficiency: 15%
      100 for Low capex, 75 for Moderate, 40 for High, 20 for Very High

    This keeps the scoring explainable and prevents extreme values from dominating.
    """
    # CFO quality component
    cfo_pat_value = pd.to_numeric(cfo_pat_ratio, errors="coerce")
    if pd.isna(cfo_pat_value):
        cfo_score = 0.0
    elif cfo_pat_value < 0:
        cfo_score = 0.0
    elif cfo_pat_value < 0.5:
        cfo_score = 30.0
    elif cfo_pat_value < 0.8:
        cfo_score = 60.0
    elif cfo_pat_value < 1.2:
        cfo_score = 80.0
    else:
        cfo_score = 100.0

    # FCF conversion component (clipped to avoid extremes dominating)
    fcf_conv_value = pd.to_numeric(fcf_conversion_pct, errors="coerce")
    if pd.isna(fcf_conv_value):
        fcf_score = 0.0
    else:
        clipped = float(np.clip(fcf_conv_value, -100, 100))
        fcf_score = ((clipped + 100) / 200.0) * 100.0

    # FCF status component
    fcf_status_value = fcf_status
    if pd.isna(fcf_status_value):
        status_score = 0.0
    else:
        status_score = 100.0 if str(fcf_status_value) == "Positive" else 0.0

    # CapEx efficiency component
    capex_value = pd.to_numeric(capex_intensity_pct, errors="coerce")
    if pd.isna(capex_value):
        capex_score = 0.0
    elif capex_value < 5:
        capex_score = 100.0
    elif capex_value < 10:
        capex_score = 75.0
    elif capex_value < 20:
        capex_score = 40.0
    else:
        capex_score = 20.0

    total_score = (
        0.40 * cfo_score +
        0.30 * fcf_score +
        0.15 * status_score +
        0.15 * capex_score
    )
    return round(float(total_score), 2)


def validate_table_and_columns(conn, table_name, required_columns):
    table_list = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table'", conn)
    if table_name not in table_list["name"].tolist():
        raise ValueError(f"Required table not found: {table_name}")
    columns = pd.read_sql_query(f"PRAGMA table_info({table_name})", conn)
    actual = set(columns["name"].tolist())
    missing = [col for col in required_columns if col not in actual]
    if missing:
        raise ValueError(f"Missing required columns in {table_name}: {missing}")


def safe_round_percent(series):
    if series.empty:
        return 0.0
    return round(float(series.mean()), 2)


# ============================================================
# MAIN
# ============================================================

print("=" * 70)
print("NIFTY100 CASH FLOW INTELLIGENCE V4")
print("=" * 70)
print(f"\nDatabase: {DB_PATH}")
print(f"Analysis year: {YEAR}")

if not DB_PATH.exists():
    raise FileNotFoundError(f"Database not found: {DB_PATH}")

conn = sqlite3.connect(DB_PATH)

try:
    required_tables = ["companies", "sectors", "profitandloss", "cashflow"]
    for table_name in required_tables:
        validate_table_and_columns(conn, table_name, [])

    companies = pd.read_sql_query(
        """
        SELECT
            c.id AS company_id,
            c.company_name
        FROM companies c
        """,
        conn,
    )

    sectors = pd.read_sql_query(
        """
        SELECT
            company_id,
            broad_sector AS sector,
            sub_sector
        FROM sectors
        """,
        conn,
    )

    profit = pd.read_sql_query(
        """
        SELECT
            company_id,
            year,
            sales,
            net_profit,
            operating_profit
        FROM profitandloss
        WHERE year = ?
        """,
        conn,
        params=(YEAR,),
    )

    cashflow = pd.read_sql_query(
        """
        SELECT
            company_id,
            year,
            operating_activity,
            investing_activity
        FROM cashflow
        WHERE year = ?
        """,
        conn,
        params=(YEAR,),
    )
finally:
    conn.close()

# Normalize IDs
for frame in [companies, sectors, profit, cashflow]:
    if "company_id" in frame.columns:
        frame.loc[:, "company_id"] = frame["company_id"].astype(str).str.strip()

# Remove duplicate rows if any
companies = companies.drop_duplicates(subset=["company_id"], keep="last").copy()
sectors = sectors.drop_duplicates(subset=["company_id"], keep="last").copy()
profit = profit.drop_duplicates(subset=["company_id"], keep="last").copy()
cashflow = cashflow.drop_duplicates(subset=["company_id"], keep="last").copy()

print(f"\nCompanies loaded: {len(companies)}")
print(f"Cash-flow rows: {len(cashflow)}")

# Merge core data
company_df = companies.merge(sectors, on="company_id", how="left")
company_df = company_df.merge(profit, on="company_id", how="left")
company_df = company_df.merge(cashflow, on="company_id", how="left")

if "year" not in company_df.columns:
    company_df.loc[:, "year"] = YEAR

print(f"Merged rows: {len(company_df)}")

# Validate company universe
if len(company_df) != EXPECTED_COMPANIES:
    raise ValueError(f"Expected {EXPECTED_COMPANIES} companies but found {len(company_df)}")
if company_df["company_id"].nunique() != EXPECTED_COMPANIES:
    raise ValueError("Duplicate or missing company IDs found in merged data")
if company_df["company_id"].isna().any():
    raise ValueError("Missing company_id in merged data")

# Required columns for analytics
required_columns = [
    "company_id",
    "company_name",
    "sector",
    "sub_sector",
    "year",
    "sales",
    "net_profit",
    "operating_profit",
    "operating_activity",
    "investing_activity",
]
missing_cols = [col for col in required_columns if col not in company_df.columns]
if missing_cols:
    raise ValueError(f"Missing required columns before computing metrics: {missing_cols}")

# Convert numeric values and replace infs
company_df = ensure_numeric(
    company_df,
    [
        "sales",
        "net_profit",
        "operating_profit",
        "operating_activity",
        "investing_activity",
    ],
)

# Safe arithmetic metrics
company_df.loc[:, "cfo_pat_ratio"] = safe_divide(company_df["operating_activity"], company_df["net_profit"])
company_df.loc[:, "fcf"] = company_df["operating_activity"] + company_df["investing_activity"]
company_df.loc[:, "fcf_conversion_pct"] = safe_divide(company_df["fcf"], company_df["operating_profit"]) * 100.0
company_df.loc[:, "capex_intensity_pct"] = safe_divide(np.abs(company_df["investing_activity"]), company_df["sales"]) * 100.0

company_df = company_df.replace([np.inf, -np.inf], np.nan)

# Company-level classifications
company_df.loc[:, "cfo_quality"] = company_df["cfo_pat_ratio"].apply(classify_cfo_quality)
company_df.loc[:, "capex_intensity_class"] = company_df["capex_intensity_pct"].apply(classify_capex_intensity)
company_df.loc[:, "cash_profit_alignment"] = company_df["cfo_pat_ratio"].apply(classify_cash_profit_alignment)
company_df.loc[:, "fcf_status"] = company_df["fcf"].apply(classify_fcf_status)

company_df.loc[:, "cash_flow_risk"] = company_df.apply(
    lambda row: (
        str(row["cfo_quality"]) in {"Negative", "Poor"}
        or str(row["fcf_status"]) == "Negative"
        or str(row["capex_intensity_class"]) == "Very High"
        or pd.notna(row["cfo_pat_ratio"]) and row["cfo_pat_ratio"] < 0.5
    ),
    axis=1,
)

# Cash flow score using weighted components
company_df.loc[:, "cash_flow_score"] = company_df.apply(
    lambda row: compute_cash_flow_score(
        row["cfo_pat_ratio"],
        row["fcf_conversion_pct"],
        row["fcf_status"],
        row["capex_intensity_pct"],
    ),
    axis=1,
)

# Clean final output
company_df = company_df.copy()
company_df.loc[:, "year"] = YEAR
company_df.loc[:, "company_id"] = company_df["company_id"].astype(str).str.strip()
company_df.loc[:, "company_name"] = company_df["company_name"].astype(str).str.strip()
company_df.loc[:, "sector"] = company_df["sector"].fillna("Unknown")
company_df.loc[:, "sub_sector"] = company_df["sub_sector"].fillna("Unknown")
company_df.loc[:, "cash_flow_risk"] = company_df["cash_flow_risk"].astype(bool)

# Final column order
output_columns = [
    "company_id",
    "company_name",
    "sector",
    "sub_sector",
    "year",
    "sales",
    "net_profit",
    "operating_profit",
    "operating_activity",
    "investing_activity",
    "cfo_pat_ratio",
    "fcf",
    "fcf_conversion_pct",
    "capex_intensity_pct",
    "cfo_quality",
    "capex_intensity_class",
    "cash_profit_alignment",
    "fcf_status",
    "cash_flow_risk",
    "cash_flow_score",
]

company_output = company_df[output_columns].copy()
company_output = company_output.sort_values(["cash_flow_score", "company_name"], ascending=[False, True]).reset_index(drop=True)

# Required validation checks
assert company_output["company_id"].notna().all(), "Missing company IDs in output"
assert company_output["company_id"].nunique() == EXPECTED_COMPANIES, "Duplicate company IDs in output"
assert len(company_output) == EXPECTED_COMPANIES, f"Expected {EXPECTED_COMPANIES} rows but got {len(company_output)}"
assert not np.isinf(company_output.select_dtypes(include=[np.number]).to_numpy()).any(), "Infinite numeric values found"

# CFO class counts
cfo_quality_counts = company_output["cfo_quality"].value_counts(dropna=False).sort_index()
capex_class_counts = company_output["capex_intensity_class"].value_counts(dropna=False).sort_index()
fcf_status_counts = company_output["fcf_status"].value_counts(dropna=False).sort_index()

# Output summary tables
cfo_summary = (
    company_output.groupby("cfo_quality", dropna=False)
    .agg(
        company_count=("company_id", "count"),
        average_cfo_pat_ratio=("cfo_pat_ratio", "mean"),
        median_cfo_pat_ratio=("cfo_pat_ratio", "median"),
        average_fcf_conversion_pct=("fcf_conversion_pct", "mean"),
        average_cash_flow_score=("cash_flow_score", "mean"),
    )
    .reset_index()
)

cfo_summary.loc[:, "percentage_of_companies"] = (
    cfo_summary["company_count"] / EXPECTED_COMPANIES * 100.0
).round(2)

# Capex summary
capex_summary = (
    company_output.groupby("capex_intensity_class", dropna=False)
    .agg(
        company_count=("company_id", "count"),
        average_capex_intensity_pct=("capex_intensity_pct", "mean"),
        median_capex_intensity_pct=("capex_intensity_pct", "median"),
        average_fcf_conversion_pct=("fcf_conversion_pct", "mean"),
    )
    .reset_index()
)
capex_summary.loc[:, "percentage_of_companies"] = (
    capex_summary["company_count"] / EXPECTED_COMPANIES * 100.0
).round(2)

# Sector summary
sector_summary = (
    company_output.groupby("sector", dropna=False)
    .agg(
        company_count=("company_id", "count"),
        average_cfo_pat_ratio=("cfo_pat_ratio", "mean"),
        median_cfo_pat_ratio=("cfo_pat_ratio", "median"),
        average_fcf_conversion_pct=("fcf_conversion_pct", "mean"),
        median_fcf_conversion_pct=("fcf_conversion_pct", "median"),
        average_capex_intensity_pct=("capex_intensity_pct", "mean"),
        average_cash_flow_score=("cash_flow_score", "mean"),
    )
    .reset_index()
)
sector_summary.loc[:, "negative_fcf_count"] = company_output.groupby("sector")["fcf"].apply(lambda s: (s < 0).sum()).values
sector_summary.loc[:, "negative_fcf_pct"] = (sector_summary["negative_fcf_count"] / sector_summary["company_count"] * 100.0).round(2)
sector_summary.loc[:, "strong_cfo_count"] = company_output.groupby("sector")["cfo_quality"].apply(lambda s: (s == "Strong").sum()).values
sector_summary.loc[:, "weak_or_worse_cfo_count"] = company_output.groupby("sector")["cfo_quality"].apply(lambda s: s.isin(["Weak", "Poor", "Negative"]).sum()).values

# Risk companies
risk_mask = (
    company_output["cfo_quality"].isin(["Negative", "Poor"]) |
    (company_output["fcf"] < 0) |
    (company_output["capex_intensity_class"] == "Very High")
)
risk_companies = company_output.loc[risk_mask, [
    "company_id",
    "company_name",
    "sector",
    "cfo_pat_ratio",
    "fcf",
    "fcf_conversion_pct",
    "capex_intensity_pct",
    "cfo_quality",
    "capex_intensity_class",
    "fcf_status",
    "cash_flow_risk",
    "cash_flow_score",
]].copy()
risk_companies = risk_companies.sort_values(["cash_flow_score", "company_name"], ascending=[False, True]).reset_index(drop=True)

# Write outputs
company_output.to_csv(COMPANY_OUTPUT_FILE, index=False)
cfo_summary.to_csv(CFO_QUALITY_SUMMARY_FILE, index=False)
capex_summary.to_csv(CAPEX_SUMMARY_FILE, index=False)
sector_summary.to_csv(SECTOR_SUMMARY_FILE, index=False)
risk_companies.to_csv(RISK_COMPANIES_FILE, index=False)

# Validate output files written
for path in [
    COMPANY_OUTPUT_FILE,
    CFO_QUALITY_SUMMARY_FILE,
    CAPEX_SUMMARY_FILE,
    SECTOR_SUMMARY_FILE,
    RISK_COMPANIES_FILE,
]:
    if not path.exists():
        raise FileNotFoundError(f"Output file not created: {path}")

# Validate classification totals
assert int(company_output["cfo_quality"].notna().sum()) == EXPECTED_COMPANIES, "CFO quality classification missing"
assert int(company_output["capex_intensity_class"].notna().sum()) == EXPECTED_COMPANIES, "CapEx classification missing"
assert int(company_output["fcf_status"].notna().sum()) == EXPECTED_COMPANIES, "FCF status missing"
assert int(company_output["model_count"] if "model_count" in company_output.columns else 0) == 0, "Unexpected extra validation artifact"

cfo_total = cfo_quality_counts.sum()
capex_total = capex_class_counts.sum()
fcf_total = fcf_status_counts.sum()
assert cfo_total == EXPECTED_COMPANIES, f"CFO quality totals must equal {EXPECTED_COMPANIES}, got {cfo_total}"
assert capex_total == EXPECTED_COMPANIES, f"CapEx totals must equal {EXPECTED_COMPANIES}, got {capex_total}"
assert fcf_total == EXPECTED_COMPANIES, f"FCF totals must equal {EXPECTED_COMPANIES}, got {fcf_total}"
assert company_output["sector"].notna().all(), "Missing sector information"
assert company_output["sector"].value_counts().sum() == EXPECTED_COMPANIES, "Sector totals do not sum to 92"

# Print concise validation report
print("\nCash Flow Metrics:")
print("- CFO/PAT calculated")
print("- FCF calculated")
print("- FCF conversion calculated")
print("- CapEx intensity calculated")

print("\nCFO Quality:")
for label in ["Strong", "Healthy", "Weak", "Poor", "Negative"]:
    count = int((company_output["cfo_quality"] == label).sum())
    print(f"{label}: {count}")

print("\nCapEx Intensity:")
for label in ["Low", "Moderate", "High", "Very High"]:
    count = int((company_output["capex_intensity_class"] == label).sum())
    print(f"{label}: {count}")

print("\nFCF Status:")
for label in ["Positive", "Negative"]:
    count = int((company_output["fcf_status"] == label).sum())
    print(f"{label}: {count}")

negative_fcf_count = int((company_output["fcf"] < 0).sum())
print(f"\nNegative FCF companies: {negative_fcf_count}")

high_risk_count = int(company_output["cash_flow_risk"].sum())
print(f"High-risk companies: {high_risk_count}")

print("\nValidation:")
print("✓ 92 unique companies")
print("✓ 92 output rows")
print("✓ No duplicate company IDs")
print("✓ No infinite values")
print("✓ Classification totals = 92")
print("✓ Output CSVs written successfully")

print("\nOutputs:")
for output_path in [
    COMPANY_OUTPUT_FILE,
    CFO_QUALITY_SUMMARY_FILE,
    CAPEX_SUMMARY_FILE,
    SECTOR_SUMMARY_FILE,
    RISK_COMPANIES_FILE,
]:
    print(f"- {output_path.relative_to(BASE_DIR)}")

print("\n" + "=" * 70)
print("CASH FLOW INTELLIGENCE V4 COMPLETE")
print("=" * 70)
