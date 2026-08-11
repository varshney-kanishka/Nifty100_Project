import pandas as pd

files = [
    "balancesheet.csv",
    "cashflow.csv",
    "financial_ratios.csv",
    "profitandloss.csv",
]

for filename in files:
    path = "data/processed/" + filename
    df = pd.read_csv(path)

    duplicates = df[
        df.duplicated(["company_id", "year"], keep=False)
    ]

    exact_duplicates = duplicates.duplicated(keep=False).sum()

    conflicting = (
        duplicates
        .groupby(["company_id", "year"])
        .filter(lambda x: len(x.drop_duplicates()) > 1)
    )

    print()
    print("===", filename, "===")
    print("Duplicate key rows:", len(duplicates))
    print("Exact duplicate rows:", exact_duplicates)
    print("Conflicting duplicate rows:", len(conflicting))