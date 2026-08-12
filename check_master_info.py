import pandas as pd

ids = {
    "ULTRACEMCO",
    "UNIONBANK",
    "UNITDSPR",
    "VBL",
    "VEDL",
    "WIPRO",
    "ZOMATO",
    "ZYDUSLIFE",
}

files = [
    "balancesheet.xlsx",
    "cashflow.xlsx",
    "documents.xlsx",
    "profitandloss.xlsx",
    "prosandcons.xlsx",
]

print("8 COMPANY MASTER INFO CHECK")
print("=" * 80)

for filename in files:
    path = "data/raw/" + filename

    try:
        df = pd.read_excel(path, header=1)

        if "company_id" not in df.columns:
            print(f"\n{filename}: NO company_id column")
            continue

        matches = df[df["company_id"].astype(str).isin(ids)]

        print(f"\n{filename}")
        print("-" * 50)

        columns = [
            c for c in [
                "company_id",
                "company_name",
                "name",
                "id",
            ]
            if c in df.columns
        ]

        if columns:
            print(matches[columns].drop_duplicates().to_string(index=False))
        else:
            print("No company-name column found.")
            print("Columns:", df.columns.tolist())

    except Exception as e:
        print(f"\n{filename}: ERROR -> {e}")