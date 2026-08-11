"""
db_loader.py

Nifty100 Project
Loads processed CSV files into SQLite.

Rules:
- companies.csv is the master company dataset.
- Do NOT add missing companies to the master.
- Normalize company IDs before validation.
- Rows whose company_id is not present in the master are rejected.
- Rejected rows are saved separately for audit.
"""

from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine


# ======================================================
# Project Paths
# ======================================================

BASE_DIR = Path(__file__).resolve().parents[2]

PROCESSED_FOLDER = BASE_DIR / "data" / "processed"

DATABASE_FOLDER = BASE_DIR / "data" / "database"
DATABASE_FOLDER.mkdir(parents=True, exist_ok=True)

OUTPUT_FOLDER = BASE_DIR / "output"
OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

REJECTED_FOLDER = OUTPUT_FOLDER / "rejected"
REJECTED_FOLDER.mkdir(parents=True, exist_ok=True)

DB_PATH = DATABASE_FOLDER / "nifty100.db"


# ======================================================
# SQLite Connection
# ======================================================

engine = create_engine(f"sqlite:///{DB_PATH}")


# ======================================================
# Read CSV Files
# ======================================================

csv_files = sorted(PROCESSED_FOLDER.glob("*.csv"))

print("=" * 70)
print(f"Database : {DB_PATH}")
print(f"Total CSV Files : {len(csv_files)}")
print("=" * 70)


# ======================================================
# Load Master Companies First
# ======================================================

companies_file = PROCESSED_FOLDER / "companies.csv"

if not companies_file.exists():
    raise FileNotFoundError(
        f"Master companies file not found: {companies_file}"
    )

companies_df = pd.read_csv(companies_file)

companies_df.columns = (
    companies_df.columns
    .astype(str)
    .str.strip()
)

if "id" not in companies_df.columns:
    raise ValueError(
        "companies.csv must contain an 'id' column."
    )


# Normalize master IDs

companies_df["id"] = (
    companies_df["id"]
    .astype("string")
    .str.strip()
    .str.upper()
)

companies_df = companies_df[
    companies_df["id"].notna()
    & (companies_df["id"] != "")
].copy()


# Master ID set

master_ids = set(companies_df["id"].tolist())

print("\n" + "=" * 70)
print("MASTER COMPANY VALIDATION")
print("=" * 70)

print(f"Master companies : {len(master_ids)}")

if len(master_ids) != 92:
    print(
        f"⚠️ WARNING: Expected 92 master companies, "
        f"found {len(master_ids)}"
    )

# ======================================================
# Load Master Companies
# ======================================================

print("\nLoading : companies.csv")

companies_df.to_sql(
    "companies",
    engine,
    if_exists="replace",
    index=False,
)

print(
    f"✅ Loaded {'companies':<20} "
    f"{len(companies_df)} rows"
)


# ======================================================
# Load Other CSVs
# ======================================================

load_audit = []

# companies already loaded
load_audit.append(
    {
        "table": "companies",
        "rows_loaded": len(companies_df),
        "rejected_rows": 0,
        "status": "SUCCESS",
    }
)


for file in csv_files:

    if file.name == "companies.csv":
        continue

    print(f"\nLoading : {file.name}")

    try:

        # --------------------------------------------------
        # Read CSV
        # --------------------------------------------------

        df = pd.read_csv(
            file,
            dtype={
                "year": "string",
                "Year": "string",
            },
        )

        df.columns = (
            df.columns
            .astype(str)
            .str.strip()
        )


        # --------------------------------------------------
        # Clean year columns
        # --------------------------------------------------

        for year_col in ["year", "Year"]:

            if year_col in df.columns:

                df[year_col] = (
                    df[year_col]
                    .astype("string")
                    .str.replace(
                        r"\.0$",
                        "",
                        regex=True,
                    )
                    .str.strip()
                )

                df[year_col] = df[year_col].replace(
                    {
                        "nan": pd.NA,
                        "<NA>": pd.NA,
                    }
                )


        # --------------------------------------------------
        # Validate company IDs
        # --------------------------------------------------

        rejected_df = pd.DataFrame()

        if "company_id" in df.columns:

            # Normalize company IDs

            df["company_id"] = (
                df["company_id"]
                .astype("string")
                .str.strip()
                .str.upper()
            )


            # Identify invalid IDs

            invalid_mask = (
                df["company_id"].isna()
                | ~df["company_id"].isin(master_ids)
            )


            # Save rejected rows

            rejected_df = df[invalid_mask].copy()


            # Keep only valid rows

            df = df[~invalid_mask].copy()


        # --------------------------------------------------
        # Save rejected rows
        # --------------------------------------------------

        rejected_count = len(rejected_df)

        if rejected_count > 0:

            rejected_path = (
                REJECTED_FOLDER
                / f"{file.stem}_invalid.csv"
            )

            rejected_df.to_csv(
                rejected_path,
                index=False,
            )

            print(
                f"⚠️ Rejected {rejected_count} rows"
            )

            print(
                f"   Saved: {rejected_path}"
            )

        else:

            print("✅ No invalid company IDs")


        # --------------------------------------------------
        # Load valid rows into SQLite
        # --------------------------------------------------

        table_name = file.stem

        df.to_sql(
            table_name,
            engine,
            if_exists="replace",
            index=False,
        )


        # --------------------------------------------------
        # Audit
        # --------------------------------------------------

        load_audit.append(
            {
                "table": table_name,
                "rows_loaded": len(df),
                "rejected_rows": rejected_count,
                "status": "SUCCESS",
            }
        )


        print(
            f"✅ Loaded {table_name:<20} "
            f"{len(df)} rows"
        )


    except Exception as e:

        print(
            f"❌ Error loading {file.name}"
        )

        print(e)

        load_audit.append(
            {
                "table": file.stem,
                "rows_loaded": 0,
                "rejected_rows": 0,
                "status": "FAILED",
            }
        )


# ======================================================
# Verify Tables
# ======================================================

print("\n" + "=" * 70)
print("Tables Created")
print("=" * 70)

with engine.connect() as conn:

    tables = pd.read_sql(
        "SELECT name FROM sqlite_master "
        "WHERE type='table';",
        conn,
    )

print(tables)


# ======================================================
# Verify Row Counts
# ======================================================

print("\n" + "=" * 70)
print("Row Counts")
print("=" * 70)

with engine.connect() as conn:

    for table in tables["name"]:

        count = pd.read_sql(
            f"SELECT COUNT(*) AS rows "
            f"FROM {table}",
            conn,
        )

        print(
            f"{table:<20} "
            f"{count.iloc[0, 0]} rows"
        )


# ======================================================
# Foreign Key Check
# ======================================================

with engine.connect() as conn:

    fk = pd.read_sql(
        "PRAGMA foreign_key_check;",
        conn,
    )


print("\n" + "=" * 70)
print("Foreign Key Check")
print("=" * 70)

if fk.empty:

    print(
        "✅ No foreign key violations found."
    )

else:

    print(fk)


# ======================================================
# Save Load Audit
# ======================================================

audit_df = pd.DataFrame(load_audit)

audit_path = OUTPUT_FOLDER / "load_audit.csv"

audit_df.to_csv(
    audit_path,
    index=False,
)


print("\n" + "=" * 70)
print("Load Audit")
print("=" * 70)

print(audit_df)

print(
    f"\n✅ Load audit saved to {audit_path}"
)


# ======================================================
# Final Summary
# ======================================================

print("\n" + "=" * 70)
print("DATABASE LOADING COMPLETED")
print("=" * 70)

print(
    f"Master companies : {len(master_ids)}"
)

print(
    f"Total rows loaded : "
    f"{audit_df['rows_loaded'].sum()}"
)

print(
    f"Total rows rejected : "
    f"{audit_df['rejected_rows'].sum()}"
)

print(
    "\nRejected files:"
)

for path in sorted(REJECTED_FOLDER.glob("*_invalid.csv")):

    print(
        f"  {path.name}"
    )