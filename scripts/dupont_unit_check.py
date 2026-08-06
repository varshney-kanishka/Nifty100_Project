import sqlite3
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DB = BASE_DIR / 'data/database/nifty100.db'
conn = sqlite3.connect(DB)

companies = ['BEL', 'HAL', 'TCS', 'LT', 'INDIGO']
for cid in companies:
    profit = pd.read_sql('SELECT * FROM profitandloss WHERE company_id = ? AND year != ? ORDER BY year DESC LIMIT 1', conn, params=(cid, 'TTM'))
    balance = pd.read_sql('SELECT * FROM balancesheet WHERE company_id = ? ORDER BY year DESC LIMIT 1', conn, params=(cid,))
    if profit.empty or balance.empty:
        print(cid, 'missing data')
        continue
    s = float(profit.loc[0, 'sales'])
    npf = float(profit.loc[0, 'net_profit'])
    ta = float(balance.loc[0, 'total_assets'])
    eq = float(balance.loc[0, 'equity_capital']) + float(balance.loc[0, 'reserves'])

    def safe(x):
        return None if x == 0 else x
    raw_pm = npf / s if safe(s) else None
    raw_at = s / ta if safe(ta) else None
    raw_em = ta / eq if safe(eq) else None
    raw_roe = raw_pm * raw_at * raw_em * 100 if raw_pm is not None and raw_at is not None and raw_em is not None else None

    s100 = s / 100
    np100 = npf / 100
    sc_pm = np100 / s100 if safe(s100) else None
    sc_at = s100 / ta if safe(ta) else None
    sc_em = raw_em
    sc_roe = sc_pm * sc_at * sc_em * 100 if sc_pm is not None and sc_at is not None and sc_em is not None else None

    print(f'=== {cid} ===')
    print('sales raw', s, 'net_profit raw', npf, 'assets raw', ta, 'equity raw', eq)
    print('  raw pm', raw_pm, 'raw at', raw_at, 'raw em', raw_em, 'raw roe', raw_roe)
    print('  /100 pm', sc_pm, ' /100 at', sc_at, ' /100 em', sc_em, ' /100 roe', sc_roe)
    print()
conn.close()
