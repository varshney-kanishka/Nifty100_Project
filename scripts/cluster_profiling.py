import pandas as pd
from pathlib import Path


# ============================================================
# CONFIGURATION
# ============================================================

INPUT_FILE = Path("output/company_clusters.csv")
OUTPUT_FILE = Path("output/cluster_archetypes.csv")


# ============================================================
# LOAD DATA
# ============================================================

print("=" * 70)
print("NIFTY100 CLUSTER PROFILING")
print("=" * 70)

if not INPUT_FILE.exists():
    raise FileNotFoundError(f"Input file not found: {INPUT_FILE}")

df = pd.read_csv(INPUT_FILE)

print(f"\nCompanies loaded: {len(df)}")
print(f"Clusters found: {df['cluster'].nunique()}")


# ============================================================
# CLUSTER PROFILES
# ============================================================

FEATURES = [
    "net_profit_margin_pct",
    "operating_profit_margin_pct",
    "debt_to_equity",
    "interest_coverage",
    "free_cash_flow_cr",
    "cash_from_operations_cr",
    "market_cap_crore",
    "pe_ratio",
    "pb_ratio",
    "ev_ebitda",
    "dividend_yield_pct",
]


profiles = (
    df.groupby("cluster")[FEATURES]
    .median()
    .round(2)
)


# ============================================================
# DISPLAY PROFILES
# ============================================================

print("\n" + "=" * 70)
print("CLUSTER MEDIAN PROFILES")
print("=" * 70)

print(profiles.to_string())


# ============================================================
# SECTOR DISTRIBUTION
# ============================================================

print("\n" + "=" * 70)
print("SECTOR DISTRIBUTION BY CLUSTER")
print("=" * 70)

sector_distribution = pd.crosstab(
    df["cluster"],
    df["sector"]
)

print(sector_distribution.to_string())


# ============================================================
# COMPANY COUNTS
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
    print(f"Cluster {cluster}: {count} companies")


# ============================================================
# TOP COMPANIES BY MARKET CAP
# ============================================================

print("\n" + "=" * 70)
print("TOP COMPANIES BY MARKET CAP IN EACH CLUSTER")
print("=" * 70)

for cluster in sorted(df["cluster"].unique()):

    print(f"\nCluster {cluster}:")

    cluster_df = (
        df[df["cluster"] == cluster]
        .sort_values("market_cap_crore", ascending=False)
        .head(10)
    )

    print(
        cluster_df[
            [
                "company_id",
                "company_name",
                "sector",
                "market_cap_crore",
                "net_profit_margin_pct",
                "debt_to_equity",
                "interest_coverage",
            ]
        ].to_string(index=False)
    )


# ============================================================
# ARCHETYPE NAMES
# ============================================================

# Based on the current 2024 cluster profiles.

ARCHETYPES = {
    0: "High-Margin, Low-Leverage Leaders",
    1: "High-Operating-Margin Growth Companies",
    2: "High-Leverage / Weak-Cash-Flow Companies",
    3: "Diversified Core Large-Cap Companies",
    4: "Highly Leveraged Financial Companies",
}


df["archetype"] = df["cluster"].map(ARCHETYPES)


# ============================================================
# SAVE ARCHETYPE OUTPUT
# ============================================================

output = df[
    [
        "company_id",
        "company_name",
        "sector",
        "cluster",
        "archetype",
    ]
].sort_values(
    ["cluster", "company_name"]
)


output.to_csv(
    OUTPUT_FILE,
    index=False,
)


# ============================================================
# FINAL OUTPUT
# ============================================================

print("\n" + "=" * 70)
print("ARCHETYPE ASSIGNMENT COMPLETE")
print("=" * 70)

print(f"\nSaved:")
print(f"  {OUTPUT_FILE}")

print("\nArchetypes:")

for cluster, name in ARCHETYPES.items():

    count = (df["cluster"] == cluster).sum()

    print(
        f"  Cluster {cluster}: "
        f"{name} ({count} companies)"
    )
