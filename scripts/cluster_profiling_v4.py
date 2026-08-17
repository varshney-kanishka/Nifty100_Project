import pandas as pd
from pathlib import Path


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]

INPUT_FILE = BASE_DIR / "output" / "company_clusters_v4.csv"

PROFILE_FILE = BASE_DIR / "output" / "cluster_profiles_v4.csv"
ARCHETYPE_FILE = BASE_DIR / "output" / "cluster_archetypes_v4.csv"


EXPECTED_COMPANIES = 92
EXPECTED_CLUSTERS = 5


# ============================================================
# FEATURES
# ============================================================

FEATURES = [
    "net_profit_margin_pct",
    "operating_profit_margin_pct",
    "return_on_equity_pct",
    "return_on_capital_employed_pct",
    "debt_to_equity",
    "interest_coverage",
    "cfo_pat_ratio",
    "fcf_conversion_pct",
    "capex_intensity_pct",
    "pe_ratio",
    "pb_ratio",
    "ev_ebitda",
    "dividend_yield_pct",
]


# ============================================================
# START
# ============================================================

print("=" * 70)
print("NIFTY100 CLUSTER PROFILING V4")
print("=" * 70)

print(f"\nInput: {INPUT_FILE}")


# ============================================================
# LOAD DATA
# ============================================================

if not INPUT_FILE.exists():
    raise FileNotFoundError(
        f"Input file not found: {INPUT_FILE}"
    )


df = pd.read_csv(INPUT_FILE)


print(f"\nCompanies loaded: {len(df)}")


# ============================================================
# VALIDATION
# ============================================================

required_columns = [
    "company_id",
    "company_name",
    "cluster",
    "sector",
] + FEATURES


missing_columns = [
    column
    for column in required_columns
    if column not in df.columns
]


if missing_columns:
    raise ValueError(
        f"Missing required columns: {missing_columns}"
    )


if len(df) != EXPECTED_COMPANIES:
    raise ValueError(
        f"Expected {EXPECTED_COMPANIES} companies, "
        f"found {len(df)}"
    )


if df["company_id"].nunique() != EXPECTED_COMPANIES:
    raise ValueError(
        "Company IDs are not unique."
    )


cluster_count = df["cluster"].nunique()


if cluster_count != EXPECTED_CLUSTERS:
    raise ValueError(
        f"Expected {EXPECTED_CLUSTERS} clusters, "
        f"found {cluster_count}"
    )


print(f"Clusters found: {cluster_count}")


# ============================================================
# NUMERIC CONVERSION
# ============================================================

for feature in FEATURES:

    df[feature] = pd.to_numeric(
        df[feature],
        errors="coerce",
    )


# ============================================================
# CLUSTER SIZES
# ============================================================

cluster_sizes = (
    df["cluster"]
    .value_counts()
    .sort_index()
)


print("\n" + "=" * 70)
print("CLUSTER SIZES")
print("=" * 70)


for cluster, count in cluster_sizes.items():

    print(
        f"Cluster {cluster}: "
        f"{count} companies"
    )


# ============================================================
# MEDIAN PROFILE
# ============================================================

median_profile = (
    df
    .groupby("cluster")[FEATURES]
    .median()
    .round(2)
)


# ============================================================
# MEAN PROFILE
# ============================================================

mean_profile = (
    df
    .groupby("cluster")[FEATURES]
    .mean()
    .round(2)
)


# ============================================================
# SAVE MEDIAN PROFILE
# ============================================================

median_output = median_profile.reset_index()

median_output.to_csv(
    PROFILE_FILE,
    index=False,
)


# ============================================================
# DISPLAY MEDIAN PROFILES
# ============================================================

print("\n" + "=" * 70)
print("CLUSTER MEDIAN PROFILES")
print("=" * 70)

print(
    median_profile.to_string()
)


# ============================================================
# SECTOR DISTRIBUTION
# ============================================================

print("\n" + "=" * 70)
print("SECTOR DISTRIBUTION BY CLUSTER")
print("=" * 70)


sector_distribution = pd.crosstab(
    df["cluster"],
    df["sector"],
)


print(
    sector_distribution.to_string()
)


# ============================================================
# SECTOR PERCENTAGES
# ============================================================

print("\n" + "=" * 70)
print("SECTOR PERCENTAGE WITHIN EACH CLUSTER")
print("=" * 70)


sector_percentage = (
    sector_distribution
    .div(
        sector_distribution.sum(axis=1),
        axis=0,
    )
    .mul(100)
    .round(1)
)


print(
    sector_percentage.to_string()
)


# ============================================================
# DATA-DRIVEN ARCHETYPE LOGIC
# ============================================================

def describe_cluster(row):

    descriptions = []

    # --------------------------------------------------------
    # Profitability
    # --------------------------------------------------------

    if row["net_profit_margin_pct"] >= 20:
        descriptions.append("High profitability")

    elif row["net_profit_margin_pct"] < 10:
        descriptions.append("Low profitability")

    else:
        descriptions.append("Moderate profitability")


    # --------------------------------------------------------
    # Leverage
    # --------------------------------------------------------

    if row["debt_to_equity"] >= 2:
        descriptions.append("High leverage")

    elif row["debt_to_equity"] <= 0.5:
        descriptions.append("Low leverage")

    else:
        descriptions.append("Moderate leverage")


    # --------------------------------------------------------
    # Cash flow
    # --------------------------------------------------------

    if row["cfo_pat_ratio"] >= 1.2:
        descriptions.append("Strong cash generation")

    elif row["cfo_pat_ratio"] < 0:
        descriptions.append("Negative operating cash flow")

    elif row["cfo_pat_ratio"] < 0.5:
        descriptions.append("Weak cash generation")

    else:
        descriptions.append("Moderate cash generation")


    # --------------------------------------------------------
    # FCF
    # --------------------------------------------------------

    if row["fcf_conversion_pct"] >= 40:
        descriptions.append("Strong FCF conversion")

    elif row["fcf_conversion_pct"] < 0:
        descriptions.append("Negative FCF conversion")


    # --------------------------------------------------------
    # CapEx
    # --------------------------------------------------------

    if row["capex_intensity_pct"] >= 20:
        descriptions.append("Capital intensive")

    elif row["capex_intensity_pct"] < 5:
        descriptions.append("Low capital intensity")


    return " | ".join(descriptions)


# ============================================================
# ARCHETYPE OUTPUT
# ============================================================

archetype_rows = []


for cluster in sorted(df["cluster"].unique()):

    row = median_profile.loc[cluster]

    description = describe_cluster(row)

    company_count = int(
        (df["cluster"] == cluster).sum()
    )

    dominant_sector = (
        df.loc[
            df["cluster"] == cluster,
            "sector",
        ]
        .value_counts()
        .idxmax()
    )

    archetype_rows.append(
        {
            "cluster": cluster,
            "company_count": company_count,
            "dominant_sector": dominant_sector,
            "profile_description": description,
        }
    )


archetypes = pd.DataFrame(
    archetype_rows
)


# ============================================================
# SAVE ARCHETYPES
# ============================================================

archetypes.to_csv(
    ARCHETYPE_FILE,
    index=False,
)


# ============================================================
# DISPLAY ARCHETYPES
# ============================================================

print("\n" + "=" * 70)
print("DATA-DRIVEN CLUSTER ARCHETYPES")
print("=" * 70)


for _, row in archetypes.iterrows():

    print(
        f"\nCluster {row['cluster']} "
        f"({row['company_count']} companies)"
    )

    print(
        f"Dominant sector: "
        f"{row['dominant_sector']}"
    )

    print(
        f"Profile: "
        f"{row['profile_description']}"
    )


# ============================================================
# COMPANY LIST
# ============================================================

print("\n" + "=" * 70)
print("COMPANIES BY CLUSTER")
print("=" * 70)


for cluster in sorted(df["cluster"].unique()):

    cluster_df = (
        df[df["cluster"] == cluster]
        .sort_values("company_name")
    )

    print(
        f"\nCluster {cluster} "
        f"({len(cluster_df)} companies):"
    )

    print(
        cluster_df[
            [
                "company_id",
                "company_name",
                "sector",
            ]
        ]
        .to_string(index=False)
    )


# ============================================================
# FINAL
# ============================================================

print("\n" + "=" * 70)
print("CLUSTER PROFILING V4 COMPLETE")
print("=" * 70)

print("\nOutputs:")

print(
    f"- {PROFILE_FILE.relative_to(BASE_DIR)}"
)

print(
    f"- {ARCHETYPE_FILE.relative_to(BASE_DIR)}"
)
