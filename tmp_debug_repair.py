from pathlib import Path
import sys

root = Path('c:/Users/varsh/Desktop/Nifty100_Project')
sys.path.insert(0, str(root / 'src' / 'etl'))
import loader
import pandas as pd

raw = root / 'data' / 'raw'
bs = pd.read_excel(raw / 'balancesheet.xlsx', header=1)
pl = pd.read_excel(raw / 'profitandloss.xlsx', header=1)
repaired = loader.repair_balancesheet_units(bs, pl)
print('repaired rows same:', len(repaired) == len(bs))
for cid in ['BEL','HAL','INDIGO','LT']:
    print('===', cid)
    merged = repaired[repaired['company_id']==cid].merge(
        pl[['company_id','year','sales']], on=['company_id','year'], how='left')
    merged['sales'] = pd.to_numeric(merged['sales'], errors='coerce')
    merged['total_assets'] = pd.to_numeric(merged['total_assets'], errors='coerce')
    print(merged[['year','sales','total_assets']].head(15).to_string(index=False))
    print('ratios > 20 rows', ((merged['sales']/merged['total_assets']) > 20).sum())
    print('max ratio', (merged['sales']/merged['total_assets']).max())
    print('---')
