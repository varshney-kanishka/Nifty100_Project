"""
manual_review.py

Sprint 1 - Day 6

Manual review of SQLite database.
"""

from pathlib import Path
import random

import pandas as pd
from sqlalchemy import create_engine

# --------------------------------------------------
# Database
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]

DB_PATH = BASE_DIR / "data" / "database" / "nifty100.db"

engine = create_engine(f"sqlite:///{DB_PATH}")

print("=" * 70)
print("DAY 6 - MANUAL REVIEW")
print("=" * 70)

# --------------------------------------------------
# Load companies
# --------------------------------------------------

companies = pd.read_sql(
    "SELECT id, company_name FROM companies",
    engine
)

print(f"\nTotal Companies : {len(companies)}")

# --------------------------------------------------
# Pick 5 random companies
# --------------------------------------------------

sample = companies.sample(5, random_state=42)

print("\nRandom Companies Selected\n")

print(sample)

print("\n" + "=" * 70)
print("YEAR COVERAGE")
print("=" * 70)

for company in sample["id"]:

    print(f"\n{company}")

    query = f"""
    SELECT COUNT(DISTINCT year) AS years
    FROM profitandloss
    WHERE company_id = '{company}'
    """

    years = pd.read_sql(query, engine)

    print(years)

print("\n" + "=" * 70)
print("COMPANIES WITH LESS THAN 5 YEARS OF DATA")
print("=" * 70)

query = """
SELECT
    company_id,
    COUNT(DISTINCT year) AS total_years
FROM profitandloss
GROUP BY company_id
HAVING COUNT(DISTINCT year) < 5
ORDER BY total_years;
"""

few_years = pd.read_sql(query, engine)

if few_years.empty:
    print("✅ No companies found with less than 5 years of data.")
else:
    print(few_years)  

print("\n" + "=" * 70)
print("YEAR RANGE")
print("=" * 70)

query = """
SELECT
    company_id,
    MIN(year) AS first_year,
    MAX(year) AS last_year,
    COUNT(DISTINCT year) AS total_years
FROM profitandloss
GROUP BY company_id
ORDER BY company_id;
"""

year_range = pd.read_sql(query, engine)

print(year_range.head(20))      

print("\n" + "=" * 70)
print("DATA AVAILABILITY CHECK")
print("=" * 70)

tables = [
    "profitandloss",
    "balancesheet",
    "cashflow",
    "financial_ratios",
]

for company in sample["id"]:

    print(f"\nCompany : {company}")

    for table in tables:

        query = f"""
        SELECT COUNT(*) AS records
        FROM {table}
        WHERE company_id = '{company}'
        """

        count = pd.read_sql(query, engine)

        print(f"{table:<20} {count.iloc[0,0]} records")
        
print("\n" + "=" * 70)
print("FOREIGN KEY VERIFICATION")
print("=" * 70)

tables = [
    "analysis",
    "balancesheet",
    "cashflow",
    "documents",
    "financial_ratios",
    "market_cap",
    "peer_groups",
    "profitandloss",
    "prosandcons",
    "sectors",
    "stock_prices",
]

for table in tables:

    query = f"""
SELECT COUNT(*) AS invalid_rows
FROM {table}
WHERE TRIM(company_id) NOT IN (
    SELECT TRIM(id)
    FROM companies
);
"""

    invalid = pd.read_sql(query, engine)

    print(f"{table:<20} {invalid.iloc[0,0]} invalid company_id")        