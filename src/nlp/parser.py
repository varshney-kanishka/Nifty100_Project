import re
import sqlite3
from pathlib import Path

import pandas as pd

print("=" * 70)
print("DAY 29 - NLP ANALYSIS PARSER")
print("=" * 70)


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

DB_PATH = BASE_DIR / "data" / "database" / "nifty100.db"
OUTPUT_DIR = BASE_DIR / "output"

OUTPUT_DIR.mkdir(exist_ok=True)


# ============================================================
# DATABASE CONNECTION
# ============================================================

conn = sqlite3.connect(DB_PATH)


# ============================================================
# LOAD TABLES
# ============================================================

analysis = pd.read_sql(
    "SELECT * FROM analysis",
    conn
)

ratios = pd.read_sql(
    "SELECT * FROM financial_ratios",
    conn
)


print("\nTables Loaded")
print("Analysis :", len(analysis))
print("Ratios   :", len(ratios))


print("\nAnalysis Columns")
print(analysis.columns.tolist())


print("\nRatio Columns")
print(ratios.columns.tolist())


# ============================================================
# REGEX PATTERNS
# ============================================================

# Examples:
#
# 10 Years: 21%
# 10Years: 11%
# 5 Years: 24%
# 3 Years: 17%
# 1 Year: -2%
#
years_pattern = re.compile(
    r"(\d+)\s*Years?\s*:?\s*(-?[\d.]+)\s*%"
)

# Examples:
#
# TTM: 43%
# TTM: 18%
#
ttm_pattern = re.compile(
    r"TTM\s*:?\s*(-?[\d.]+)\s*%",
    re.IGNORECASE
)

# Examples:
#
# Last Year: 12%
#
last_year_pattern = re.compile(
    r"Last\s+Year\s*:?\s*(-?[\d.]+)\s*%",
    re.IGNORECASE
)


# ============================================================
# TARGET COLUMNS
# ============================================================

target_columns = [
    "compounded_sales_growth",
    "compounded_profit_growth",
    "stock_price_cagr",
    "roe"
]


# ============================================================
# PARSE DATA
# ============================================================

parsed = []
failures = []


for _, row in analysis.iterrows():

    company_id = row["company_id"]

    for column in target_columns:

        text = str(row[column]).strip()

        match = years_pattern.search(text)

        if match:

            period_years = int(match.group(1))
            value_pct = float(match.group(2))

            parsed.append(
                {
                    "company_id": company_id,
                    "metric_type": column,
                    "period_years": period_years,
                    "value_pct": value_pct
                }
            )

            continue

        # ----------------------------------------------------
        # TTM
        # ----------------------------------------------------

        match = ttm_pattern.search(text)

        if match:

            value_pct = float(match.group(1))

            parsed.append(
                {
                    "company_id": company_id,
                    "metric_type": column,
                    "period_years": 0,
                    "value_pct": value_pct
                }
            )

            continue

        # ----------------------------------------------------
        # LAST YEAR
        # ----------------------------------------------------

        match = last_year_pattern.search(text)

        if match:

            value_pct = float(match.group(1))

            parsed.append(
                {
                    "company_id": company_id,
                    "metric_type": column,
                    "period_years": 1,
                    "value_pct": value_pct
                }
            )

            continue

        # ----------------------------------------------------
        # FAILED PARSE
        # ----------------------------------------------------

        failures.append(
            {
                "company_id": company_id,
                "metric_type": column,
                "text": text
            }
        )


# ============================================================
# DATAFRAMES
# ============================================================

parsed_df = pd.DataFrame(parsed)

failure_df = pd.DataFrame(failures)


# ============================================================
# SAVE PARSED DATA
# ============================================================

parsed_path = OUTPUT_DIR / "analysis_parsed.csv"

failure_path = OUTPUT_DIR / "parse_failures.csv"


parsed_df.to_csv(
    parsed_path,
    index=False
)

failure_df.to_csv(
    failure_path,
    index=False
)


print("\nParsed Records :", len(parsed_df))
print("Failed Records :", len(failure_df))


# ============================================================
# PARSE SUMMARY
# ============================================================

if not parsed_df.empty:

    print("\nParsed Metric Summary")

    print(
        parsed_df
        .groupby("metric_type")
        .size()
    )


# ============================================================
# CROSS VALIDATION
# ============================================================

print("\nStarting Cross Validation...")


# The original version incorrectly compared
# sales CAGR against net profit margin.
#
# We will only perform validation when a matching
# computed CAGR column actually exists in financial_ratios.


possible_ratio_columns = {
    "compounded_sales_growth": [
        "sales_cagr",
        "revenue_cagr",
        "compounded_sales_growth"
    ],
    "compounded_profit_growth": [
        "profit_cagr",
        "pat_cagr",
        "net_profit_cagr",
        "compounded_profit_growth"
    ],
    "stock_price_cagr": [
        "stock_price_cagr",
        "price_cagr"
    ],
    "roe": [
        "roe",
        "roe_percentage",
        "roe_pct"
    ]
}


validation_records = []


for metric, possible_columns in possible_ratio_columns.items():

    parsed_metric = parsed_df[
        parsed_df["metric_type"] == metric
    ].copy()

    if parsed_metric.empty:
        continue

    ratio_column = None

    for candidate in possible_columns:

        if candidate in ratios.columns:

            ratio_column = candidate
            break

    if ratio_column is None:

        print(
            f"Skipping validation for {metric}: "
            f"no matching computed column found."
        )

        continue

    ratio_latest = (
        ratios
        .sort_values("year")
        .groupby("company_id")
        .tail(1)
        [
            [
                "company_id",
                ratio_column
            ]
        ]
        .rename(
            columns={
                ratio_column: "computed_value_pct"
            }
        )
    )

    merged = parsed_metric.merge(
        ratio_latest,
        on="company_id",
        how="left"
    )

    merged["difference_pct"] = (
        merged["value_pct"]
        - merged["computed_value_pct"]
    ).abs()

    merged["manual_review"] = (
        merged["difference_pct"] > 5
    )

    merged["metric_type"] = metric

    validation_records.append(
        merged
    )


# ============================================================
# SAVE VALIDATION
# ============================================================

if validation_records:

    validation_df = pd.concat(
        validation_records,
        ignore_index=True
    )

    review_df = validation_df[
        validation_df["manual_review"]
    ].copy()

else:

    validation_df = pd.DataFrame()

    review_df = pd.DataFrame()


validation_path = OUTPUT_DIR / "cagr_manual_review.csv"


review_df.to_csv(
    validation_path,
    index=False
)


print(
    "\nManual Review Required :",
    len(review_df)
)

print(
    validation_path
)


# ============================================================
# CLOSE DATABASE
# ============================================================

conn.close()


# ============================================================
# FINAL SUMMARY
# ============================================================

print("\nFiles Created")

print(parsed_path)
print(failure_path)
print(validation_path)


print("\n" + "=" * 70)
print("DAY 29 COMPLETED")
print("=" * 70)