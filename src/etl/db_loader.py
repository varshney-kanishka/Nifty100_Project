"""
db_loader.py

Sprint 1 - Day 4

Loads all processed CSV files into SQLite database.
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
# Load CSVs into SQLite
# ======================================================
load_audit = []
for file in csv_files:
    print(f"\nLoading : {file.name}")

    try:
        df = pd.read_csv(file, dtype={"year": "string", "Year": "string"})
        df.columns = df.columns.str.strip()

        for year_col in ["year", "Year"]:
            if year_col in df.columns:
                df[year_col] = df[year_col].astype("string").str.replace(
                    r"\.0$",
                    "",
                    regex=True,
                ).str.strip()
                df[year_col] = df[year_col].replace({"nan": pd.NA, "<NA>": pd.NA})

        table_name = file.stem

        df.to_sql(
            table_name,
            engine,
            if_exists="replace",
            index=False,
        )
        load_audit.append(
            {
                "table": table_name,
                "rows_loaded": len(df),
                "rejected_rows": 0,
                "status": "SUCCESS",
            }
        )

        print(f"✅ Loaded {table_name:<20} {len(df)} rows")

    except Exception as e:
        print(f"❌ Error loading {file.name}")
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
        "SELECT name FROM sqlite_master WHERE type='table';",
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
            f"SELECT COUNT(*) AS rows FROM {table}",
            conn,
        )

        print(f"{table:<20} {count.iloc[0,0]} rows")
        fk = pd.read_sql(
        "PRAGMA foreign_key_check;",
        conn,
    )

print("\n" + "=" * 70)
print("Foreign Key Check")
print("=" * 70)

if fk.empty:
    print("✅ No foreign key violations found.")
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

print(f"\n✅ Load audit saved to {audit_path}")

print("\n" + "=" * 70)
print("Database loading completed successfully.")
print("=" * 70)