import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import davies_bouldin_score, silhouette_score
from sklearn.preprocessing import RobustScaler


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]

DB_PATH = BASE_DIR / "data" / "database" / "nifty100.db"

OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "company_clusters_v4.csv"
PROFILE_FILE = OUTPUT_DIR / "cluster_profiles_v4.csv"
ARCHETYPE_PROFILE_FILE = OUTPUT_DIR / "cluster_archetype_profiles_v4.csv"

LATEST_YEAR = "2024"
N_CLUSTERS = 5
EXPECTED_COMPANIES = 92


# ============================================================
# FEATURES
# ============================================================

FEATURES = [
    # Profitability
    "net_profit_margin_pct",
    "operating_profit_margin_pct",
    "return_on_equity_pct",
    "return_on_capital_employed_pct",
    # Financial strength
    "debt_to_equity",
    "interest_coverage",
    # Cash quality
    "cfo_pat_ratio",
    "fcf_conversion_pct",
    # Capital intensity
    "capex_intensity_pct",
    # Valuation
    "pe_ratio",
    "pb_ratio",
    "ev_ebitda",
    "dividend_yield_pct",
]

RATIO_FEATURES = [
    "return_on_equity_pct",
    "return_on_capital_employed_pct",
    "interest_coverage",
    "cfo_pat_ratio",
    "fcf_conversion_pct",
    "capex_intensity_pct",
]

GENERAL_FEATURES = [
    "net_profit_margin_pct",
    "operating_profit_margin_pct",
    "debt_to_equity",
    "pe_ratio",
    "pb_ratio",
    "ev_ebitda",
    "dividend_yield_pct",
]

LOG_FEATURES = [
    "return_on_equity_pct",
    "return_on_capital_employed_pct",
    "interest_coverage",
    "cfo_pat_ratio",
    "fcf_conversion_pct",
]

FEATURE_LABELS = {
    "net_profit_margin_pct": "net profit margin",
    "operating_profit_margin_pct": "operating margin",
    "return_on_equity_pct": "ROE",
    "return_on_capital_employed_pct": "ROCE",
    "debt_to_equity": "debt-to-equity",
    "interest_coverage": "interest coverage",
    "cfo_pat_ratio": "CFO/PAT",
    "fcf_conversion_pct": "FCF conversion",
    "capex_intensity_pct": "capex intensity",
    "pe_ratio": "P/E",
    "pb_ratio": "P/B",
    "ev_ebitda": "EV/EBITDA",
    "dividend_yield_pct": "dividend yield",
}

OUTLIER_PRONE_FEATURES = {
    "return_on_equity_pct",
    "return_on_capital_employed_pct",
    "interest_coverage",
    "cfo_pat_ratio",
    "fcf_conversion_pct",
}


# ============================================================
# HELPERS
# ============================================================

def safe_divide(numerator, denominator):
    """Return NaN where denominator is zero or missing."""
    return np.where(
        pd.notna(numerator) & pd.notna(denominator) & (denominator != 0),
        numerator / denominator,
        np.nan,
    )


def signed_log1p(series):
    """Compress extreme positive and negative values while preserving sign."""
    return np.sign(series) * np.log1p(np.abs(series))


def assert_condition(condition, message):
    if not condition:
        raise ValueError(message)


def clean_name(value):
    return " ".join(str(value).split())


def format_feature_pair(mean_value, median_value):
    return f"median={median_value:.2f}, mean={mean_value:.2f}"


def safe_relative_delta(cluster_value, baseline_value):
    return (cluster_value - baseline_value) / (abs(baseline_value) + 1e-9)


def describe_relative(feature, cluster_median, overall_median):
    delta = safe_relative_delta(cluster_median, overall_median)
    label = FEATURE_LABELS[feature]
    direction = "higher" if delta >= 0 else "lower"
    return abs(delta), f"{direction} {label} (median {cluster_median:.2f} vs universe {overall_median:.2f})"


def strongest_characteristics(cluster_mean_row, cluster_median_row, overall_median_row, top_n=5):
    ranked = []
    for feature in FEATURES:
        strength, text = describe_relative(
            feature,
            float(cluster_median_row[feature]),
            float(overall_median_row[feature]),
        )
        ranked.append((strength, feature, text))

    ranked.sort(key=lambda item: item[0], reverse=True)
    selected = [item[2] for item in ranked[:top_n]]

    for feature in OUTLIER_PRONE_FEATURES:
        mean_value = float(cluster_mean_row[feature])
        median_value = float(cluster_median_row[feature])
        divergence = abs(mean_value - median_value) / (abs(median_value) + 1e-9)
        if divergence >= 0.75 and len(selected) < top_n:
            selected.append(
                f"material mean-median divergence in {FEATURE_LABELS[feature]} "
                f"(median {median_value:.2f}, mean {mean_value:.2f})"
            )

    return selected[:top_n]


def percentile_band(cluster_value, all_values):
    return float((all_values <= cluster_value).mean()) * 100.0


def summarize_profitability(cluster_median_row, overall_median_row):
    npm = float(cluster_median_row["net_profit_margin_pct"])
    opm = float(cluster_median_row["operating_profit_margin_pct"])
    npm_ref = float(overall_median_row["net_profit_margin_pct"])
    opm_ref = float(overall_median_row["operating_profit_margin_pct"])
    return (
        f"Net margin {npm:.2f}% and operating margin {opm:.2f}% "
        f"vs universe medians {npm_ref:.2f}%/{opm_ref:.2f}%."
    )


def summarize_capital_efficiency(cluster_median_row, overall_median_row):
    roe = float(cluster_median_row["return_on_equity_pct"])
    roce = float(cluster_median_row["return_on_capital_employed_pct"])
    roe_ref = float(overall_median_row["return_on_equity_pct"])
    roce_ref = float(overall_median_row["return_on_capital_employed_pct"])
    return (
        f"ROE {roe:.2f}% and ROCE {roce:.2f}% "
        f"vs universe medians {roe_ref:.2f}%/{roce_ref:.2f}% "
        f"(use medians due to extreme outliers)."
    )


def summarize_leverage(cluster_median_row, overall_median_row):
    dte = float(cluster_median_row["debt_to_equity"])
    ic = float(cluster_median_row["interest_coverage"])
    dte_ref = float(overall_median_row["debt_to_equity"])
    ic_ref = float(overall_median_row["interest_coverage"])
    return (
        f"Debt-to-equity {dte:.2f} and interest coverage {ic:.2f}x "
        f"vs universe medians {dte_ref:.2f} and {ic_ref:.2f}x."
    )


def summarize_cash_flow(cluster_median_row, overall_median_row):
    cfo_pat = float(cluster_median_row["cfo_pat_ratio"])
    fcf_conv = float(cluster_median_row["fcf_conversion_pct"])
    cfo_ref = float(overall_median_row["cfo_pat_ratio"])
    fcf_ref = float(overall_median_row["fcf_conversion_pct"])
    return (
        f"CFO/PAT {cfo_pat:.2f} and FCF conversion {fcf_conv:.2f}% "
        f"vs universe medians {cfo_ref:.2f} and {fcf_ref:.2f}%."
    )


def summarize_capex_intensity(cluster_median_row, overall_median_row):
    capex = float(cluster_median_row["capex_intensity_pct"])
    capex_ref = float(overall_median_row["capex_intensity_pct"])
    return (
        f"Capex intensity {capex:.2f}% vs universe median {capex_ref:.2f}%."
    )


def summarize_valuation(cluster_median_row, overall_median_row):
    pe = float(cluster_median_row["pe_ratio"])
    pb = float(cluster_median_row["pb_ratio"])
    ev = float(cluster_median_row["ev_ebitda"])
    pe_ref = float(overall_median_row["pe_ratio"])
    pb_ref = float(overall_median_row["pb_ratio"])
    ev_ref = float(overall_median_row["ev_ebitda"])
    return (
        f"P/E {pe:.2f}, P/B {pb:.2f}, EV/EBITDA {ev:.2f} vs "
        f"universe medians {pe_ref:.2f}, {pb_ref:.2f}, {ev_ref:.2f}."
    )


def short_archetype_description(cluster_median_row, overall_median_row):
    leverage_text = (
        "higher leverage" if float(cluster_median_row["debt_to_equity"]) > float(overall_median_row["debt_to_equity"]) else "lower leverage"
    )
    cash_text = (
        "weaker cash conversion" if float(cluster_median_row["fcf_conversion_pct"]) < float(overall_median_row["fcf_conversion_pct"]) else "healthier cash conversion"
    )
    capex_text = (
        "capex-heavy" if float(cluster_median_row["capex_intensity_pct"]) > float(overall_median_row["capex_intensity_pct"]) else "capex-light"
    )
    return f"{leverage_text}, {cash_text}, {capex_text} profile based on cluster medians."


# ============================================================
# START
# ============================================================

print("=" * 70)
print("NIFTY100 COMPANY KMEANS CLUSTERING V4")
print("=" * 70)

print(f"\nDatabase: {DB_PATH}")
print(f"Clustering year: {LATEST_YEAR}")
print(f"Number of clusters: {N_CLUSTERS}")

if not DB_PATH.exists():
    raise FileNotFoundError(f"Database not found: {DB_PATH}")


# ============================================================
# DATABASE
# ============================================================

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
            return_on_capital_employed_pct,
            debt_to_equity,
            interest_coverage
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
print(f"2024 cash flow: {len(cashflow)}")
print(f"2024 valuation: {len(market_cap)}")


# ============================================================
# ID NORMALIZATION AND DEDUP
# ============================================================

for frame in [companies, ratios, profit, cashflow, market_cap]:
    frame.loc[:, "company_id"] = frame["company_id"].astype(str).str.strip()

ratios = ratios.drop_duplicates(subset=["company_id"], keep="last")
profit = profit.drop_duplicates(subset=["company_id"], keep="last")
cashflow = cashflow.drop_duplicates(subset=["company_id"], keep="last")
market_cap = market_cap.drop_duplicates(subset=["company_id"], keep="last")


# ============================================================
# MERGE
# ============================================================

df = companies.copy()
df = df.merge(ratios.drop(columns=["year"]), on="company_id", how="left")
df = df.merge(profit.drop(columns=["year"]), on="company_id", how="left")
df = df.merge(cashflow.drop(columns=["year"]), on="company_id", how="left")
df = df.merge(market_cap.drop(columns=["year"]), on="company_id", how="left")

print(f"\nMerged rows: {len(df)}")


# ============================================================
# VALIDATION CHECKS (PRE-CLUSTER)
# ============================================================

assert_condition(len(df) == EXPECTED_COMPANIES, f"Expected {EXPECTED_COMPANIES} companies but found {len(df)}")
assert_condition(df["company_id"].notna().all(), "Missing company IDs found")
assert_condition((df["company_id"].str.strip() != "").all(), "Blank company IDs found")
assert_condition(df["company_id"].nunique() == EXPECTED_COMPANIES, "Duplicate company IDs found")
assert_condition(df["sector"].notna().all(), "Missing sector values found")
assert_condition((df["sector"].astype(str).str.strip() != "").all(), "Blank sector values found")


# ============================================================
# FEATURE ENGINEERING
# ============================================================

df.loc[:, "cfo_pat_ratio"] = safe_divide(df["operating_activity"], df["net_profit"])
df.loc[:, "fcf"] = df["operating_activity"] + df["investing_activity"]
df.loc[:, "fcf_conversion_pct"] = safe_divide(df["fcf"], df["operating_profit"]) * 100
df.loc[:, "capex_intensity_pct"] = safe_divide(np.abs(df["investing_activity"]), df["sales"]) * 100

print("\nSelected V4 features:")
for feature in FEATURES:
    print(f"  - {feature}")

print("\nMissing values before imputation:")
missing = df[FEATURES].isna().sum()
if (missing > 0).any():
    print(missing[missing > 0].to_string())
else:
    print("  0")


# ============================================================
# IMPUTATION
# ============================================================

for feature in FEATURES:
    median_value = df[feature].median()
    if pd.isna(median_value):
        raise ValueError(f"Cannot impute {feature}: median is NaN")
    df.loc[:, feature] = df[feature].fillna(median_value)

print("\nMissing values after imputation:")
print(df[FEATURES].isna().sum().sum())


# ============================================================
# OUTLIER HANDLING + TRANSFORM + SCALE
# ============================================================

print("\nApplying robust ratio handling...")
X = df[FEATURES].copy()

print("\nCapping extreme ratio values (5th-90th pct):")
for feature in RATIO_FEATURES:
    low = X[feature].quantile(0.05)
    high = X[feature].quantile(0.90)
    X.loc[:, feature] = X[feature].clip(lower=low, upper=high)
    print(f"  {feature}: {low:.2f} -> {high:.2f}")

print("\nCapping general features (5th-95th pct):")
for feature in GENERAL_FEATURES:
    low = X[feature].quantile(0.05)
    high = X[feature].quantile(0.95)
    X.loc[:, feature] = X[feature].clip(lower=low, upper=high)

print("\nApplying signed_log1p on extreme ratio features:")
for feature in LOG_FEATURES:
    X.loc[:, feature] = signed_log1p(X[feature])
    print(f"  - {feature}")

print("\nApplying RobustScaler...")
scaler = RobustScaler()
X_scaled = scaler.fit_transform(X)


# ============================================================
# KMEANS (UNCHANGED METHODOLOGY)
# ============================================================

print("\nRunning KMeans...")
kmeans = KMeans(n_clusters=N_CLUSTERS, random_state=42, n_init=50)
df.loc[:, "cluster"] = kmeans.fit_predict(X_scaled)

silhouette = silhouette_score(X_scaled, df["cluster"])
davies_bouldin = davies_bouldin_score(X_scaled, df["cluster"])

print("\nCluster validation:")
print(f"  Silhouette Score:       {silhouette:.4f}")
print(f"  Davies-Bouldin Index:   {davies_bouldin:.4f}")
print(f"  KMeans Inertia:         {kmeans.inertia_:.2f}")

cluster_sizes = df["cluster"].value_counts().sort_index()


# ============================================================
# VALIDATION CHECKS (POST-CLUSTER)
# ============================================================

assert_condition(df["cluster"].nunique() == N_CLUSTERS, f"Expected exactly {N_CLUSTERS} clusters")
assert_condition(int(cluster_sizes.sum()) == EXPECTED_COMPANIES, f"Cluster counts do not sum to {EXPECTED_COMPANIES}")


# ============================================================
# PROFILES (MEAN + MEDIAN)
# ============================================================

profile_mean = df.groupby("cluster", as_index=True)[FEATURES].mean().round(2)
profile_median = df.groupby("cluster", as_index=True)[FEATURES].median().round(2)
overall_median = df[FEATURES].median()

print("\nCluster sizes:")
for cluster_id, size in cluster_sizes.items():
    print(f"  Cluster {cluster_id}: {size} companies")

sector_distribution = pd.crosstab(df["cluster"], df["sector"])
sector_pct = sector_distribution.div(sector_distribution.sum(axis=1), axis=0).mul(100).round(1)

print("\nSector distribution by cluster:")
print(sector_distribution.to_string())

print("\nSector percentage within each cluster:")
print(sector_pct.to_string())

print("\nCluster mean profiles:")
print(profile_mean.to_string())

print("\nCluster median profiles:")
print(profile_median.to_string())


# ============================================================
# ARCHETYPE NAMING (STABLE CLUSTER IDS)
# ============================================================

ARCHETYPE_NAMES = {
    0: "High-Leverage / Cash-Flow Stressed",
    1: "Low-Leverage / Cash-Generative Compounders",
    2: "Capital-Efficient Premium Compounders",
    3: "Leverage-Heavy / Weak Cash Conversion",
    4: "Capital-Intensive Profit Reinvestment",
}

assert_condition(set(ARCHETYPE_NAMES.keys()) == set(range(N_CLUSTERS)), "ARCHETYPE_NAMES keys must match cluster IDs 0-4")

df.loc[:, "archetype"] = df["cluster"].map(ARCHETYPE_NAMES)
assert_condition(df["archetype"].notna().all(), "Missing archetype detected after mapping")


# ============================================================
# CLUSTER-LEVEL DETAILED REPORT + ARCHETYPE PROFILE BUILD
# ============================================================

archetype_rows = []

print("\n" + "=" * 70)
print("DETAILED CLUSTER VALIDATION REPORT")
print("=" * 70)

for cluster_id in sorted(df["cluster"].unique()):
    cluster_df = df[df["cluster"] == cluster_id].copy()
    company_count = len(cluster_df)
    company_pct = company_count / EXPECTED_COMPANIES * 100

    cluster_mean_row = df[df["cluster"] == cluster_id][FEATURES].mean()
    cluster_median_row = df[df["cluster"] == cluster_id][FEATURES].median()

    sector_counts = cluster_df["sector"].value_counts()
    sector_shares = (sector_counts / company_count * 100).round(1)
    dominant_sector = sector_counts.idxmax()
    dominant_pct = sector_shares.loc[dominant_sector]

    companies_sorted = [clean_name(name) for name in cluster_df.sort_values("company_name")["company_name"].tolist()]

    characteristics = strongest_characteristics(
        cluster_mean_row=cluster_mean_row,
        cluster_median_row=cluster_median_row,
        overall_median_row=overall_median,
        top_n=5,
    )

    profitability_summary = summarize_profitability(cluster_median_row, overall_median)
    capital_eff_summary = summarize_capital_efficiency(cluster_median_row, overall_median)
    leverage_summary = summarize_leverage(cluster_median_row, overall_median)
    cash_flow_summary = summarize_cash_flow(cluster_median_row, overall_median)
    capex_summary = summarize_capex_intensity(cluster_median_row, overall_median)
    valuation_summary = summarize_valuation(cluster_median_row, overall_median)

    df.loc[df["cluster"] == cluster_id, "archetype_description"] = short_archetype_description(
        cluster_median_row,
        overall_median,
    )

    print(f"\nCluster {cluster_id} - {ARCHETYPE_NAMES[cluster_id]}")
    print(f"Companies: {company_count}")
    print(f"Share: {company_pct:.2f}%")
    print("Dominant sectors:")
    for sector_name, count in sector_counts.items():
        print(f"  - {sector_name}: {count} ({sector_shares.loc[sector_name]:.1f}%)")

    print("Companies in cluster:")
    print("  - " + " | ".join(companies_sorted))

    print("Feature statistics (mean vs median):")
    for feature in FEATURES:
        mean_value = float(cluster_mean_row[feature])
        median_value = float(cluster_median_row[feature])
        print(f"  - {feature}: {format_feature_pair(mean_value, median_value)}")

    print("Strongest distinguishing characteristics:")
    for item in characteristics:
        print(f"  - {item}")

    print("Archetype support checks:")
    print(f"  - Profitability: {profitability_summary}")
    print(f"  - Capital efficiency: {capital_eff_summary}")
    print(f"  - Leverage: {leverage_summary}")
    print(f"  - Cash flow quality: {cash_flow_summary}")
    print(f"  - Capital intensity: {capex_summary}")
    print(f"  - Valuation: {valuation_summary}")

    archetype_rows.append(
        {
            "cluster": int(cluster_id),
            "archetype": ARCHETYPE_NAMES[cluster_id],
            "company_count": int(company_count),
            "company_percentage": round(company_pct, 2),
            "dominant_sector": f"{dominant_sector} ({dominant_pct:.1f}%)",
            "key_characteristics": " | ".join(characteristics),
            "profitability_summary": profitability_summary,
            "capital_efficiency_summary": capital_eff_summary,
            "leverage_summary": leverage_summary,
            "cash_flow_summary": f"{cash_flow_summary} {capex_summary}",
            "valuation_summary": valuation_summary,
        }
    )


# ============================================================
# OUTPUTS
# ============================================================

OUTPUT_COLUMNS = [
    "company_id",
    "company_name",
    "cluster",
    "sector",
    "archetype",
    "archetype_description",
] + FEATURES

output = df[OUTPUT_COLUMNS].sort_values(["cluster", "company_name"]).copy()

output.to_csv(OUTPUT_FILE, index=False)
profile_mean.to_csv(PROFILE_FILE)
pd.DataFrame(archetype_rows).sort_values("cluster").to_csv(ARCHETYPE_PROFILE_FILE, index=False)


# ============================================================
# VALIDATION CHECKS (POST-OUTPUT)
# ============================================================

written_output = pd.read_csv(OUTPUT_FILE)
assert_condition(len(written_output) == EXPECTED_COMPANIES, f"Output CSV row count must be {EXPECTED_COMPANIES}")
assert_condition(written_output["company_id"].notna().all(), "Output has missing company IDs")
assert_condition(written_output["company_id"].nunique() == EXPECTED_COMPANIES, "Output has duplicate company IDs")
assert_condition(written_output["sector"].notna().all(), "Output has missing sector")
assert_condition(written_output["archetype"].notna().all(), "Output has missing archetype")
assert_condition((written_output["cluster"].value_counts().sum()) == EXPECTED_COMPANIES, "Output cluster counts do not sum to 92")
assert_condition(written_output["cluster"].nunique() == N_CLUSTERS, "Output does not contain exactly 5 clusters")


# ============================================================
# FINAL CONCISE REPORT
# ============================================================

print("\n" + "=" * 70)
print("FINAL CLUSTER ARCHETYPE SUMMARY")
print("=" * 70)

for row in sorted(archetype_rows, key=lambda x: x["cluster"]):
    print(f"\nCluster {row['cluster']} - {row['archetype']}")
    print(f"Companies: {row['company_count']}")
    print(f"Share: {row['company_percentage']:.2f}%")
    print(f"Key characteristics: {row['key_characteristics']}")

print("\nModel metrics:")
print(f"Silhouette Score: {silhouette:.4f}")
print(f"Davies-Bouldin Index: {davies_bouldin:.4f}")
print(f"KMeans Inertia: {kmeans.inertia_:.2f}")

print("\nOutputs written:")
print(OUTPUT_FILE)
print(PROFILE_FILE)
print(ARCHETYPE_PROFILE_FILE)
