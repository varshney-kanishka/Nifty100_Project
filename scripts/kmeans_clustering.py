
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans


# ============================================================
# CONFIGURATION
# ============================================================

DB_PATH = Path("data/database/nifty100.db")
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "company_clusters.csv"
PROFILE_FILE = OUTPUT_DIR / "cluster_profiles.csv"

LATEST_YEAR = "2024"
N_CLUSTERS = 5


# ============================================================
# LOAD DATA
# ============================================================

print("=" * 70)
print("NIFTY100 COMPANY KMEANS CLUSTERING")
print("=" * 70)

print(f"\nDatabase: {DB_PATH}")
print(f"Clustering year: {LATEST_YEAR}")
print(f"Number of clusters: {N_CLUSTERS}")

if not DB_PATH.exists():
    raise FileNotFoundError(f"Database not found: {DB_PATH}")


conn = sqlite3.connect(DB_PATH)

companies = pd.read_sql_query(
    """
    SELECT
        id AS company_id,
        company_name
    FROM companies
    """,
    conn,
)

ratios = pd.read_sql_query(
    """
    SELECT
        company_id,
        year,
        net_profit_margin_pct,
        operating_profit_margin_pct,
        return_on_equity_pct,
        return_on_capital_employed_pct,
        debt_to_equity,
        interest_coverage,
        asset_turnover,
        free_cash_flow_cr,
        capex_cr,
        cash_from_operations_cr
    FROM financial_ratios
    WHERE year = ?
    """,
    conn,
    params=(LATEST_YEAR,),
)

market_cap = pd.read_sql_query(
    """
    SELECT
        company_id,
        year,
        market_cap_crore,
        pe_ratio,
        pb_ratio,
        ev_ebitda,
        dividend_yield_pct
    FROM market_cap
    WHERE year = ?
    """,
    conn,
    params=(LATEST_YEAR,),
)

# IMPORTANT:
# sectors table uses broad_sector, not sector.
sectors = pd.read_sql_query(
    """
    SELECT
        company_id,
        broad_sector AS sector
    FROM sectors
    """,
    conn,
)

conn.close()


# ============================================================
# MERGE
# ============================================================

df = companies.merge(
    sectors,
    on="company_id",
    how="left",
)

df = df.merge(
    ratios.drop(columns=["year"]),
    on="company_id",
    how="left",
)

df = df.merge(
    market_cap.drop(columns=["year"]),
    on="company_id",
    how="left",
)


print("\nData loaded:")
print(f"Companies:      {len(companies)}")
print(f"2024 ratios:    {len(ratios)}")
print(f"2024 marketcap: {len(market_cap)}")
print(f"Merged rows:    {len(df)}")


# ============================================================
# FEATURE SELECTION
# ============================================================

FEATURES = [
    "net_profit_margin_pct",
    "operating_profit_margin_pct",
    "debt_to_equity",
    "interest_coverage",
    "free_cash_flow_cr",
    "capex_cr",
    "cash_from_operations_cr",
    "market_cap_crore",
    "pe_ratio",
    "pb_ratio",
    "ev_ebitda",
    "dividend_yield_pct",
]


print("\nSelected features:")
for feature in FEATURES:
    print(f"  - {feature}")


# ============================================================
# MISSING VALUES
# ============================================================

print("\nMissing values before cleaning:")

missing = df[FEATURES].isna().sum()
print(missing[missing > 0])


# Median imputation
for feature in FEATURES:
    median_value = df[feature].median()

    if pd.isna(median_value):
        raise ValueError(
            f"Cannot impute {feature}: median is NaN."
        )

    df[feature] = df[feature].fillna(median_value)


print("\nMissing values after imputation:")
print(df[FEATURES].isna().sum().sum())


# ============================================================
# CHECK COMPANY COUNT
# ============================================================

if len(df) != 92:
    raise ValueError(
        f"Expected 92 companies but found {len(df)}."
    )

if df["company_id"].nunique() != 92:
    raise ValueError(
        "Company IDs are not unique after merging."
    )



# ============================================================
# ROBUST OUTLIER HANDLING
# ============================================================

print("\nApplying robust outlier handling...")

X = df[FEATURES].copy()


# ------------------------------------------------------------
# IMPORTANT:
# The source database contains extreme ratio values.
# We do NOT modify the database.
#
# We only cap extreme observations for clustering.
# ------------------------------------------------------------

def winsorize_series(series, lower=0.05, upper=0.95):
    """
    Cap extreme observations at the 5th and 95th percentiles.
    No companies are removed.
    """
    low = series.quantile(lower)
    high = series.quantile(upper)

    return series.clip(
        lower=low,
        upper=high,
    )


print("\nWinsorizing features at 5th/95th percentiles...")

for feature in FEATURES:
    X[feature] = winsorize_series(
        X[feature],
        lower=0.05,
        upper=0.95,
    )


# ============================================================
# SIGNED LOG TRANSFORMATION
# ============================================================

LOG_FEATURES = [
    "free_cash_flow_cr",
    "capex_cr",
    "cash_from_operations_cr",
    "market_cap_crore",
]


def signed_log1p(series):
    """
    Signed logarithmic transformation.

    Positive values:
        log(1 + x)

    Negative values:
        -log(1 + abs(x))

    This preserves the direction of cash-flow values.
    """
    return np.sign(series) * np.log1p(np.abs(series))


print("\nApplying signed log transformation to:")

for feature in LOG_FEATURES:
    print(f"  - {feature}")
    X[feature] = signed_log1p(X[feature])


# ============================================================
# ROBUST SCALING
# ============================================================

from sklearn.preprocessing import RobustScaler

print("\nApplying RobustScaler...")

scaler = RobustScaler()

X_scaled = scaler.fit_transform(X)


# ============================================================
# KMEANS
# ============================================================

print("\nRunning KMeans...")

kmeans = KMeans(
    n_clusters=N_CLUSTERS,
    random_state=42,
    n_init=50,
)

df["cluster"] = kmeans.fit_predict(X_scaled)


# ============================================================
# CLUSTER SUMMARY
# ============================================================

cluster_sizes = (
    df["cluster"]
    .value_counts()
    .sort_index()
)

print("\nCluster sizes:")

for cluster, size in cluster_sizes.items():
    print(f"  Cluster {cluster}: {size} companies")


# ============================================================
# BASIC BALANCE CHECK
# ============================================================

largest_cluster = cluster_sizes.max()
smallest_cluster = cluster_sizes.min()

print("\nCluster balance check:")
print(f"  Smallest cluster: {smallest_cluster}")
print(f"  Largest cluster:  {largest_cluster}")

if largest_cluster >= 70:
    print(
        "  WARNING: A cluster still contains 70+ companies."
    )
else:
    print(
        "  Cluster distribution is substantially improved."
    )


# ============================================================
# CLUSTER PROFILES
# ============================================================

profile = (
    df.groupby("cluster")[FEATURES]
    .mean()
    .round(2)
)

print("\nCluster profiles:")
print(profile.to_string())


# ============================================================
# CLUSTER MEDIANS
# ============================================================

median_profile = (
    df.groupby("cluster")[FEATURES]
    .median()
    .round(2)
)

print("\nCluster median profiles:")
print(median_profile.to_string())


# ============================================================
# ARCHETYPE NAMES
# ============================================================

# Keep neutral names until the new cluster profiles
# have been reviewed.

df["archetype"] = df["cluster"].apply(
    lambda x: f"Archetype {x + 1}"
)


# ============================================================
# SAVE COMPANY ASSIGNMENTS
# ============================================================

OUTPUT_COLUMNS = [
    "company_id",
    "company_name",
    "sector",
    "cluster",
    "archetype",
] + FEATURES

output = df[OUTPUT_COLUMNS].sort_values(
    ["cluster", "company_name"]
)

output.to_csv(
    OUTPUT_FILE,
    index=False,
)


# ============================================================
# SAVE CLUSTER PROFILE
# ============================================================

profile.to_csv(PROFILE_FILE)


# ============================================================
# FINAL OUTPUT
# ============================================================

print("\n" + "=" * 70)
print("CLUSTERING COMPLETE")
print("=" * 70)

print("\nCompany assignments:")
print(f"  {OUTPUT_FILE}")

print("\nCluster profiles:")
print(f"  {PROFILE_FILE}")

print("\nFirst 10 assignments:")

print(
    output[
        [
            "company_id",
            "company_name",
            "sector",
            "cluster",
        ]
    ]
    .head(10)
    .to_string(index=False)
)
