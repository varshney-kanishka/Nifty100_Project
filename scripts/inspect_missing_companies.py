import pandas as pd
from pathlib import Path

RAW = Path("data/raw")

IDS = {
    "ULTRACEMCO",
    "UNIONBANK",
    "UNITDSPR",
    "VBL",
    "VEDL",
    "WIPRO",
    "ZOMATO",
    "ZYDUSLIFE",
}

FILES = [
    "balancesheet.xlsx",
    "cashflow.xlsx",
    "documents.xlsx",
    "financial_ratios.xlsx",
    "profitandloss.xlsx",
    "sectors.xlsx",
    "stock_prices.xlsx",
]

HEADER_ROWS = {
    "balancesheet.xlsx": 1,
    "cashflow.xlsx": 1,
    "documents.xlsx": 1,
    "profitandloss.xlsx": 1,
    "financial_ratios.xlsx": 0,
    "sectors.xlsx": 0,
    "stock_prices.xlsx": 0,
}

for filename in FILES:

    path = RAW / filename

    print("\n" + "=" * 80)
    print(filename)
    print("=" * 80)

    df = pd.read_excel(
        path,
        header=HEADER_ROWS[filename]
    )

    df.columns = (
        df.columns
        .astype(str)
        .str.strip()
    )

    if "company_id" not in df.columns:
        print("No company_id column")
        continue

    df["company_id"] = (
        df["company_id"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    result = df[df["company_id"].isin(IDS)]

    print("Rows found:", len(result))

    if not result.empty:
        print(result.head(3).to_string(index=False))