
import pandas as pd
from pathlib import Path


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = BASE_DIR / "output"

CLUSTER_PROFILE_FILE = OUTPUT_DIR / "cluster_profiles_v4.csv"
COMPANY_CLUSTER_FILE = OUTPUT_DIR / "company_clusters_v4.csv"

ARCHETYPE_FILE = OUTPUT_DIR / "cluster_archetypes_v4.csv"
PROFILE_FILE = OUTPUT_DIR / "cluster_archetype_profiles_v4.csv"

EXPECTED_COMPANIES = 92
EXPECTED_CLUSTERS = {0, 1, 2, 3, 4}


# ============================================================
# FINAL ARCHETYPE DEFINITIONS
# ============================================================

ARCHETYPES = {
    0: {
        "name": "High-Leverage / Cash-Flow Stressed",
        "description": (
            "High leverage | Weak cash generation | Negative FCF conversion | "
            "Low interest coverage | Low capital intensity"
        ),
    },
    1: {
        "name": "Low-Leverage / Cash-Generative Compounders",
        "description": (
            "Low leverage | Strong cash generation | Strong FCF conversion | "
            "High ROE | High interest coverage"
        ),
    },
    2: {
        "name": "Capital-Efficient High-ROCE Companies",
        "description": (
            "Very low leverage | Extremely high ROCE | High operating margin | "
            "Strong interest coverage | Moderate FCF conversion"
        ),
    },
    3: {
        "name": "Leverage-Heavy / Weak Cash Conversion",
        "description": (
            "High leverage | Weak CFO generation | Negative FCF conversion | "
            "Low interest coverage | Low profitability"
        ),
    },
    4: {
        "name": "Capital-Intensive Profit Reinvestment",
        "description": (
            "Very high capital intensity | Strong CFO generation | Moderate leverage | "
            "Lower ROCE | Positive FCF conversion"
        ),
    },
}


# ============================================================
# LOAD
# ============================================================

print("=" * 70)
print("FIXING NIFTY100 CLUSTER ARCHETYPES V4")
print("=" * 70)

if not CLUSTER_PROFILE_FILE.exists():
    raise FileNotFoundError(
        f"Missing: {CLUSTER_PROFILE_FILE}"
    )

if not COMPANY_CLUSTER_FILE.exists():
    raise FileNotFoundError(
        f"Missing: {COMPANY_CLUSTER_FILE}"
    )

profiles = pd.read_csv(CLUSTER_PROFILE_FILE)
clusters = pd.read_csv(COMPANY_CLUSTER_FILE)

print(f"\nCluster profiles: {len(profiles)}")
print(f"Company assignments: {len(clusters)}")


# ============================================================
# VALIDATE COMPANY DATA
# ============================================================

if len(clusters) != EXPECTED_COMPANIES:
    raise ValueError(
        f"Expected {EXPECTED_COMPANIES} company rows, "
        f"found {len(clusters)}"
    )

if clusters["company_id"].nunique() != EXPECTED_COMPANIES:
    raise ValueError(
        "Company IDs are not unique."
    )

clusters["cluster"] = pd.to_numeric(
    clusters["cluster"],
    errors="coerce"
)

if clusters["cluster"].isna().any():
    raise ValueError(
        "Missing or invalid cluster values."
    )

actual_clusters = set(
    clusters["cluster"].astype(int).unique()
)

if actual_clusters != EXPECTED_CLUSTERS:
    raise ValueError(
        f"Expected clusters {EXPECTED_CLUSTERS}, "
        f"found {actual_clusters}"
    )

print("✓ 5 clusters validated")
print("✓ 92 companies validated")


# ============================================================
# VALIDATE PROFILE DATA
# ============================================================

profiles["cluster"] = pd.to_numeric(
    profiles["cluster"],
    errors="coerce"
)

profile_clusters = set(
    profiles["cluster"].dropna().astype(int)
)

if profile_clusters != EXPECTED_CLUSTERS:
    raise ValueError(
        f"Profile clusters mismatch: {profile_clusters}"
    )

print("✓ Cluster metric profiles validated")


# ============================================================
# CALCULATE COMPANY COUNTS + DOMINANT SECTORS
# ============================================================

cluster_counts = (
    clusters["cluster"]
    .astype(int)
    .value_counts()
    .sort_index()
)

dominant_sectors = {}

for cluster_id in sorted(EXPECTED_CLUSTERS):

    cluster_df = clusters[
        clusters["cluster"] == cluster_id
    ]

    if "sector" not in cluster_df.columns:
        dominant_sectors[cluster_id] = "Unknown"
        continue

    sector_counts = (
        cluster_df["sector"]
        .fillna("Unknown")
        .value_counts()
    )

    dominant_sectors[cluster_id] = (
        sector_counts.index[0]
        if not sector_counts.empty
        else "Unknown"
    )


# ============================================================
# UNIVERSE MEDIANS
# ============================================================

metric_columns = [
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
]

for column in metric_columns:

    if column not in profiles.columns:
        raise ValueError(
            f"Missing required metric column: {column}"
        )

    profiles[column] = pd.to_numeric(
        profiles[column],
        errors="coerce"
    )

universe_medians = {
    column: profiles[column].median()
    for column in metric_columns
}


# ============================================================
# SIMPLE ARCHETYPE SUMMARY
# ============================================================

summary_rows = []

for cluster_id in sorted(EXPECTED_CLUSTERS):

    profile = profiles[
        profiles["cluster"] == cluster_id
    ].iloc[0]

    count = int(cluster_counts[cluster_id])

    summary_rows.append(
        {
            "cluster": cluster_id,
            "company_count": count,
            "dominant_sector": dominant_sectors[cluster_id],
            "profile_description": ARCHETYPES[cluster_id]["description"],
        }
    )

archetype_summary = pd.DataFrame(summary_rows)

archetype_summary.to_csv(
    ARCHETYPE_FILE,
    index=False
)


# ============================================================
# DETAILED ARCHETYPE PROFILES
# ============================================================

detailed_rows = []

for cluster_id in sorted(EXPECTED_CLUSTERS):

    profile = profiles[
        profiles["cluster"] == cluster_id
    ].iloc[0]

    count = int(cluster_counts[cluster_id])

    percentage = round(
        count / EXPECTED_COMPANIES * 100,
        1
    )

    dominant_sector = dominant_sectors[cluster_id]

    profitability_summary = (
        f"Net margin {profile['net_profit_margin_pct']:.2f}% and "
        f"operating margin {profile['operating_profit_margin_pct']:.2f}% "
        f"vs universe medians "
        f"{universe_medians['net_profit_margin_pct']:.2f}%/"
        f"{universe_medians['operating_profit_margin_pct']:.2f}%."
    )

    capital_efficiency_summary = (
        f"ROE {profile['return_on_equity_pct']:.2f}% and "
        f"ROCE {profile['return_on_capital_employed_pct']:.2f}% "
        f"vs universe medians "
        f"{universe_medians['return_on_equity_pct']:.2f}%/"
        f"{universe_medians['return_on_capital_employed_pct']:.2f}%."
    )

    leverage_summary = (
        f"Debt-to-equity {profile['debt_to_equity']:.2f} and "
        f"interest coverage {profile['interest_coverage']:.2f}x "
        f"vs universe medians "
        f"{universe_medians['debt_to_equity']:.2f} and "
        f"{universe_medians['interest_coverage']:.2f}x."
    )

    cash_flow_summary = (
        f"CFO/PAT {profile['cfo_pat_ratio']:.2f} and "
        f"FCF conversion {profile['fcf_conversion_pct']:.2f}% "
        f"vs universe medians "
        f"{universe_medians['cfo_pat_ratio']:.2f} and "
        f"{universe_medians['fcf_conversion_pct']:.2f}%. "
        f"Capex intensity {profile['capex_intensity_pct']:.2f}% "
        f"vs universe median "
        f"{universe_medians['capex_intensity_pct']:.2f}%."
    )

    valuation_summary = (
        f"P/E {profile['pe_ratio']:.2f}, "
        f"P/B {profile['pb_ratio']:.2f}, "
        f"EV/EBITDA {profile['ev_ebitda']:.2f} "
        f"vs universe medians "
        f"{universe_medians['pe_ratio']:.2f}, "
        f"{universe_medians['pb_ratio']:.2f}, "
        f"{universe_medians['ev_ebitda']:.2f}."
    )

    detailed_rows.append(
        {
            "cluster": cluster_id,
            "archetype": ARCHETYPES[cluster_id]["name"],
            "company_count": count,
            "company_percentage": percentage,
            "dominant_sector": dominant_sector,
            "key_characteristics": ARCHETYPES[cluster_id]["description"],
            "profitability_summary": profitability_summary,
            "capital_efficiency_summary": capital_efficiency_summary,
            "leverage_summary": leverage_summary,
            "cash_flow_summary": cash_flow_summary,
            "valuation_summary": valuation_summary,
        }
    )


detailed_profiles = pd.DataFrame(
    detailed_rows
)

detailed_profiles.to_csv(
    PROFILE_FILE,
    index=False
)


# ============================================================
# UPDATE COMPANY CLUSTER FILE
# ============================================================

archetype_names = {
    cluster_id: ARCHETYPES[cluster_id]["name"]
    for cluster_id in EXPECTED_CLUSTERS
}

archetype_descriptions = {
    cluster_id: ARCHETYPES[cluster_id]["description"]
    for cluster_id in EXPECTED_CLUSTERS
}

clusters["archetype"] = (
    clusters["cluster"]
    .astype(int)
    .map(archetype_names)
)

clusters["archetype_description"] = (
    clusters["cluster"]
    .astype(int)
    .map(archetype_descriptions)
)

clusters.to_csv(
    COMPANY_CLUSTER_FILE,
    index=False
)


# ============================================================
# FINAL VALIDATION
# ============================================================

updated = pd.read_csv(
    COMPANY_CLUSTER_FILE
)

if len(updated) != EXPECTED_COMPANIES:
    raise ValueError(
        "Updated company cluster file does not contain 92 rows."
    )

if updated["company_id"].nunique() != EXPECTED_COMPANIES:
    raise ValueError(
        "Updated company IDs are not unique."
    )

if updated["archetype"].isna().any():
    raise ValueError(
        "Missing archetype assignments."
    )

if updated["archetype_description"].isna().any():
    raise ValueError(
        "Missing archetype descriptions."
    )

summary_check = pd.read_csv(
    ARCHETYPE_FILE
)

profile_check = pd.read_csv(
    PROFILE_FILE
)

if len(summary_check) != 5:
    raise ValueError(
        "Archetype summary must contain exactly 5 clusters."
    )

if len(profile_check) != 5:
    raise ValueError(
        "Archetype profile file must contain exactly 5 clusters."
    )

if summary_check["company_count"].sum() != EXPECTED_COMPANIES:
    raise ValueError(
        "Archetype company counts do not sum to 92."
    )


# ============================================================
# REPORT
# ============================================================

print("\n" + "=" * 70)
print("ARCHETYPE CORRECTION COMPLETE")
print("=" * 70)

print("\nFinal archetypes:")

for cluster_id in sorted(EXPECTED_CLUSTERS):

    count = int(
        (updated["cluster"] == cluster_id).sum()
    )

    print(
        f"Cluster {cluster_id}: "
        f"{ARCHETYPES[cluster_id]['name']} "
        f"({count} companies)"
    )

print("\nValidation:")
print("✓ 5 clusters")
print("✓ 92 companies")
print("✓ Counts sum to 92")
print("✓ No missing archetypes")
print("✓ No missing descriptions")
print("✓ Cluster 0 wording corrected")
print("✓ Cluster 2 wording corrected")
print("✓ Cluster 3 wording preserved")
print("✓ Cluster 4 wording preserved")

print("\nUpdated files:")
print(f"- {ARCHETYPE_FILE}")
print(f"- {PROFILE_FILE}")
print(f"- {COMPANY_CLUSTER_FILE}")

print("\n" + "=" * 70)

