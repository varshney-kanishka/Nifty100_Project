"""
Nifty100 Project - Clean Excel -> CSV ETL
"""
from normaliser import normalize_company_id
from pathlib import Path
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]

RAW_FOLDER = BASE_DIR / "data" / "raw"
PROCESSED_FOLDER = BASE_DIR / "data" / "processed"

PROCESSED_FOLDER.mkdir(parents=True, exist_ok=True)


FILES = {
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


def clean_columns(df):
    df.columns = (
        df.columns
        .astype(str)
        .str.strip()
        .str.lower()
        .str.replace(" ", "_", regex=False)
    )
    return df


def clean_company_id(df):
    if "company_id" in df.columns:
        df["company_id"] = (
            df["company_id"]
            .apply(normalize_company_id)
        )

    return df


def clean_ticker(df):
    if "ticker" in df.columns:
        df["ticker"] = (
            df["ticker"]
            .astype("string")
            .str.strip()
            .str.upper()
        )

    return df


def clean_year(df):
    if "year" in df.columns:

        year = (
            df["year"]
            .astype("string")
            .str.strip()
        )

        # Convert values like:
        # 2013.0 -> 2013
        # 2024.5 -> 2024
        year = year.str.replace(
            r"\.0$",
            "",
            regex=True
        )

        # Convert values like:
        # "Mar 2013" -> "2013"
        # "Mar 2024" -> "2024"
        year = year.str.extract(
            r"(\d{4})",
            expand=False
        )

        # Keep only valid 4-digit years
        year = year.where(
            year.str.fullmatch(r"\d{4}"),
            pd.NA
        )

        df["year"] = year

    return df
def clean_null_values(df):
    df = df.replace(
        {
            "Null": pd.NA,
            "NULL": pd.NA,
            "null": pd.NA,
            "None": pd.NA,
            "none": pd.NA,
            "nan": pd.NA,
            "NaN": pd.NA,
            "": pd.NA,
        }
    )
    return df


def process_file(name, header_row):

    source = RAW_FOLDER / f"{name}.xlsx"
    output = PROCESSED_FOLDER / f"{name}.csv"

    if not source.exists():
        print(f"SKIP - missing: {source}")
        return

    print("\n" + "=" * 70)
    print(f"PROCESSING: {name}")
    print("=" * 70)

    df = pd.read_excel(
        source,
        header=header_row
    )

    print("Raw shape:", df.shape)

    df = clean_columns(df)
    df = clean_company_id(df)
    df = clean_ticker(df)
    df = clean_year(df)
    df = clean_null_values(df)

    # Remove completely empty rows only.
    df = df.dropna(how="all").reset_index(drop=True)
    if name in {
    "balancesheet",
    "cashflow",
    "financial_ratios",
    "profitandloss",
    "documents",
}:
     if "company_id" in df.columns and "year" in df.columns:

        before = len(df)

        # For documents, prefer the row containing an annual report URL.
        if name == "documents" and "annual_report" in df.columns:

            # Put rows with an actual annual_report first
            df["_has_report"] = (
                df["annual_report"]
                .notna()
                .astype(int)
            )

            df = (
                df.sort_values(
                    ["company_id", "year", "_has_report"],
                    ascending=[True, True, False]
                )
                .drop_duplicates(
                    subset=["company_id", "year"],
                    keep="first"
                )
                .drop(columns=["_has_report"])
                .reset_index(drop=True)
            )

        else:
            df = (
                df.drop_duplicates(
                    subset=["company_id", "year"],
                    keep="first"
                )
                .reset_index(drop=True)
            )

        removed = before - len(df)

        if removed > 0:
            print(
                f"Removed {removed} duplicate "
                f"(company_id, year) records"
            )

    # Convert accidental unnamed columns away.
    df = df.loc[
        :,
        ~df.columns.astype(str).str.startswith("unnamed")
    ]

    df.to_csv(
        output,
        index=False
    )

    print("Saved:", output)
    print("Shape:", df.shape)
    print("Columns:", df.columns.tolist())

    if "company_id" in df.columns:
        print(
            "Companies:",
            df["company_id"].nunique()
        )


def main():

    for name, header in FILES.items():
        process_file(name, header)

    print("\n" + "=" * 70)
    print("ETL COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()