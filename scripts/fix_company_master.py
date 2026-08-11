"""
fix_company_master.py

Adds missing company IDs to the master company table.

The existing companies.xlsx contains only 92 companies,
while child datasets contain 100 companies.

This script:
1. Reads companies.csv
2. Finds company IDs appearing in child datasets
3. Finds IDs missing from the master
4. Adds placeholder master records for those IDs
5. Saves a 100-company companies.csv

IMPORTANT:
This does NOT invent financial/company information.
Missing attributes are left blank.
"""

from pathlib import Path
import pandas as pd


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]

PROCESSED_FOLDER = BASE_DIR / "data" / "processed"

MASTER_FILE = PROCESSED_FOLDER / "companies.csv"


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("FIX COMPANY MASTER")
    print("=" * 70)

    # --------------------------------------------------------
    # Check master file
    # --------------------------------------------------------

    if not MASTER_FILE.exists():

        print(
            f"\nERROR: Master file not found:\n"
            f"{MASTER_FILE}"
        )

        return

    # --------------------------------------------------------
    # Read master
    # --------------------------------------------------------

    master_df = pd.read_csv(MASTER_FILE)

    master_df["id"] = (
        master_df["id"]
        .astype("string")
        .str.strip()
        .str.upper()
    )

    master_ids = set(
        master_df["id"]
        .dropna()
    )

    print(
        f"\nExisting master companies: "
        f"{len(master_ids)}"
    )

    # ========================================================
    # FIND ALL CHILD COMPANY IDs
    # ========================================================

    child_ids = set()

    for file in PROCESSED_FOLDER.glob("*.csv"):

        # Don't compare master with itself
        if file.name == "companies.csv":
            continue

        try:

            df = pd.read_csv(file)

        except Exception as e:

            print(
                f"\nCould not read {file.name}: {e}"
            )

            continue

        if "company_id" not in df.columns:
            continue

        ids = (
            df["company_id"]
            .dropna()
            .astype("string")
            .str.strip()
            .str.upper()
        )

        child_ids.update(ids)

    # ========================================================
    # FIND MISSING MASTER IDs
    # ========================================================

    missing_ids = sorted(
        child_ids - master_ids
    )

    print(
        f"\nUnique child companies: "
        f"{len(child_ids)}"
    )

    print(
        f"Missing from master: "
        f"{len(missing_ids)}"
    )

    if not missing_ids:

        print("\nNo missing companies found.")

        return

    print("\nMissing company IDs:")

    for company_id in missing_ids:
        print(f"  {company_id}")

    # ========================================================
    # CREATE PLACEHOLDER ROWS
    # ========================================================

    new_rows = []

    for company_id in missing_ids:

        row = {}

        # Create all columns expected by companies.csv
        for column in master_df.columns:
            row[column] = pd.NA

        # Set master ID
        row["id"] = company_id

        new_rows.append(row)

    new_df = pd.DataFrame(
        new_rows,
        columns=master_df.columns
    )

    # ========================================================
    # APPEND TO MASTER
    # ========================================================

    master_df = pd.concat(
        [
            master_df,
            new_df
        ],
        ignore_index=True
    )

    # --------------------------------------------------------
    # Remove accidental duplicate IDs
    # --------------------------------------------------------

    master_df = (
        master_df
        .drop_duplicates(
            subset=["id"],
            keep="first"
        )
    )

    # --------------------------------------------------------
    # Sort master alphabetically
    # --------------------------------------------------------

    master_df = (
        master_df
        .sort_values("id")
        .reset_index(drop=True)
    )

    # ========================================================
    # SAVE
    # ========================================================

    master_df.to_csv(
        MASTER_FILE,
        index=False
    )

    # ========================================================
    # RESULT
    # ========================================================

    print("\n" + "=" * 70)
    print("MASTER UPDATED")
    print("=" * 70)

    print(
        f"\nMaster companies now: "
        f"{master_df['id'].nunique()}"
    )

    print(
        f"Saved:\n"
        f"{MASTER_FILE}"
    )

    print("\nAdded companies:")

    for company_id in missing_ids:
        print(f"  {company_id}")

    print("\nIMPORTANT:")
    print(
        "The newly added companies have blank "
        "company attributes."
    )


if __name__ == "__main__":
    main()