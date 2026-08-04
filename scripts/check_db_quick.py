import sqlite3
import sys
from pathlib import Path


def main():
    DB = Path("data/database/nifty100.db")
    if not DB.exists():
        print(f"DB file not found: {DB.resolve()}")
        sys.exit(2)

    conn = sqlite3.connect(str(DB))
    cur = conn.cursor()
    tables = [row[0] for row in cur.execute("SELECT name FROM sqlite_master WHERE type='table'")]
    print("TABLES:", tables)

    for t in ("companies", "financial_ratios", "profitandloss", "balancesheet", "cashflow"):
        if t in tables:
            try:
                cnt = cur.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            except Exception as e:
                cnt = f"ERROR: {e}"
            print(f"{t}: {cnt}")
        else:
            print(f"{t}: MISSING")

    conn.close()


if __name__ == "__main__":
    main()
