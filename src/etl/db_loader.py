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

for file in csv_files:

    print(f"\nLoading : {file.name}")

    try:

        if file.name in [
            "analysis.csv",
            "balancesheet.csv",
            "cashflow.csv",
            "companies.csv",
            "documents.csv",
            "profitandloss.csv",
            "prosandcons.csv",
        ]:
            df = pd.read_csv(file, header=1)
        else:
            df = pd.read_csv(file)

        df.columns = df.columns.str.strip()

        table_name = file.stem

        df.to_sql(
            table_name,
            engine,
            if_exists="replace",
            index=False,
        )

        print(f"✅ Loaded {table_name:<20} {len(df)} rows")

    except Exception as e:
        print(f"❌ Error loading {file.name}")
        print(e)

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

print("\n" + "=" * 70)
print("Database loading completed successfully.")
print("=" * 70)