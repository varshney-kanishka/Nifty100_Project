from pathlib import Path
import pandas as pd

# Import normalization functions
from normaliser import normalize_ticker, normalize_year

# Project paths
BASE_DIR = Path(__file__).resolve().parents[2]
RAW_FOLDER = BASE_DIR / "data" / "raw"
PROCESSED_FOLDER = BASE_DIR / "data" / "processed"

# Create processed folder if it doesn't exist
PROCESSED_FOLDER.mkdir(parents=True, exist_ok=True)


def normalize_balancesheet_years(balance_df: pd.DataFrame) -> pd.DataFrame:
    """Preserve balance sheet reporting periods while normalizing text formatting."""
    if balance_df.empty:
        return balance_df

    balance = balance_df.copy()
    balance["company_id"] = balance["company_id"].astype(str).str.strip()

    if "year" in balance.columns:
        balance["year"] = balance["year"].astype("string").str.strip()

    return balance

# Find all Excel files
excel_files = list(RAW_FOLDER.glob("*.xlsx"))

print("=" * 70)
print(f"Total Excel Files Found: {len(excel_files)}")
print("=" * 70)

# Process each Excel file
for file in excel_files:

    print("\n" + "=" * 70)
    print(f"Reading File : {file.name}")
    print("=" * 70)

    try:
        # Sectors uses a standard first-row header; other files skip a title row.
        header_row = 0 if file.stem == "sectors" else 1
        df = pd.read_excel(file, header=header_row)

        # Display first 5 rows
        print("\nFirst 5 Rows:")
        print(df.head())

        # Display shape
        print("\nShape:")
        print(f"Rows    : {df.shape[0]}")
        print(f"Columns : {df.shape[1]}")

        # Display column names
        print("\nColumns:")
        print(df.columns.tolist())

        # Display missing values
        print("\nMissing Values:")
        print(df.isnull().sum())

        # Preserve reporting period text for balance sheet and profit & loss data.
        if file.stem == "balancesheet":
            df = normalize_balancesheet_years(df)

        # Normalize ticker column (if present)
        if "ticker" in df.columns:
            df["ticker"] = df["ticker"].apply(normalize_ticker)

        elif "Ticker" in df.columns:
            df["Ticker"] = df["Ticker"].apply(normalize_ticker)

        # Normalize year column (if present)
        if file.stem in {"balancesheet", "profitandloss", "cashflow", "financial_ratios"}:
            if "year" in df.columns:
                df["year"] = df["year"].astype("string").str.strip()
            elif "Year" in df.columns:
                df["Year"] = df["Year"].astype("string").str.strip()
        else:
            if "year" in df.columns:
                df["year"] = df["year"].apply(normalize_year)
                df["year"] = df["year"].apply(
                    lambda y: str(int(y)) if pd.notna(y) else pd.NA
                )
                df["year"] = df["year"].astype("string").str.strip()

            elif "Year" in df.columns:
                df["Year"] = df["Year"].apply(normalize_year)
                df["Year"] = df["Year"].apply(
                    lambda y: str(int(y)) if pd.notna(y) else pd.NA
                )
                df["Year"] = df["Year"].astype("string").str.strip()

        # Save processed CSV
        output_file = PROCESSED_FOLDER / f"{file.stem}.csv"
        df.to_csv(output_file, index=False)

        print(f"\n✅ Saved: {output_file}")

    except Exception as e:
        print(f"\n❌ Error processing {file.name}")
        print(e)

print("\n" + "=" * 70)
print("All files processed successfully.")
print("=" * 70)
