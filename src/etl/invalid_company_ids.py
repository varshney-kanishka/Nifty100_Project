import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "data" / "database" / "nifty100.db"
print("DB PATH:", DB_PATH)
print("DB EXISTS:", DB_PATH.exists())
print("DB SIZE:", DB_PATH.stat().st_size)
TABLES = [
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


def main():
    con = sqlite3.connect(DB_PATH)

    master_ids = {
        row[0]
        for row in con.execute("SELECT id FROM companies")
    }

    print("INVALID COMPANY ID DIAGNOSTIC")
    print("=" * 60)
    print(f"Master companies: {len(master_ids)}")
    print()

    grand_total = 0

    for table in TABLES:
        query = f"""
            SELECT company_id, COUNT(*) AS records
            FROM {table}
            WHERE company_id NOT IN ({",".join("?" * len(master_ids))})
            GROUP BY company_id
            ORDER BY records DESC
        """

        rows = con.execute(query, tuple(master_ids)).fetchall()

        if rows:
            table_total = sum(count for _, count in rows)
            grand_total += table_total

            print(f"\n{table}")
            print("-" * 40)

            for company_id, count in rows:
                print(f"{company_id:<15} {count:>5}")

            print(f"Total invalid rows: {table_total}")

    print("\n" + "=" * 60)
    print(f"TOTAL INVALID ROWS: {grand_total}")

    con.close()


if __name__ == "__main__":
    main()
    