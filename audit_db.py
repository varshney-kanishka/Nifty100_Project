import sqlite3

DB = r"data/database/nifty100.db"

conn = sqlite3.connect(DB)
cur = conn.cursor()

print("\n=== DATABASE AUDIT ===")

print(
    "financial_ratios:",
    cur.execute("SELECT COUNT(*) FROM financial_ratios").fetchone()[0]
)

print(
    "companies:",
    cur.execute("SELECT COUNT(*) FROM companies").fetchone()[0]
)

print(
    "sectors:",
    cur.execute(
        "SELECT COUNT(DISTINCT broad_sector) FROM sectors"
    ).fetchone()[0]
)

print("\n=== SECTOR LIST ===")

for row in cur.execute(
    """
    SELECT broad_sector, COUNT(*)
    FROM sectors
    GROUP BY broad_sector
    ORDER BY broad_sector
    """
):
    print(row)

print("\n=== FINANCIAL RATIOS YEARS ===")

print(
    cur.execute(
        """
        SELECT MIN(year), MAX(year), COUNT(DISTINCT year)
        FROM financial_ratios
        """
    ).fetchone()
)

conn.close()