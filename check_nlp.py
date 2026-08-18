import pandas as pd
from pathlib import Path

files = [
    "output/analysis_parsed.csv",
    "output/pros_cons_generated.csv",
]

for file in files:
    print("\n" + "=" * 70)
    print(file)
    print("=" * 70)

    path = Path(file)

    if not path.exists():
        print("FILE NOT FOUND")
        continue

    df = pd.read_csv(path)

    print("Rows:", len(df))
    print("Columns:", df.columns.tolist())
    print("\nUnique company IDs:")

    if "company_id" in df.columns:
        print(df["company_id"].nunique())
        print(sorted(df["company_id"].dropna().unique()))

    print("\nFirst 10 rows:")
    print(df.head(10).to_string(index=False))