import pandas as pd

files = [
    "balancesheet.csv",
    "cashflow.csv",
    "financial_ratios.csv",
    "profitandloss.csv",
]

for filename in files:
    df = pd.read_csv("data/processed/" + filename)

    duplicate_keys = (
        df.groupby(["company_id", "year"])
        .size()
        .reset_index(name="count")
    )

    duplicate_keys = duplicate_keys[
        duplicate_keys["count"] > 1
    ]

    print()
    print("=" * 70)
    print(filename)
    print("=" * 70)

    print("Number of duplicate keys:", len(duplicate_keys))
    print()

    print(duplicate_keys.head(10).to_string(index=False))

    for _, row in duplicate_keys.head(3).iterrows():
        company = row["company_id"]
        year = row["year"]

        print()
        print("---", company, year, "---")

        conflict = df[
            (df["company_id"] == company)
            & (df["year"] == year)
        ]

        print(conflict.to_string(index=False))