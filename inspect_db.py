import sqlite3
conn = sqlite3.connect(r"data/database/nifty100.db")
cur = conn.cursor()
print('TABLES')
for (name,) in cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"):
    print(name)
for table in ['companies','financial_ratios','profitandloss','balancesheet','cashflow','sectors','peer_groups','market_cap','prosandcons']:
    print(f'\n{table}')
    try:
        for c in cur.execute(f'PRAGMA table_info({table})'):
            print(c)
    except Exception as e:
        print('ERR', e)
