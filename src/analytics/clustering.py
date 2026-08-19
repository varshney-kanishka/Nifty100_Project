import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import RobustScaler
from sklearn.metrics import davies_bouldin_score, silhouette_score


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

DB_PATH = BASE_DIR / "data" / "database" / "nifty100.db"

OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "company_clusters.csv"
PROFILE_FILE = OUTPUT_DIR / "cluster_profiles.csv"
ARCHETYPE_PROFILE_FILE = OUTPUT_DIR / "cluster_archetype_profiles.csv"

LATEST_YEAR = "2024"
N_CLUSTERS = 5
EXPECTED_COMPANIES = 92


# ============================================================
# CLUSTERING FEATURES
# ============================================================
# These are common features that are meaningful across both
# Financial and Non-Financial companies.
#
# Cash-flow metrics are deliberately excluded from the KMeans
# feature vector because CFO/FCF behave differently for
# financial institutions.
# ============================================================

FEATURES = [
    "net_profit_margin_pct",
    "return_on_equity_pct",
    "debt_to_equity",
    "interest_coverage",
    "pe_ratio",
    "pb_ratio",
    "ev_ebitda",
    "dividend_yield_pct",
]


OUTLIER_FEATURES = {
    "return_on_equity_pct",
    "interest_coverage",
}


LOG_FEATURES = {
    "return_on_equity_pct",
    "interest_coverage",
}


FEATURE_LABELS = {
    "net_profit_margin_pct": "net profit margin",
    "return_on_equity_pct": "ROE",
    "debt_to_equity": "debt-to-equity",
    "interest_coverage": "interest coverage",
    "pe_ratio": "P/E",
    "pb_ratio": "P/B",
    "ev_ebitda": "EV/EBITDA",
    "dividend_yield_pct": "dividend yield",
}


# ============================================================
# HELPERS
# ============================================================

def safe_divide(numerator, denominator):
    return np.where(
        pd.notna(numerator)
        & pd.notna(denominator)
        & (denominator != 0),
        numerator / denominator,
        np.nan,
    )


def signed_log1p(series):
    return np.sign(series) * np.log1p(np.abs(series))


def assert_condition(condition, message):
    if not condition:
        raise ValueError(message)


def clean_name(value):
    return " ".join(str(value).split())


def safe_relative_delta(cluster_value, baseline_value):
    return (cluster_value - baseline_value) / (
        abs(baseline_value) + 1e-9
    )


def describe_relative(feature, cluster_median, overall_median):
    delta = safe_relative_delta(
        cluster_median,
        overall_median,
    )

    label = FEATURE_LABELS[feature]

    direction = (
        "higher"
        if delta >= 0
        else "lower"
    )

    return (
        abs(delta),
        f"{direction} {label} "
        f"(median {cluster_median:.2f} "
        f"vs universe {overall_median:.2f})"
    )


def strongest_characteristics(
    cluster_median_row,
    overall_median_row,
    top_n=5,
):

    ranked = []

    for feature in FEATURES:

        strength, text = describe_relative(
            feature,
            float(cluster_median_row[feature]),
            float(overall_median_row[feature]),
        )

        ranked.append(
            (
                strength,
                feature,
                text,
            )
        )

    ranked.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    return [
        item[2]
        for item in ranked[:top_n]
    ]


# ============================================================
# DATA LOADING
# ============================================================

print("=" * 70)
print("NIFTY100 COMPANY KMEANS CLUSTERING V6")
print("=" * 70)

print(f"\nDatabase: {DB_PATH}")
print(f"Clustering year: {LATEST_YEAR}")
print(f"Number of clusters: {N_CLUSTERS}")

if not DB_PATH.exists():
    raise FileNotFoundError(
        f"Database not found: {DB_PATH}"
    )


conn = sqlite3.connect(DB_PATH)

try:

    companies = pd.read_sql_query(
        """
        SELECT
            c.id AS company_id,
            c.company_name,
            s.broad_sector AS sector
        FROM companies c
        LEFT JOIN sectors s
            ON c.id = s.company_id
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
            debt_to_equity,
            interest_coverage,
            free_cash_flow_cr,
            capex_cr,
            cash_from_operations_cr
        FROM financial_ratios
        WHERE year = ?
        """,
        conn,
        params=(LATEST_YEAR,),
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
        params=(LATEST_YEAR,),
    )

    market_cap = pd.read_sql_query(
        """
        SELECT
            company_id,
            year,
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

finally:
    conn.close()


print("\nData loaded:")
print(f"Companies:      {len(companies)}")
print(f"2024 ratios:    {len(ratios)}")
print(f"2024 P&L:       {len(profit)}")
print(f"2024 valuation: {len(market_cap)}")


# ============================================================
# ID NORMALIZATION
# ============================================================

for frame in [
    companies,
    ratios,
    profit,
    market_cap,
]:

    frame.loc[:, "company_id"] = (
        frame["company_id"]
        .astype(str)
        .str.strip()
    )


ratios = ratios.drop_duplicates(
    subset=["company_id"],
    keep="last",
)

profit = profit.drop_duplicates(
    subset=["company_id"],
    keep="last",
)

market_cap = market_cap.drop_duplicates(
    subset=["company_id"],
    keep="last",
)


# ============================================================
# MERGE
# ============================================================

df = companies.copy()

df = df.merge(
    ratios.drop(columns=["year"]),
    on="company_id",
    how="left",
)

df = df.merge(
    profit.drop(columns=["year"]),
    on="company_id",
    how="left",
)

df = df.merge(
    market_cap.drop(columns=["year"]),
    on="company_id",
    how="left",
)


print(f"\nMerged rows: {len(df)}")


# ============================================================
# VALIDATION
# ============================================================

assert_condition(
    len(df) == EXPECTED_COMPANIES,
    f"Expected {EXPECTED_COMPANIES} companies "
    f"but found {len(df)}",
)

assert_condition(
    df["company_id"].notna().all(),
    "Missing company IDs found",
)

assert_condition(
    df["company_id"].nunique() == EXPECTED_COMPANIES,
    "Duplicate company IDs found",
)

assert_condition(
    df["sector"].notna().all(),
    "Missing sector values found",
)


# ============================================================
# CASH-FLOW INTELLIGENCE
# ============================================================
# IMPORTANT:
# We now use the database's trusted FCF and CapEx fields.
#
# We do NOT calculate:
# FCF = CFO + total investing activity
#
# and we do NOT call total investing activity "CapEx".
# ============================================================

df.loc[:, "cfo_pat_ratio"] = safe_divide(
    df["cash_from_operations_cr"],
    df["net_profit"],
)

df.loc[:, "fcf_conversion_pct"] = (
    safe_divide(
        df["free_cash_flow_cr"],
        df["operating_profit"],
    )
    * 100
)

df.loc[:, "capex_intensity_pct"] = (
    safe_divide(
        np.abs(df["capex_cr"]),
        df["sales"],
    )
    * 100
)


# ============================================================
# FEATURE VALIDATION
# ============================================================

print("\nSelected V6 clustering features:")

for feature in FEATURES:
    print(f"  - {feature}")


print("\nMissing clustering values before imputation:")

missing = df[FEATURES].isna().sum()

if (missing > 0).any():
    print(
        missing[missing > 0].to_string()
    )
else:
    print("  0")


# ============================================================
# IMPUTATION
# ============================================================

for feature in FEATURES:

    median_value = df[feature].median()

    if pd.isna(median_value):

        raise ValueError(
            f"Cannot impute {feature}: "
            "median is NaN"
        )

    df.loc[:, feature] = (
        df[feature]
        .fillna(median_value)
    )


print("\nMissing values after imputation:")

print(
    df[FEATURES]
    .isna()
    .sum()
    .sum()
)


# ============================================================
# OUTLIER HANDLING
# ============================================================

print("\nApplying V6 robust preprocessing...")

X = df[FEATURES].copy()


# ------------------------------------------------------------
# Percentile clipping
# ------------------------------------------------------------

for feature in FEATURES:

    low = X[feature].quantile(0.05)
    high = X[feature].quantile(0.95)

    X.loc[:, feature] = X[
        feature
    ].clip(
        lower=low,
        upper=high,
    )

    print(
        f"  {feature}: "
        f"{low:.2f} -> {high:.2f}"
    )


# ------------------------------------------------------------
# Log transform only the strongly skewed variables
# ------------------------------------------------------------

print("\nApplying signed_log1p:")

for feature in LOG_FEATURES:

    X.loc[:, feature] = signed_log1p(
        X[feature]
    )

    print(
        f"  - {feature}"
    )


# ============================================================
# ROBUST SCALING
# ============================================================

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

df.loc[:, "cluster"] = (
    kmeans.fit_predict(X_scaled)
)


# ============================================================
# MODEL VALIDATION
# ============================================================

silhouette = silhouette_score(
    X_scaled,
    df["cluster"],
)

davies_bouldin = davies_bouldin_score(
    X_scaled,
    df["cluster"],
)


print("\nCluster validation:")

print(
    f"  Silhouette Score:       "
    f"{silhouette:.4f}"
)

print(
    f"  Davies-Bouldin Index:   "
    f"{davies_bouldin:.4f}"
)

print(
    f"  KMeans Inertia:         "
    f"{kmeans.inertia_:.2f}"
)


# ============================================================
# CLUSTER SIZE VALIDATION
# ============================================================

cluster_sizes = (
    df["cluster"]
    .value_counts()
    .sort_index()
)


assert_condition(
    df["cluster"].nunique()
    == N_CLUSTERS,
    "Expected exactly 5 clusters",
)

assert_condition(
    cluster_sizes.sum()
    == EXPECTED_COMPANIES,
    "Cluster counts do not sum to 92",
)


# ============================================================
# CLUSTER PROFILES
# ============================================================

profile_mean = (
    df.groupby("cluster")[FEATURES]
    .mean()
    .round(2)
)

profile_median = (
    df.groupby("cluster")[FEATURES]
    .median()
    .round(2)
)

overall_median = (
    df[FEATURES]
    .median()
)


print("\nCluster sizes:")

for cluster_id, size in cluster_sizes.items():

    print(
        f"  Cluster {cluster_id}: "
        f"{size} companies"
    )


# ============================================================
# SECTOR DISTRIBUTION
# ============================================================

sector_distribution = pd.crosstab(
    df["cluster"],
    df["sector"],
)

sector_pct = (
    sector_distribution
    .div(
        sector_distribution.sum(axis=1),
        axis=0,
    )
    .mul(100)
    .round(1)
)


print("\nSector distribution:")

print(
    sector_distribution.to_string()
)


print("\nSector percentage:")

print(
    sector_pct.to_string()
)


# ============================================================
# FINANCIAL VS NON-FINANCIAL
# ============================================================

df.loc[:, "company_type"] = np.where(
    df["sector"].eq("Financials"),
    "Financial",
    "Non-Financial",
)


print("\nFinancial vs Non-Financial:")

print(
    df["company_type"]
    .value_counts()
    .to_string()
)


financial_distribution = pd.crosstab(
    df["cluster"],
    df["company_type"],
)


print(
    "\nFinancial / Non-Financial distribution:"
)

print(
    financial_distribution.to_string()
)


# ============================================================
# DATA-DRIVEN ARCHETYPE DESCRIPTIONS
# ============================================================

archetype_rows = []

print("\n" + "=" * 70)
print("V6 CLUSTER INTERPRETATION")
print("=" * 70)


for cluster_id in sorted(
    df["cluster"].unique()
):

    cluster_df = df[
        df["cluster"] == cluster_id
    ].copy()

    company_count = len(
        cluster_df
    )

    company_pct = (
        company_count
        / EXPECTED_COMPANIES
        * 100
    )

    cluster_median = (
        cluster_df[FEATURES]
        .median()
    )

    sector_counts = (
        cluster_df["sector"]
        .value_counts()
    )

    dominant_sector = (
        sector_counts.index[0]
    )

    dominant_pct = (
        sector_counts.iloc[0]
        / company_count
        * 100
    )

    financial_count = (
        cluster_df["company_type"]
        .eq("Financial")
        .sum()
    )

    non_financial_count = (
        cluster_df["company_type"]
        .eq("Non-Financial")
        .sum()
    )

    characteristics = (
        strongest_characteristics(
            cluster_median,
            overall_median,
            top_n=5,
        )
    )

    # --------------------------------------------------------
    # Data-driven archetype label V6
    # --------------------------------------------------------

    dte = float(
        cluster_median["debt_to_equity"]
    )

    roe = float(
        cluster_median["return_on_equity_pct"]
    )

    npm = float(
        cluster_median["net_profit_margin_pct"]
    )

    ic = float(
        cluster_median["interest_coverage"]
    )

    financial_pct = (
        financial_count
        / company_count
        * 100
    )

    if financial_pct >= 60:

        if dte >= 6 and ic < 3:
            archetype = (
                "Highly Leveraged Financial Institutions"
            )

        elif dte >= 3:
            archetype = (
                "Leveraged Financial Institutions"
            )

        else:
            archetype = (
                "Financial Institutions"
            )

    elif dte >= 0.60 and npm < 10 and ic < 10:

        archetype = (
            "Higher-Leverage Lower-Profitability Companies"
        )

    elif dte < 0.15 and roe >= 25:

        archetype = (
            "High-ROE Premium Quality Companies"
        )

    elif dte < 0.15 and ic >= 40:

        archetype = (
            "Low-Leverage Established Quality Companies"
        )

    elif dte < 0.75 and npm >= 15:

        archetype = (
            "Profitable Conservatively Leveraged Companies"
        )

    else:

        archetype = (
            "Balanced Diversified Companies"
        )

    
    # --------------------------------------------------------
    # Cash-flow profile
    # --------------------------------------------------------

    cfo_pat = cluster_df[
        "cfo_pat_ratio"
    ].median()

    fcf_conversion = cluster_df[
        "fcf_conversion_pct"
    ].median()

    capex_intensity = cluster_df[
        "capex_intensity_pct"
    ].median()


    if financial_pct >= 60:

        cash_flow_note = (
            "Cash-flow metrics are "
            "reported for reference only; "
            "financial-sector interpretation "
            "is not directly comparable."
        )

    else:

        cash_flow_note = (
            f"CFO/PAT median {cfo_pat:.2f}; "
            f"FCF conversion median "
            f"{fcf_conversion:.2f}%; "
            f"CapEx intensity median "
            f"{capex_intensity:.2f}%."
        )


    companies_sorted = [
        clean_name(name)
        for name in
        cluster_df
        .sort_values("company_name")
        ["company_name"]
        .tolist()
    ]


    print(
        f"\nCluster {cluster_id}"
    )

    print(
        f"Archetype: {archetype}"
    )

    print(
        f"Companies: {company_count}"
    )

    print(
        f"Share: {company_pct:.2f}%"
    )

    print(
        f"Financials: "
        f"{financial_count}"
    )

    print(
        f"Non-Financials: "
        f"{non_financial_count}"
    )

    print(
        f"Dominant sector: "
        f"{dominant_sector} "
        f"({dominant_pct:.1f}%)"
    )

    print(
        "Characteristics:"
    )

    for characteristic in characteristics:

        print(
            f"  - {characteristic}"
        )

    print(
        f"Cash-flow note: "
        f"{cash_flow_note}"
    )

    print(
        "Companies:"
    )

    print(
        "  - "
        + " | ".join(
            companies_sorted
        )
    )


    archetype_rows.append(
        {
            "cluster": int(cluster_id),
            "archetype": archetype,
            "company_count": int(
                company_count
            ),
            "company_percentage": round(
                company_pct,
                2,
            ),
            "financial_count": int(
                financial_count
            ),
            "non_financial_count": int(
                non_financial_count
            ),
            "dominant_sector": (
                f"{dominant_sector} "
                f"({dominant_pct:.1f}%)"
            ),
            "key_characteristics":
                " | ".join(
                    characteristics
                ),
            "cash_flow_profile":
                cash_flow_note,
        }
    )


    df.loc[
        df["cluster"] == cluster_id,
        "archetype"
    ] = archetype

    df.loc[
        df["cluster"] == cluster_id,
        "archetype_description"
    ] = (
        "Data-driven cluster profile: "
        + cash_flow_note
    )


# ============================================================
# OUTPUT
# ============================================================

OUTPUT_COLUMNS = [
    "company_id",
    "company_name",
    "cluster",
    "sector",
    "company_type",
    "archetype",
    "archetype_description",
] + FEATURES + [
    "cfo_pat_ratio",
    "fcf_conversion_pct",
    "capex_intensity_pct",
]


output = (
    df[OUTPUT_COLUMNS]
    .sort_values(
        ["cluster", "company_name"]
    )
    .copy()
)


output.to_csv(
    OUTPUT_FILE,
    index=False,
)


profile_mean.to_csv(
    PROFILE_FILE
)


pd.DataFrame(
    archetype_rows
).sort_values(
    "cluster"
).to_csv(
    ARCHETYPE_PROFILE_FILE,
    index=False,
)


# ============================================================
# OUTPUT VALIDATION
# ============================================================

written_output = pd.read_csv(
    OUTPUT_FILE
)


assert_condition(
    len(written_output)
    == EXPECTED_COMPANIES,
    "Output must contain 92 companies",
)

assert_condition(
    written_output[
        "company_id"
    ].nunique()
    == EXPECTED_COMPANIES,
    "Output contains duplicate companies",
)

assert_condition(
    written_output[
        "archetype"
    ].notna().all(),
    "Missing archetypes",
)

assert_condition(
    written_output[
        "cluster"
    ].nunique()
    == N_CLUSTERS,
    "Output must contain exactly 5 clusters",
)


# ============================================================
# FINAL REPORT
# ============================================================

print("\n" + "=" * 70)
print("FINAL V6 CLUSTER SUMMARY")
print("=" * 70)


for row in sorted(
    archetype_rows,
    key=lambda x: x["cluster"],
):

    print(
        f"\nCluster {row['cluster']} "
        f"- {row['archetype']}"
    )

    print(
        f"Companies: "
        f"{row['company_count']}"
    )

    print(
        f"Share: "
        f"{row['company_percentage']:.2f}%"
    )

    print(
        f"Financials: "
        f"{row['financial_count']}"
    )

    print(
        f"Non-Financials: "
        f"{row['non_financial_count']}"
    )

    print(
        "Characteristics: "
        f"{row['key_characteristics']}"
    )


print("\nModel metrics:")

print(
    f"Silhouette Score: "
    f"{silhouette:.4f}"
)

print(
    f"Davies-Bouldin Index: "
    f"{davies_bouldin:.4f}"
)

print(
    f"KMeans Inertia: "
    f"{kmeans.inertia_:.2f}"
)


print("\nOutputs written:")

print(OUTPUT_FILE)
print(PROFILE_FILE)
print(ARCHETYPE_PROFILE_FILE)

print("\nV6 completed successfully.")