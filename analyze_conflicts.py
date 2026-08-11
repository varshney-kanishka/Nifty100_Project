import pandas as pd

files = [
    "cashflow.csv",
    "financial_ratios.csv",
]

for filename in files:

    print("\n" + "=" * 70)
    print(filename)
    print("=" * 70)

    df = pd.read_csv("data/processed/" + filename)

    dup = df[df.duplicated(
        ["company_id", "year"],
        keep=False
    )].copy()

    groups = dup.groupby(["company_id", "year"])

    print("Duplicate keys:", len(groups))

    zero_counts = 0
    nonzero_counts = 0

    for (company, year), group in groups:

        numeric = group.select_dtypes(include="number")

        # Ignore id
        numeric = numeric.drop(
            columns=["id"],
            errors="ignore"
        )

        all_zero = (numeric.fillna(0) == 0).all(axis=1)

        if all_zero.any():
            zero_counts += 1
        else:
            nonzero_counts += 1

    print("Groups containing zero-only record:", zero_counts)
    print("Groups without zero-only record:", nonzero_counts)

    print("\nFirst 10 conflicting groups:\n")

    shown = 0

    for (company, year), group in groups:

        numeric = group.select_dtypes(include="number")
        numeric = numeric.drop(
            columns=["id"],
            errors="ignore"
        )

        all_zero = (numeric.fillna(0) == 0).all(axis=1)

        if not all_zero.all():
            print("\n---", company, year, "---")
            print(group.to_string(index=False))
            shown += 1

        if shown >= 10:
            break