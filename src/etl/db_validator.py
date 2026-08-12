"""
Nifty100 Project - Database Validator

Sprint 1 - Day 5/6

Validates the SQLite database after ETL loading.

Checks:
1. Database tables
2. Row counts
3. Table schemas
4. Sample data
5. Duplicate primary IDs
6. Master company count
7. Invalid company_id values
8. Missing company_id values
9. Duplicate (company_id, year) records
10. Stock-price coverage
11. Market-cap coverage
12. Sector coverage
13. Final validation summary

IMPORTANT:
- The companies table is the master dataset.
- Do NOT add missing companies to the master dataset.
- Source-level identifier corrections belong in normalization.py.
"""

from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine


# ======================================================
# PROJECT PATHS
# ======================================================

BASE_DIR = Path(__file__).resolve().parents[2]

DB_PATH = BASE_DIR / "data" / "database" / "nifty100.db"

engine = create_engine(f"sqlite:///{DB_PATH}")


# ======================================================
# TABLE DEFINITIONS
# ======================================================

CHILD_TABLES = [
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

YEAR_TABLES = [
    "balancesheet",
    "cashflow",
    "documents",
    "financial_ratios",
    "market_cap",
    "profitandloss",
]

EXPECTED_TABLES = [
    "companies",
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


# ======================================================
# HELPER
# ======================================================

def print_section(title):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


# ======================================================
# CHECK DATABASE EXISTS
# ======================================================

print_section("DATABASE CHECK")

print(f"Database path: {DB_PATH}")

if not DB_PATH.exists():
    print("❌ Database does not exist.")
    raise SystemExit(1)

if DB_PATH.stat().st_size == 0:
    print("❌ Database file is empty.")
    raise SystemExit(1)

print("✅ Database exists")
print(f"Size: {DB_PATH.stat().st_size:,} bytes")


# ======================================================
# GET DATABASE TABLES
# ======================================================

with engine.connect() as conn:

    tables = pd.read_sql(
        """
        SELECT name
        FROM sqlite_master
        WHERE type='table'
        ORDER BY name;
        """,
        conn,
    )


print_section("DATABASE TABLES")

print(tables)


database_tables = set(tables["name"].tolist())


# ======================================================
# EXPECTED TABLE CHECK
# ======================================================

print_section("EXPECTED TABLE CHECK")

missing_tables = []

for table in EXPECTED_TABLES:

    if table in database_tables:
        print(f"✅ {table}")
    else:
        print(f"❌ {table} - MISSING")
        missing_tables.append(table)

if not missing_tables:
    print("\n✅ All expected tables exist.")
else:
    print(f"\n❌ Missing tables: {missing_tables}")


# ======================================================
# ROW COUNTS
# ======================================================

print_section("ROW COUNTS")

row_counts = {}

with engine.connect() as conn:

    for table in tables["name"]:

        rows = pd.read_sql(
            f"""
            SELECT COUNT(*) AS total
            FROM "{table}";
            """,
            conn,
        )

        count = int(rows.iloc[0]["total"])

        row_counts[table] = count

        print(f"{table:<20} {count}")


# ======================================================
# TABLE SCHEMAS
# ======================================================

print_section("TABLE SCHEMAS")

with engine.connect() as conn:

    for table in tables["name"]:

        print(f"\n{table}")

        schema = pd.read_sql(
            f'PRAGMA table_info("{table}");',
            conn,
        )

        print(
            schema[
                [
                    "name",
                    "type",
                ]
            ].to_string(index=False)
        )


# ======================================================
# SAMPLE COMPANY DATA
# ======================================================

print_section("SAMPLE COMPANY DATA")

query = """
SELECT
    id,
    company_name
FROM companies
LIMIT 10;
"""

print(
    pd.read_sql(
        query,
        engine,
    ).to_string(index=False)
)


# ======================================================
# TOP MARKET CAP COMPANIES
# ======================================================

print_section("TOP MARKET CAP DATA")

query = """
SELECT
    company_id,
    market_cap_crore
FROM market_cap
ORDER BY market_cap_crore DESC
LIMIT 10;
"""

print(
    pd.read_sql(
        query,
        engine,
    ).to_string(index=False)
)


# ======================================================
# STOCK PRICE COVERAGE
# ======================================================

print_section("STOCK PRICE COVERAGE")

query = """
SELECT
    company_id,
    COUNT(*) AS records
FROM stock_prices
GROUP BY company_id
ORDER BY records DESC
LIMIT 10;
"""

print(
    pd.read_sql(
        query,
        engine,
    ).to_string(index=False)
)


# ======================================================
# PRIMARY KEY / ID DUPLICATE CHECK
# ======================================================

print_section("PRIMARY KEY CHECK")

duplicate_pk_tables = []

with engine.connect() as conn:

    for table in tables["name"]:

        columns = pd.read_sql(
            f'PRAGMA table_info("{table}");',
            conn,
        )

        if "id" not in columns["name"].values:
            continue

        duplicate = pd.read_sql(
            f"""
            SELECT COUNT(*) AS duplicate_groups
            FROM (
                SELECT id
                FROM "{table}"
                WHERE id IS NOT NULL
                GROUP BY id
                HAVING COUNT(*) > 1
            );
            """,
            conn,
        )

        duplicate_count = int(
            duplicate.iloc[0]["duplicate_groups"]
        )

        if duplicate_count == 0:

            print(
                f"✅ {table:<20} "
                f"0 duplicate IDs"
            )

        else:

            print(
                f"❌ {table:<20} "
                f"{duplicate_count} duplicate IDs"
            )

            duplicate_pk_tables.append(
                table
            )


# ======================================================
# MASTER COMPANY VALIDATION
# ======================================================

print_section("MASTER COMPANY VALIDATION")

with engine.connect() as conn:

    master = pd.read_sql(
        """
        SELECT id
        FROM companies
        WHERE id IS NOT NULL;
        """,
        conn,
    )


master_ids = set(
    master["id"]
    .astype(str)
    .str.strip()
    .str.upper()
)


print(
    f"Master companies: {len(master_ids)}"
)

if len(master_ids) == 92:
    print("✅ Master company count is 92")
else:
    print(
        f"⚠️ Expected 92 companies, "
        f"found {len(master_ids)}"
    )


# ======================================================
# INVALID COMPANY ID CHECK
# ======================================================

print_section("INVALID COMPANY ID CHECK")

total_invalid = 0

invalid_summary = []

with engine.connect() as conn:

    for table in CHILD_TABLES:

        if table not in database_tables:
            continue

        query = f"""
        SELECT
            company_id,
            COUNT(*) AS records
        FROM "{table}"
        WHERE company_id IS NOT NULL
          AND TRIM(company_id) != ''
          AND UPPER(TRIM(company_id)) NOT IN (
              SELECT UPPER(TRIM(id))
              FROM companies
              WHERE id IS NOT NULL
          )
        GROUP BY company_id
        ORDER BY records DESC;
        """

        invalid = pd.read_sql(
            query,
            conn,
        )

        print(f"\n## {table}")

        if invalid.empty:

            print(
                "✅ No invalid company IDs"
            )

            continue

        print(
            invalid.to_string(
                index=False
            )
        )

        table_invalid = int(
            invalid["records"].sum()
        )

        total_invalid += table_invalid

        invalid_summary.append(
            {
                "table": table,
                "invalid_rows": table_invalid,
            }
        )

        print(
            f"Total invalid rows: "
            f"{table_invalid}"
        )


print("\n" + "=" * 70)
print(
    f"TOTAL INVALID ROWS: "
    f"{total_invalid}"
)
print("=" * 70)


# ======================================================
# MISSING COMPANY ID CHECK
# ======================================================

print_section("MISSING COMPANY ID CHECK")

missing_company_ids = []

with engine.connect() as conn:

    for table in CHILD_TABLES:

        if table not in database_tables:
            continue

        query = f"""
        SELECT COUNT(*) AS missing_ids
        FROM "{table}"
        WHERE company_id IS NULL
           OR TRIM(company_id) = '';
        """

        result = pd.read_sql(
            query,
            conn,
        )

        missing = int(
            result.iloc[0]["missing_ids"]
        )

        if missing == 0:

            print(
                f"✅ {table:<20} "
                f"0 missing company_id"
            )

        else:

            print(
                f"❌ {table:<20} "
                f"{missing} missing company_id"
            )

            missing_company_ids.append(
                {
                    "table": table,
                    "missing_rows": missing,
                }
            )


# ======================================================
# DUPLICATE COMPANY + YEAR CHECK
# ======================================================

print_section(
    "DUPLICATE COMPANY + YEAR CHECK"
)

duplicate_company_year_tables = []

with engine.connect() as conn:

    for table in YEAR_TABLES:

        if table not in database_tables:
            continue

        query = f"""
        SELECT
            company_id,
            year,
            COUNT(*) AS records
        FROM "{table}"
        GROUP BY company_id, year
        HAVING COUNT(*) > 1
        ORDER BY records DESC;
        """

        duplicates = pd.read_sql(
            query,
            conn,
        )

        if duplicates.empty:

            print(
                f"✅ {table:<20} "
                f"No duplicate company-year records"
            )

        else:

            print(
                f"❌ {table:<20} "
                f"Duplicate records found"
            )

            print(
                duplicates.to_string(
                    index=False
                )
            )

            duplicate_company_year_tables.append(
                table
            )


# ======================================================
# COMPANY COVERAGE BY TABLE
# ======================================================

print_section("COMPANY COVERAGE BY TABLE")

coverage_results = []

with engine.connect() as conn:

    for table in CHILD_TABLES:

        if table not in database_tables:
            continue

        query = f"""
        SELECT COUNT(
            DISTINCT UPPER(TRIM(company_id))
        ) AS companies
        FROM "{table}"
        WHERE company_id IS NOT NULL
          AND TRIM(company_id) != '';
        """

        result = pd.read_sql(
            query,
            conn,
        )

        company_count = int(
            result.iloc[0]["companies"]
        )

        coverage_results.append(
            {
                "table": table,
                "companies": company_count,
            }
        )

        print(
            f"{table:<20} "
            f"{company_count} companies"
        )


# ======================================================
# STOCK PRICE COVERAGE CHECK
# ======================================================

print_section("STOCK PRICE COVERAGE CHECK")

with engine.connect() as conn:

    query = """
    SELECT
        COUNT(DISTINCT company_id)
        AS companies,
        COUNT(*) AS records
    FROM stock_prices;
    """

    result = pd.read_sql(
        query,
        conn,
    )

stock_companies = int(
    result.iloc[0]["companies"]
)

stock_records = int(
    result.iloc[0]["records"]
)

print(
    f"Companies : {stock_companies}"
)

print(
    f"Records   : {stock_records}"
)

expected_stock_records = 92 * 60

print(
    f"Expected  : {expected_stock_records}"
)

if stock_companies == 92:

    print(
        "✅ Stock prices contain "
        "all 92 master companies"
    )

else:

    print(
        "⚠️ Stock price company coverage "
        "is not 92"
    )

if stock_records == expected_stock_records:

    print(
        "✅ Stock price row count is "
        "92 × 60 = 5520"
    )

else:

    print(
        "⚠️ Unexpected stock price "
        "row count"
    )


# ======================================================
# MARKET CAP COVERAGE CHECK
# ======================================================

print_section("MARKET CAP COVERAGE CHECK")

with engine.connect() as conn:

    query = """
    SELECT
        COUNT(DISTINCT company_id)
        AS companies,
        COUNT(*) AS records
    FROM market_cap;
    """

    result = pd.read_sql(
        query,
        conn,
    )

market_companies = int(
    result.iloc[0]["companies"]
)

market_records = int(
    result.iloc[0]["records"]
)

print(
    f"Companies : {market_companies}"
)

print(
    f"Records   : {market_records}"
)

expected_market_records = 92 * 6

print(
    f"Expected  : {expected_market_records}"
)

if market_companies == 92:
    print(
        "✅ Market cap contains "
        "all 92 master companies"
    )
else:
    print(
        "⚠️ Market cap company coverage "
        "is not 92"
    )

if market_records == expected_market_records:
    print(
        "✅ Market cap row count is "
        "92 × 6 = 552"
    )
else:
    print(
        "⚠️ Unexpected market cap "
        "row count"
    )


# ======================================================
# SECTOR COVERAGE CHECK
# ======================================================

print_section("SECTOR COVERAGE CHECK")

with engine.connect() as conn:

    query = """
    SELECT
        COUNT(DISTINCT company_id)
        AS companies,
        COUNT(*) AS records
    FROM sectors;
    """

    result = pd.read_sql(
        query,
        conn,
    )

sector_companies = int(
    result.iloc[0]["companies"]
)

sector_records = int(
    result.iloc[0]["records"]
)

print(
    f"Companies : {sector_companies}"
)

print(
    f"Records   : {sector_records}"
)

if sector_companies == 92:
    print(
        "✅ Sector table covers "
        "all 92 companies"
    )
else:
    print(
        "⚠️ Sector coverage is not 92"
    )

if sector_records == 92:
    print(
        "✅ Sector table has "
        "92 records"
    )
else:
    print(
        "⚠️ Sector table does not "
        "have exactly 92 records"
    )


# ======================================================
# FOREIGN KEY LOGICAL CHECK
# ======================================================

print_section(
    "LOGICAL FOREIGN KEY CHECK"
)

fk_violations = []

with engine.connect() as conn:

    for table in CHILD_TABLES:

        if table not in database_tables:
            continue

        query = f"""
        SELECT
            COUNT(*) AS invalid_rows
        FROM "{table}" t
        LEFT JOIN companies c
            ON UPPER(TRIM(t.company_id))
             = UPPER(TRIM(c.id))
        WHERE t.company_id IS NOT NULL
          AND TRIM(t.company_id) != ''
          AND c.id IS NULL;
        """

        result = pd.read_sql(
            query,
            conn,
        )

        invalid_rows = int(
            result.iloc[0]["invalid_rows"]
        )

        if invalid_rows == 0:

            print(
                f"✅ {table:<20} "
                f"No FK violations"
            )

        else:

            print(
                f"❌ {table:<20} "
                f"{invalid_rows} FK violations"
            )

            fk_violations.append(
                {
                    "table": table,
                    "invalid_rows": invalid_rows,
                }
            )


# ======================================================
# SQLITE FOREIGN KEY CHECK
# ======================================================

print_section(
    "SQLITE FOREIGN KEY CONSTRAINT CHECK"
)

with engine.connect() as conn:

    fk = pd.read_sql(
        "PRAGMA foreign_key_check;",
        conn,
    )

if fk.empty:

    print(
        "✅ No SQLite foreign key "
        "constraint violations found."
    )

else:

    print(
        "❌ SQLite foreign key violations:"
    )

    print(fk)


# ======================================================
# FINAL VALIDATION SUMMARY
# ======================================================

print_section(
    "FINAL VALIDATION SUMMARY"
)

checks = []

checks.append(
    {
        "check": "Database exists",
        "status": "PASS",
    }
    if DB_PATH.exists()
    else
    {
        "check": "Database exists",
        "status": "FAIL",
    }
)

checks.append(
    {
        "check": "92 master companies",
        "status": "PASS"
        if len(master_ids) == 92
        else "FAIL",
    }
)

checks.append(
    {
        "check": "Expected tables",
        "status": "PASS"
        if not missing_tables
        else "FAIL",
    }
)

checks.append(
    {
        "check": "Duplicate primary IDs",
        "status": "PASS"
        if not duplicate_pk_tables
        else "FAIL",
    }
)

checks.append(
    {
        "check": "Invalid company IDs",
        "status": "PASS"
        if total_invalid == 0
        else "FAIL",
    }
)

checks.append(
    {
        "check": "Missing company IDs",
        "status": "PASS"
        if not missing_company_ids
        else "FAIL",
    }
)

checks.append(
    {
        "check": "Duplicate company-year records",
        "status": "PASS"
        if not duplicate_company_year_tables
        else "FAIL",
    }
)

checks.append(
    {
        "check": "Stock price coverage",
        "status": "PASS"
        if stock_companies == 92
        and stock_records == 5520
        else "FAIL",
    }
)

checks.append(
    {
        "check": "Market cap coverage",
        "status": "PASS"
        if market_companies == 92
        and market_records == 552
        else "FAIL",
    }
)

checks.append(
    {
        "check": "Sector coverage",
        "status": "PASS"
        if sector_companies == 92
        and sector_records == 92
        else "FAIL",
    }
)

checks.append(
    {
        "check": "Logical foreign keys",
        "status": "PASS"
        if not fk_violations
        else "FAIL",
    }
)

summary_df = pd.DataFrame(checks)

print(
    summary_df.to_string(
        index=False
    )
)


# ======================================================
# FINAL STATUS
# ======================================================

failed_checks = (
    summary_df["status"] == "FAIL"
).sum()

print("\n" + "=" * 70)

if failed_checks == 0:

    print(
        "✅ ALL DATABASE VALIDATION CHECKS PASSED"
    )

else:

    print(
        f"⚠️ {failed_checks} "
        f"VALIDATION CHECK(S) FAILED"
    )

print("=" * 70)