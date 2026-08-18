import sqlite3

db = "data/database/nifty100.db"
c = sqlite3.connect(db)

print("PROS & CONS RECORDS")
print("=" * 60)

rows = c.execute("""
    SELECT p.company_id, c.company_name, p.pros, p.cons
    FROM prosandcons p
    LEFT JOIN companies c
        ON p.company_id = c.id
    ORDER BY p.company_id
""").fetchall()

for company_id, company_name, pros, cons in rows:
    print(f"\nCompany ID: {company_id}")
    print(f"Company:    {company_name}")
    print(f"Pros:       {pros}")
    print(f"Cons:       {cons}")


print("\n\nANALYSIS RECORDS")
print("=" * 60)

rows = c.execute("""
    SELECT a.company_id,
           c.company_name,
           a.compounded_sales_growth,
           a.compounded_profit_growth,
           a.stock_price_cagr,
           a.roe
    FROM analysis a
    LEFT JOIN companies c
        ON a.company_id = c.id
    ORDER BY a.company_id
""").fetchall()

for company_id, company_name, sales, profit, cagr, roe in rows:
    print(f"\nCompany ID: {company_id}")
    print(f"Company:    {company_name}")
    print(f"Sales CAGR: {sales}")
    print(f"Profit CAGR:{profit}")
    print(f"Stock CAGR: {cagr}")
    print(f"ROE:        {roe}")


print("\n\nDUPLICATE COMPANY IDs")
print("=" * 60)

for table in ["prosandcons", "analysis"]:
    print(f"\n{table}:")

    rows = c.execute(f"""
        SELECT company_id, COUNT(*)
        FROM {table}
        GROUP BY company_id
        HAVING COUNT(*) > 1
        ORDER BY company_id
    """).fetchall()

    if rows:
        for company_id, count in rows:
            print(f"{company_id}: {count} rows")
    else:
        print("No duplicates.")


c.close()