import pandas as pd
from pathlib import Path

PROCESSED = Path("data/processed")

FILES = [
    "cashflow.csv",
    "profitandloss.csv",
]

for filename in FILES:

    path = PROCESSED / filename
    df = pd.read_csv(path)

    print("\n" + "=" * 80)
    print(filename)
    print("=" * 80)

    missing = df[df["year"].isna()]

    print("Missing year rows:", len(missing))

    if not missing.empty:
        print(missing.to_string(index=False))
