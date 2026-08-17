"""
validator.py

Sprint 1 - Day 3

Validates processed CSV files using Data Quality Rules.
"""

from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[2]
PROCESSED_FOLDER = BASE_DIR / "data" / "processed"
OUTPUT_FOLDER = BASE_DIR / "output"

OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)



FINANCIAL_TABLES = [
    "balancesheet.csv",
    "cashflow.csv",
    "financial_ratios.csv",
    "market_cap.csv",
    "profitandloss.csv",
]

VALIDATION_COLUMNS = ["file", "rule", "severity", "message"]


def list_csv_files(directory: Path) -> list[Path]:
    return sorted(directory.glob("*.csv"))


def load_csv(file_path: Path) -> pd.DataFrame:
    """Load a processed CSV using its first row as the header."""
    df = pd.read_csv(file_path, header=0)

    df.columns = df.columns.astype(str).str.strip()

    return df


def validate_companies(df: pd.DataFrame, file_name: str) -> list[dict]:
    results: list[dict] = []

    if "id" not in df.columns:
        results.append(
            {
                "file": file_name,
                "rule": "DQ-01",
                "severity": "CRITICAL",
                "message": "Missing required column 'id' for companies.csv",
            }
        )
        return results

    duplicate_rows = df[df["id"].duplicated(keep=False)]
    if not duplicate_rows.empty:
        results.append(
            {
                "file": file_name,
                "rule": "DQ-01",
                "severity": "CRITICAL",
                "message": f"{len(duplicate_rows)} duplicate company IDs found",
            }
        )

    return results


def validate_financial_table(df: pd.DataFrame, file_name: str) -> list[dict]:
    results: list[dict] = []

    required_columns = ["company_id", "year"]

    missing_columns = [col for col in required_columns if col not in df.columns]

    if missing_columns:
        results.append(
            {
                "file": file_name,
                "rule": "DQ-02",
                "severity": "CRITICAL",
                "message": f"Missing required columns: {', '.join(missing_columns)}",
            }
        )
        return results

    duplicate_rows = df[df.duplicated(subset=["company_id", "year"], keep=False)]

    if duplicate_rows.empty:
        print("✅ DQ-02 Passed")
    else:
        print("❌ DQ-02 Failed")

        results.append(
            {
                "file": file_name,
                "rule": "DQ-02",
                "severity": "CRITICAL",
                "message": f"{len(duplicate_rows)} duplicate (company_id, year) combinations",
            }
        )

    return results


def validate_primary_key(df: pd.DataFrame, file_name: str) -> list[dict]:
    results: list[dict] = []

    # Check if id column exists
    if "id" not in df.columns:
        results.append(
            {
                "file": file_name,
                "rule": "DQ-03",
                "severity": "CRITICAL",
                "message": "Missing required column: id",
            }
        )
        return results

    # Count missing primary keys
    missing_ids = df["id"].isna().sum()

    if missing_ids > 0:
        results.append(
            {
                "file": file_name,
                "rule": "DQ-03",
                "severity": "CRITICAL",
                "message": f"{missing_ids} missing primary key values",
            }
        )
    else:
        print("✅ DQ-03 Passed")

    return results


def validate_foreign_key(df, file_name, valid_company_ids):
    results = []

    if "company_id" not in df.columns:
        return results

    invalid_ids = (
        df.loc[~df["company_id"].isin(valid_company_ids), "company_id"]
        .dropna()
        .unique()
    )

    if len(invalid_ids) == 0:
        print("✅ DQ-04 Passed")
        return results

    print("❌ DQ-04 Failed")
    print("Invalid company IDs:", invalid_ids)

    results.append(
        {
            "file": file_name,
            "rule": "DQ-04",
            "severity": "CRITICAL",
            "message": f"{len(invalid_ids)} invalid company_id values found",
        }
    )

    return results


def validate_company_id(df: pd.DataFrame, file_name: str) -> list[dict]:
    results = []

    if "company_id" not in df.columns:
        return results

    missing = df["company_id"].isna().sum()

    if missing > 0:
        print("❌ DQ-05 Failed")

        results.append(
            {
                "file": file_name,
                "rule": "DQ-05",
                "severity": "CRITICAL",
                "message": f"{missing} missing company_id values",
            }
        )
    else:
        print("✅ DQ-05 Passed")

    return results


def validate_year(df: pd.DataFrame, file_name: str) -> list[dict]:
    results = []

    if "year" not in df.columns:
        return results

    missing = df["year"].isna().sum()

    if missing > 0:
        print("❌ DQ-06 Failed")

        results.append(
            {
                "file": file_name,
                "rule": "DQ-06",
                "severity": "CRITICAL",
                "message": f"{missing} missing year values",
            }
        )
    else:
        print("✅ DQ-06 Passed")

    return results


def validate_empty_strings(df: pd.DataFrame, file_name: str) -> list[dict]:
    results = []

    object_cols = df.select_dtypes(include=["object", "string"]).columns

    empty = 0

    for col in object_cols:
        empty += (df[col].astype(str).str.strip() == "").sum()

    if empty > 0:
        print("❌ DQ-07 Failed")

        results.append(
            {
                "file": file_name,
                "rule": "DQ-07",
                "severity": "WARNING",
                "message": f"{empty} empty string values found",
            }
        )
    else:
        print("✅ DQ-07 Passed")

    return results


def validate_missing_values(df: pd.DataFrame, file_name: str) -> list[dict]:
    results = []

    missing_by_column = df.isna().sum()
    missing_by_column = missing_by_column[missing_by_column > 0]

    if not missing_by_column.empty:
        total_missing = int(missing_by_column.sum())

        print("❌ DQ-08 Failed")
        print("Missing values by column:")

        for column, count in missing_by_column.items():
            print(f"   {column}: {count}")

        results.append(
            {
                "file": file_name,
                "rule": "DQ-08",
                "severity": "WARNING",
                "message": (
                    f"{total_missing} missing values found "
                    f"across {len(missing_by_column)} columns"
                ),
            }
        )

    else:
        print("✅ DQ-08 Passed")

    return results

def validate_duplicate_rows(df: pd.DataFrame, file_name: str) -> list[dict]:
    results = []

    duplicate_rows = df[df.duplicated(keep=False)]

    if not duplicate_rows.empty:
        print("❌ DQ-09 Failed")

        results.append(
            {
                "file": file_name,
                "rule": "DQ-09",
                "severity": "WARNING",
                "message": f"{len(duplicate_rows)} duplicate rows found",
            }
        )
    else:
        print("✅ DQ-09 Passed")

    return results


def validate_negative_values(df: pd.DataFrame, file_name: str) -> list[dict]:
    results = []

    # Columns where negative values are legitimate
    allowed_negative_columns = {
        "cashflow.csv": [
            "operating_activity",
            "investing_activity",
            "financing_activity",
            "net_cash_flow",
        ],

        "financial_ratios.csv": [
            "net_profit_margin_pct",
            "operating_profit_margin_pct",
            "return_on_equity_pct",
            "interest_coverage",
            "free_cash_flow_cr",
            "earnings_per_share",
            "dividend_payout_ratio_pct",
            "cash_from_operations_cr",
        ],

        "profitandloss.csv": [
            "operating_profit",
            "opm_percentage",
            "other_income",
            "interest",
            "profit_before_tax",
            "tax_percentage",
            "net_profit",
            "eps",
            "dividend_payout",
            "expenses",
        ],

        "balancesheet.csv": [
            "reserves",
        ],
    }

    # Numeric columns
    numeric_cols = df.select_dtypes(include="number").columns.tolist()

    # Never check ID/year for negative values
    numeric_cols = [
        col for col in numeric_cols
        if col not in ["id", "year"]
    ]

    # Remove columns where negatives are expected
    allowed = allowed_negative_columns.get(file_name, [])

    check_cols = [
        col for col in numeric_cols
        if col not in allowed
    ]

    negative_count = 0

    for col in check_cols:
        negative_count += int((df[col] < 0).sum())

    if negative_count > 0:
        print("❌ DQ-10 Failed")

        results.append(
            {
                "file": file_name,
                "rule": "DQ-10",
                "severity": "WARNING",
                "message": f"{negative_count} negative numeric values found",
            }
        )
    else:
        print("✅ DQ-10 Passed")

    return results


def validate_future_dates(df: pd.DataFrame, file_name: str) -> list[dict]:
    results = []

    if "date" not in df.columns:
        return results

    dates = pd.to_datetime(df["date"], errors="coerce")

    future = (dates > pd.Timestamp.today()).sum()

    if future > 0:
        print("❌ DQ-11 Failed")

        results.append(
            {
                "file": file_name,
                "rule": "DQ-11",
                "severity": "WARNING",
                "message": f"{future} future dates found",
            }
        )
    else:
        print("✅ DQ-11 Passed")

    return results


def validate_year_format(df: pd.DataFrame, file_name: str) -> list[dict]:
    results = []

    if "year" not in df.columns:
        return results

    invalid = df["year"].astype(str).str.strip().eq("").sum()

    if invalid > 0:
        print("❌ DQ-12 Failed")

        results.append(
            {
                "file": file_name,
                "rule": "DQ-12",
                "severity": "WARNING",
                "message": f"{invalid} invalid year values found",
            }
        )
    else:
        print("✅ DQ-12 Passed")

    return results


def validate_data_types(df: pd.DataFrame, file_name: str) -> list[dict]:
    results = []

    numeric_columns = df.select_dtypes(
        include=["int64", "float64", "Int64", "Float64"]
    ).columns

    invalid = 0

    for col in numeric_columns:
        original = df[col]

        # Only test values that are NOT already missing
        non_missing = original.dropna()

        converted = pd.to_numeric(non_missing, errors="coerce")

        invalid += converted.isna().sum()

    if invalid > 0:
        print("❌ DQ-13 Failed")

        results.append(
            {
                "file": file_name,
                "rule": "DQ-13",
                "severity": "WARNING",
                "message": f"{invalid} invalid numeric values found",
            }
        )
    else:
        print("✅ DQ-13 Passed")

    return results

def validate_date_format(df: pd.DataFrame, file_name: str) -> list[dict]:
    results = []

    if "date" not in df.columns:
        return results

    invalid_dates = pd.to_datetime(df["date"], errors="coerce").isna().sum()

    if invalid_dates > 0:
        print("❌ DQ-14 Failed")

        results.append(
            {
                "file": file_name,
                "rule": "DQ-14",
                "severity": "WARNING",
                "message": f"{invalid_dates} invalid date values found",
            }
        )
    else:
        print("✅ DQ-14 Passed")

    return results


def validate_duplicate_columns(df: pd.DataFrame, file_name: str) -> list[dict]:
    results = []

    duplicate_columns = df.columns[df.columns.duplicated()]

    if len(duplicate_columns) > 0:
        print("❌ DQ-15 Failed")

        results.append(
            {
                "file": file_name,
                "rule": "DQ-15",
                "severity": "WARNING",
                "message": f"{len(duplicate_columns)} duplicate column names found",
            }
        )
    else:
        print("✅ DQ-15 Passed")

    return results


def validate_empty_dataset(df: pd.DataFrame, file_name: str) -> list[dict]:
    results = []

    if df.empty:
        print("❌ DQ-16 Failed")

        results.append(
            {
                "file": file_name,
                "rule": "DQ-16",
                "severity": "CRITICAL",
                "message": "Dataset is empty",
            }
        )
    else:
        print("✅ DQ-16 Passed")

    return results


def summarize_dataset(df: pd.DataFrame) -> str:
    summary_lines = [
        "First 5 Rows:",
        str(df.head()),
        "\nShape:",
        f"Rows    : {df.shape[0]}",
        f"Columns : {df.shape[1]}",
        "\nColumns:",
        str(df.columns.tolist()),
        "\nMissing Values:",
        str(df.isnull().sum()),
    ]
    return "\n".join(summary_lines)


def validate_file(file_path: Path, valid_company_ids: set) -> list[dict]:

    print("\n" + "=" * 70)
    print(f"Reading File : {file_path.name}")
    print("=" * 70)

    try:
        df = load_csv(file_path)
    except Exception as error:  # noqa: BLE001
        print(f"\n❌ Error reading {file_path.name}")
        print(error)
        return [
            {
                "file": file_path.name,
                "rule": "LOAD",
                "severity": "CRITICAL",
                "message": str(error),
            }
        ]

    results: list[dict] = []

    # DQ-01
    if file_path.name == "companies.csv":
        results.extend(validate_companies(df, file_path.name))

    # DQ-02
    if file_path.name in FINANCIAL_TABLES:
        results.extend(validate_financial_table(df, file_path.name))

        # DQ-03
    results.extend(validate_primary_key(df, file_path.name))

    # DQ-04
    results.extend(validate_foreign_key(df, file_path.name, valid_company_ids))
    # DQ-05
    results.extend(validate_company_id(df, file_path.name))

    # DQ-06
    results.extend(validate_year(df, file_path.name))

    # DQ-07
    results.extend(validate_empty_strings(df, file_path.name))

    # DQ-08
    results.extend(validate_missing_values(df, file_path.name))

    # DQ-09
    results.extend(validate_duplicate_rows(df, file_path.name))

    # DQ-10
    results.extend(validate_negative_values(df, file_path.name))

    # DQ-11
    results.extend(validate_future_dates(df, file_path.name))

    # DQ-12
    results.extend(validate_year_format(df, file_path.name))

    # DQ-13
    results.extend(validate_data_types(df, file_path.name))

    # DQ-14
    results.extend(validate_date_format(df, file_path.name))

    # DQ-15
    results.extend(validate_duplicate_columns(df, file_path.name))

    # DQ-16
    results.extend(validate_empty_dataset(df, file_path.name))

    print(summarize_dataset(df))
    return results


def run_validation() -> pd.DataFrame:
    csv_files = list_csv_files(PROCESSED_FOLDER)
    companies_df = load_csv(PROCESSED_FOLDER / "companies.csv")
    valid_company_ids = set(companies_df["id"].dropna())
    print("=" * 70)
    print(f"Total CSV Files : {len(csv_files)}")
    print("=" * 70)

    validation_results: list[dict] = []
    for csv_file in csv_files:
        validation_results.extend(validate_file(csv_file, valid_company_ids))

    report = pd.DataFrame(validation_results, columns=VALIDATION_COLUMNS)

    print("\n" + "=" * 70)
    print("Validation Report")
    print("=" * 70)

    if report.empty:
        print("✅ No validation failures found.")
    else:
        print(report)

    report_path = OUTPUT_FOLDER / "validation_failures.csv"
    report.to_csv(report_path, index=False)
    print(f"\n✅ Saved validation report to {report_path}")

    return report


if __name__ == "__main__":
    run_validation()
