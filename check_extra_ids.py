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
    "financial_ratios.xlsx",
    "profitandloss.xlsx",
]

for filename in files:
    path = rf"data\raw\{filename}"
    df = pd.read_excel(path)

    found = set()

    for column in df.columns:
        values = (
            df[column]
            .astype(str)
            .str.strip()
            .str.upper()
        )

        found.update(values[values.isin(ids)].tolist())

    print(f"\n=== {filename} ===")

    if found:
        print("Found:", sorted(found))
    else:
        print("None")