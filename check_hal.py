import sqlite3

DB_PATH = "data/database/nifty100.db"

con = sqlite3.connect(DB_PATH)

rows = con.execute(
    """
    SELECT *
    FROM documents
    WHERE company_id = ?
      AND year = ?
    """,
    ("HAL", "2011"),
).fetchall()

print("HAL 2011 records:")
print("-" * 50)

for row in rows:
    print(row)

print("\nTotal:", len(rows))

con.close()