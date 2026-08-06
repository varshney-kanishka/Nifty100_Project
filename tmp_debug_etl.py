from pathlib import Path
import pandas as pd

base = Path('c:/Users/varsh/Desktop/Nifty100_Project')
raw = base / 'data' / 'raw'

bs = pd.read_excel(raw / 'balancesheet.xlsx', header=1)
pl = pd.read_excel(raw / 'profitandloss.xlsx', header=1)

targets = ['BEL', 'HAL', 'INDIGO', 'LT']
for cid in targets:
    print('===', cid)
    b = bs[bs['company_id'] == cid]
    p = pl[pl['company_id'] == cid]
    print('balance rows', len(b), 'profit rows', len(p))
    print('balance years', b['year'].astype(str).tolist())
    print('profit years', p['year'].astype(str).tolist())
    if len(b) and len(p):
        merged = b.merge(p[['company_id', 'year', 'sales']], on=['company_id', 'year'], how='left')
        print('merged null sales', merged['sales'].isna().sum())
        print('merged sample')
        print(merged[['year', 'sales', 'total_assets']].tail(10).to_string(index=False))
        print('needs_scale rows', ((merged['sales']/merged['total_assets']) > 20).sum())
        print('ratios >20 sample', (merged['sales']/merged['total_assets'])[merged['sales'].notna() & merged['total_assets'].notna() & ((merged['sales']/merged['total_assets'])>20)].head(10).tolist())

print('done')
