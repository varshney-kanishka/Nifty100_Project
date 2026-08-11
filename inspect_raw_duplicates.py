import pandas as pd
from pathlib import Path

files = [
    "balancesheet.xlsx",
    "cashflow.xlsx",
    "financial_ratios.xlsx",
    "profitandloss.xlsx",
]

RAW = Path("data/raw")

for filename in files:
    path = RAW / filename

    print("\n" + "=" * 70)
    print(filename)
    print("=" * 70)

    xls = pd.ExcelFile(path)

    print("Sheets:")
    print(xls.sheet_names)

    for sheet in xls.sheet_names:
        df = pd.read_excel(path, sheet_name=sheet)

        print("\n--- Sheet:", sheet, "---")
        print("Shape:", df.shape)
        print("Columns:")
        print(df.columns.tolist())

        print("\nFirst 5 rows:")
        print(df.head().to_string(index=False))