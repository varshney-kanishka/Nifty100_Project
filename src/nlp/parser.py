import sqlite3
import re
from pathlib import Path

import pandas as pd

print("=" * 70)
print("DAY 29 - NLP ANALYSIS PARSER")
print("=" * 70)

BASE_DIR = Path(__file__).resolve().parents[2]

DB = BASE_DIR / "data/database/nifty100.db"

OUTPUT = BASE_DIR / "output"

conn = sqlite3.connect(DB)

analysis = pd.read_sql(
    "SELECT * FROM analysis",
    conn,
)

ratios = pd.read_sql(
    "SELECT * FROM financial_ratios",
    conn,
)

print("\nTables Loaded")
print("Analysis :", len(analysis))
print("Ratios   :", len(ratios))
pattern = re.compile(
    r"(\d+)\s*Years?:?\s*([\d.]+)%"
)
parsed = []

failures = []
columns = [
    "compounded_sales_growth",
    "compounded_profit_growth",
    "stock_price_cagr",
    "roe",
]
for _, row in analysis.iterrows():

    company = row["company_id"]

    for col in columns:

        text = str(row[col])

        match = pattern.search(text)

        if match:

            years = int(match.group(1))

            value = float(match.group(2))

            parsed.append(
                {
                    "company_id": company,
                    "metric_type": col,
                    "period_years": years,
                    "value_pct": value,
                }
            )

        else:

            failures.append(
                {
                    "company_id": company,
                    "metric_type": col,
                    "text": text,
                }
            )
parsed_df = pd.DataFrame(parsed)

failure_df = pd.DataFrame(failures)
parsed_df.to_csv(
    OUTPUT / "analysis_parsed.csv",
    index=False,
)

failure_df.to_csv(
    OUTPUT / "parse_failures.csv",
    index=False,
)
print("\nParsed Records :", len(parsed_df))

print("Failed Records :", len(failure_df))

print("\nFiles Created")

print(OUTPUT / "analysis_parsed.csv")

print(OUTPUT / "parse_failures.csv")
failure_df.to_csv(
    OUTPUT / "parse_failures.csv",
    index=False,
)
print("\nStarting Cross Validation...")
sales = parsed_df[
    parsed_df["metric_type"] == "compounded_sales_growth"
].copy()
ratio_latest = (
    ratios.sort_values("year")
    .groupby("company_id")
    .tail(1)
)
validation = sales.merge(
    ratio_latest[
        [
            "company_id",
            "net_profit_margin_pct",
        ]
    ],
    on="company_id",
    how="left",
)
validation["difference_pct"] = (
    validation["value_pct"]
    - validation["net_profit_margin_pct"]
).abs()
validation["manual_review"] = (
    validation["difference_pct"] > 5
)
review = validation[
    validation["manual_review"]
]
review.to_csv(
    OUTPUT / "cagr_manual_review.csv",
    index=False,
)
print("\nManual Review Required :", len(review))

print(
    OUTPUT / "cagr_manual_review.csv"
)

print("\n" + "=" * 70)
print("DAY 29 COMPLETED")
print("=" * 70)
            