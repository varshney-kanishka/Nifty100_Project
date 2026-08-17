"""
Nifty100 Project - Clean Excel -> CSV ETL
"""

import re
from pathlib import Path

import pandas as pd

from .normaliser import normalize_company_id

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
    """
    Convert different year formats into integer years.

    Examples:
        2024       -> 2024
        2024.0     -> 2024
        Mar 2024   -> 2024
        Mar-24     -> 2024
        TTM        -> <NA>
    """

    if "year" not in df.columns:
        return df

    def parse_year(value):

        if pd.isna(value):
            return pd.NA

        value = str(value).strip()

        # TTM is NOT an annual year
        if value.upper() == "TTM":
            return pd.NA

        # 2024.0
        match = re.fullmatch(
            r"(19|20)\d{2}\.0",
            value
        )

        if match:
            return int(float(value))

        # 2024
        match = re.fullmatch(
            r"(19|20)\d{2}",
            value
        )

        if match:
            return int(value)

        # Mar 2024 / Mar-2024
        match = re.search(
            r"(19|20)\d{2}",
            value
        )

        if match:
            return int(match.group(0))

        # Mar-24 / Mar 24
        match = re.search(
            r"(?:Mar|March)[\s-]*(\d{2})$",
            value,
            re.IGNORECASE
        )

        if match:
            yy = int(match.group(1))

            if yy <= 49:
                return 2000 + yy
            else:
                return 1900 + yy

        return pd.NA

    df["year"] = (
        df["year"]
        .apply(parse_year)
        .astype("Int64")
    )

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


def remove_non_annual_rows(df, name):

    annual_datasets = {
        "balancesheet",
        "cashflow",
        "financial_ratios",
        "profitandloss",
    }

    if name not in annual_datasets:
        return df

    if "year" not in df.columns:
        return df

    before = len(df)

    df = (
        df.dropna(subset=["year"])
        .reset_index(drop=True)
    )

    removed = before - len(df)

    if removed > 0:
        print(
            f"Removed {removed} non-annual records"
        )

    return df


def remove_duplicates(df, name):

    datasets = {
        "balancesheet",
        "cashflow",
        "financial_ratios",
        "profitandloss",
        "documents",
    }

    if name not in datasets:
        return df

    if "company_id" not in df.columns:
        return df

    if "year" not in df.columns:
        return df

    before = len(df)

    # Documents need special handling because
    # multiple rows may exist for the same company/year.
    if (
        name == "documents"
        and "annual_report" in df.columns
    ):

        df["_has_report"] = (
            df["annual_report"]
            .notna()
            .astype(int)
        )

        df = (
            df.sort_values(
                [
                    "company_id",
                    "year",
                    "_has_report"
                ],
                ascending=[
                    True,
                    True,
                    False
                ]
            )
            .drop_duplicates(
                subset=[
                    "company_id",
                    "year"
                ],
                keep="first"
            )
            .drop(
                columns=["_has_report"]
            )
            .reset_index(drop=True)
        )

    else:

        df = (
            df.drop_duplicates(
                subset=[
                    "company_id",
                    "year"
                ],
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

    # -------------------------
    # CLEANING
    # -------------------------

    df = clean_columns(df)

    df = clean_company_id(df)

    df = clean_ticker(df)

    df = clean_null_values(df)

    df = clean_year(df)

    # Remove completely empty rows
    df = (
        df.dropna(
            how="all"
        )
        .reset_index(drop=True)
    )

    # Remove TTM rows
    df = remove_non_annual_rows(
        df,
        name
    )

    # Remove duplicates
    df = remove_duplicates(
        df,
        name
    )

    # Remove accidental unnamed columns
    df = df.loc[
        :,
        ~df.columns
        .astype(str)
        .str.startswith("unnamed")
    ]

    # -------------------------
    # SAVE
    # -------------------------

    df.to_csv(
        output,
        index=False
    )

    print("Saved:", output)
    print("Shape:", df.shape)
    print(
        "Columns:",
        df.columns.tolist()
    )

    if "company_id" in df.columns:
        print(
            "Companies:",
            df["company_id"].nunique()
        )

    if "year" in df.columns:
        print(
            "Missing years:",
            df["year"].isna().sum()
        )


def main():

    for name, header in FILES.items():
        process_file(
            name,
            header
        )

    print("\n" + "=" * 70)
    print("ETL COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()