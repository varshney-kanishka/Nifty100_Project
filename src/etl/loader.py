from pathlib import Path
import pandas as pd

# Import normalization functions
from normaliser import normalize_ticker, normalize_year

# Folder paths
RAW_FOLDER = Path("data/raw")
PROCESSED_FOLDER = Path("data/processed")

# Create processed folder if it doesn't exist
PROCESSED_FOLDER.mkdir(parents=True, exist_ok=True)

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
        # Read Excel
        df = pd.read_excel(file)

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

        # Normalize ticker column (if present)
        if "ticker" in df.columns:
            df["ticker"] = df["ticker"].apply(normalize_ticker)

        elif "Ticker" in df.columns:
            df["Ticker"] = df["Ticker"].apply(normalize_ticker)

        # Normalize year column (if present)
        if "year" in df.columns:
            df["year"] = df["year"].apply(normalize_year)

        elif "Year" in df.columns:
            df["Year"] = df["Year"].apply(normalize_year)

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