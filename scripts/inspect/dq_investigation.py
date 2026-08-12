import pandas as pd
from pathlib import Path

PROCESSED = Path("data/processed")

FILES = [
    "cashflow.csv",
    "profitandloss.csv",
    "financial_ratios.csv",
    "companies.csv",
    "peer_groups.csv",
]

print("=" * 80)
print("DQ INVESTIGATION")
print("=" * 80)

for filename in FILES:

    path = PROCESSED / filename
    df = pd.read_csv(path)

    print("\n" + "=" * 80)
    print(filename)
    print("=" * 80)

    for column in df.columns:

        if column in ["id", "company_id"]:
            continue

        numeric = pd.to_numeric(df[column], errors="coerce")

        missing = int(df[column].isna().sum())

        invalid = int(
            numeric.isna().sum() - missing
        )

        negative = int(
            (numeric < 0).sum()
        )

        print(
            f"{column:35} "
            f"missing={missing:4} "
            f"negative={negative:4} "
            f"invalid={invalid:4}"
        )