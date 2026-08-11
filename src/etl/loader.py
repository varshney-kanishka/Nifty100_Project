from pathlib import Path
import pandas as pd

# Import normalization functions
from normaliser import normalize_ticker, normalize_year


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

RAW_FOLDER = BASE_DIR / "data" / "raw"
PROCESSED_FOLDER = BASE_DIR / "data" / "processed"

# Create processed folder if it doesn't exist
PROCESSED_FOLDER.mkdir(parents=True, exist_ok=True)


# ============================================================
# HEADER ROW CONFIGURATION
# ============================================================
#
# 0 = first Excel row contains the column headers
# 1 = second Excel row contains the column headers
#

HEADER_ROWS = {
    "analysis": 1,
    "balancesheet": 1,
    "cashflow": 1,
    "companies": 1,
    "documents": 1,
    "financial_ratios": 0,
    "market_cap": 0,
    "peer_groups": 0,
    "profitandloss": 1,
    "prosandcons": 1,
    "sectors": 0,
    "stock_prices": 0,
}


# ============================================================
# BALANCE SHEET YEAR NORMALIZATION
# ============================================================

def normalize_balancesheet_years(balance_df: pd.DataFrame) -> pd.DataFrame:
    """
    Preserve balance sheet reporting periods while
    normalizing text formatting.
    """

    if balance_df.empty:
        return balance_df

    balance = balance_df.copy()

    if "company_id" in balance.columns:
        balance["company_id"] = (
            balance["company_id"]
            .astype(str)
            .str.strip()
        )

    if "year" in balance.columns:
        balance["year"] = (
            balance["year"]
            .astype("string")
            .str.strip()
        )

    return balance


# ============================================================
# FIND ALL EXCEL FILES
# ============================================================

excel_files = sorted(RAW_FOLDER.glob("*.xlsx"))

print("=" * 70)
print(f"Total Excel Files Found: {len(excel_files)}")
print("=" * 70)


# ============================================================
# PROCESS EACH EXCEL FILE
# ============================================================

for file in excel_files:

    print("\n" + "=" * 70)
    print(f"Reading File : {file.name}")
    print("=" * 70)

    try:

        # ----------------------------------------------------
        # SELECT CORRECT HEADER ROW
        # ----------------------------------------------------

        header_row = HEADER_ROWS.get(file.stem, 0)

        print(f"Header Row : {header_row}")

        df = pd.read_excel(
            file,
            header=header_row
        )

        # ----------------------------------------------------
        # DISPLAY FIRST 5 ROWS
        # ----------------------------------------------------

        print("\nFirst 5 Rows:")
        print(df.head())

        # ----------------------------------------------------
        # DISPLAY SHAPE
        # ----------------------------------------------------

        print("\nShape:")
        print(f"Rows    : {df.shape[0]}")
        print(f"Columns : {df.shape[1]}")

        # ----------------------------------------------------
        # DISPLAY COLUMN NAMES
        # ----------------------------------------------------

        print("\nColumns:")
        print(df.columns.tolist())

        # ----------------------------------------------------
        # DISPLAY MISSING VALUES
        # ----------------------------------------------------

        print("\nMissing Values:")
        print(df.isnull().sum())

        # ====================================================
        # BALANCE SHEET NORMALIZATION
        # ====================================================

        if file.stem == "balancesheet":
            df = normalize_balancesheet_years(df)

        # ====================================================
        # NORMALIZE TICKER COLUMN
        # ====================================================

        if "ticker" in df.columns:

            df["ticker"] = df["ticker"].apply(
                normalize_ticker
            )

        elif "Ticker" in df.columns:

            df["Ticker"] = df["Ticker"].apply(
                normalize_ticker
            )

        # ====================================================
        # NORMALIZE YEAR COLUMN
        # ====================================================

        # These datasets contain reporting periods such as:
        # Dec 2012, Mar 2014, etc.
        #
        # Therefore preserve them as text.

        if file.stem in {
            "balancesheet",
            "profitandloss",
            "cashflow",
            "financial_ratios"
        }:

            if "year" in df.columns:

                df["year"] = (
                    df["year"]
                    .astype("string")
                    .str.strip()
                )

            elif "Year" in df.columns:

                df["Year"] = (
                    df["Year"]
                    .astype("string")
                    .str.strip()
                )

        # ====================================================
        # NORMALIZE NUMERIC YEAR DATASETS
        # ====================================================

        else:

            if "year" in df.columns:

                df["year"] = df["year"].apply(
                    normalize_year
                )

                df["year"] = df["year"].apply(
                    lambda y: (
                        str(int(y))
                        if pd.notna(y)
                        else pd.NA
                    )
                )

                df["year"] = (
                    df["year"]
                    .astype("string")
                    .str.strip()
                )

            elif "Year" in df.columns:

                df["Year"] = df["Year"].apply(
                    normalize_year
                )

                df["Year"] = df["Year"].apply(
                    lambda y: (
                        str(int(y))
                        if pd.notna(y)
                        else pd.NA
                    )
                )

                df["Year"] = (
                    df["Year"]
                    .astype("string")
                    .str.strip()
                )

        # ====================================================
        # SAVE PROCESSED CSV
        # ====================================================

        output_file = (
            PROCESSED_FOLDER /
            f"{file.stem}.csv"
        )

        df.to_csv(
            output_file,
            index=False
        )

        print(f"\nSaved: {output_file}")

    except Exception as e:

        print(f"\nERROR processing {file.name}")
        print(f"Error: {e}")


# ============================================================
# COMPLETION MESSAGE
# ============================================================

print("\n" + "=" * 70)
print("All files processed.")
print("=" * 70)