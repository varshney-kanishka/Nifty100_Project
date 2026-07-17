"""
validator.py

Sprint 1 - Day 3

Validates processed CSV files using Data Quality Rules.
"""

from pathlib import Path
import pandas as pd

# ======================================================
# Folders
# ======================================================

PROCESSED_FOLDER = Path("data/processed")
OUTPUT_FOLDER = Path("output")

OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

# ======================================================
# Files having title row
# ======================================================

SPECIAL_FILES = [
    "analysis.csv",
    "balancesheet.csv",
    "cashflow.csv",
    "companies.csv",
    "documents.csv",
    "profitandloss.csv",
    "prosandcons.csv"
]

# ======================================================
# Files for DQ-02
# ======================================================

DQ02_FILES = [
    "balancesheet",
    "cashflow",
    "financial_ratios",
    "market_cap",
    "profitandloss"
]

# ======================================================
# Read all CSV files
# ======================================================

csv_files = list(PROCESSED_FOLDER.glob("*.csv"))

validation_results = []

print("=" * 70)
print(f"Total CSV Files : {len(csv_files)}")
print("=" * 70)

# ======================================================
# Process each CSV
# ======================================================

for file in csv_files:

    print("\n" + "=" * 70)
    print(f"Reading File : {file.name}")
    print("=" * 70)

    try:

        # --------------------------------------------------
        # Read CSV
        # --------------------------------------------------

        if file.name in SPECIAL_FILES:
            df = pd.read_csv(file, header=1)
        else:
            df = pd.read_csv(file)

        # --------------------------------------------------
        # DQ-01 : Primary Key Uniqueness
        # --------------------------------------------------

        if file.name == "companies.csv":

            if "id" in df.columns:

                duplicate_rows = df[df["id"].duplicated()]

                if duplicate_rows.empty:

                    print("\n✅ DQ-01 Passed")
                    print("No duplicate company IDs found.")

                else:

                    print("\n❌ DQ-01 Failed")

                    validation_results.append({

                        "file": file.name,
                        "rule": "DQ-01",
                        "severity": "CRITICAL",
                        "message": f"{len(duplicate_rows)} duplicate company IDs found"

                    })

        # --------------------------------------------------
        # DQ-02 : Duplicate (company_id, year)
        # --------------------------------------------------

        if file.stem in DQ02_FILES:

            if "company_id" in df.columns and "year" in df.columns:

                duplicate_rows = df[
                    df.duplicated(
                        subset=["company_id", "year"],
                        keep=False
                    )
                ]

                if duplicate_rows.empty:

                    print("\n✅ DQ-02 Passed")

                else:

                    print("\n❌ DQ-02 Failed")

                    validation_results.append({

                        "file": file.name,
                        "rule": "DQ-02",
                        "severity": "CRITICAL",
                        "message": f"{len(duplicate_rows)} duplicate (company_id, year) combinations"

                    })

        # --------------------------------------------------
        # Dataset Information
        # --------------------------------------------------

        print("\nFirst 5 Rows:")
        print(df.head())

        print("\nShape:")
        print(f"Rows    : {df.shape[0]}")
        print(f"Columns : {df.shape[1]}")

        print("\nColumns:")
        print(df.columns.tolist())

        print("\nMissing Values:")
        print(df.isnull().sum())

    except Exception as e:

        print(f"\n❌ Error reading {file.name}")
        print(e)

# ======================================================
# Validation Report
# ======================================================

report = pd.DataFrame(validation_results)

print("\n" + "=" * 70)
print("Validation Report")
print("=" * 70)

if report.empty:

    print("✅ No validation failures found.")

else:

    print(report)

# ======================================================
# Save Validation Report
# ======================================================

report.to_csv(
    OUTPUT_FOLDER / "validation_failures.csv",
    index=False
)

print("\n✅ validation_failures.csv saved successfully.")