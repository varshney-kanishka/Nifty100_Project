import sqlite3
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DB = BASE_DIR / 'data/database/nifty100.db'
conn = sqlite3.connect(DB)

profit = pd.read_sql('SELECT * FROM profitandloss', conn)
balance = pd.read_sql('SELECT * FROM balancesheet', conn)

profit['sales'] = pd.to_numeric(profit['sales'], errors='coerce')
profit['net_profit'] = pd.to_numeric(profit['net_profit'], errors='coerce')

merged = profit.merge(
    balance[['company_id', 'year', 'equity_capital', 'reserves', 'borrowings', 'total_assets']],
    on=['company_id', 'year'],
    how='left',
)
merged = merged[merged['year'] != 'TTM'].copy()
merged['year_num'] = pd.to_numeric(merged['year'].str.extract(r'(\d{4})')[0], errors='coerce')
merged = merged.dropna(subset=['year_num'])
merged['year_num'] = merged['year_num'].astype(int)
latest = merged.sort_values('year_num').drop_duplicates(subset='company_id', keep='last')

for cid in ['BEL', 'HAL', 'TCS', 'LT', 'INDIGO', 'NESTLEIND']:
    row = latest[latest['company_id'] == cid]
    print('===', cid, '===')
    if row.empty:
        print('no latest row')
        continue
    row = row.iloc[0]
    s = row['sales']
    npf = row['net_profit']
    ta = float(row['total_assets'])
    eq = float(row['equity_capital']) + float(row['reserves'])
    raw_at = s / ta if ta else None
    raw_pm = npf / s if s else None
    raw_em = ta / eq if eq else None
    raw_roe = raw_pm * raw_at * raw_em * 100 if raw_pm is not None and raw_at is not None and raw_em is not None else None
    scaled_s = s / 100
    scaled_npf = npf / 100
    scaled_at = scaled_s / ta if ta else None
    scaled_pm = scaled_npf / scaled_s if scaled_s else None
    scaled_roe = scaled_pm * scaled_at * raw_em * 100 if scaled_pm is not None and scaled_at is not None and raw_em is not None else None
    print('year', row['year'])
    print('sales', s, 'net_profit', npf, 'total_assets', ta, 'equity', eq)
    print('raw pm', raw_pm, 'raw at', raw_at, 'raw em', raw_em, 'raw roe', raw_roe)
    print('scaled pm', scaled_pm, 'scaled at', scaled_at, 'scaled roe', scaled_roe)
    print()

conn.close()
