import pandas as pd
from pathlib import Path

RAW_FOLDER = Path('data/raw')
PROCESSED_FOLDER = Path('data/processed')

print('Inspecting raw and processed profitandloss and balancesheet data...')

for name in ['profitandloss', 'balancesheet']:
    raw_path = RAW_FOLDER / f'{name}.xlsx'
    proc_path = PROCESSED_FOLDER / f'{name}.csv'
    print('\n' + '=' * 70)
    print(name.upper())
    print('RAW exists:', raw_path.exists())
    print('PROC exists:', proc_path.exists())

    if raw_path.exists():
        raw = pd.read_excel(raw_path, header=1)
        print('RAW shape:', raw.shape)
        raw_small = raw[(name == 'balancesheet' and pd.to_numeric(raw['total_assets'], errors='coerce') < 100) | (name == 'profitandloss' and pd.to_numeric(raw['sales'], errors='coerce') < 100)] if name == 'balancesheet' else raw
        print('RAW columns:', raw.columns.tolist())
    else:
        raw = None

    if proc_path.exists():
        proc = pd.read_csv(proc_path, header=1)
        print('PROC shape:', proc.shape)
        print('PROC columns:', proc.columns.tolist())
    else:
        proc = None

print('\nInspecting small total_assets in processed balancesheet...')
proc = pd.read_csv(PROCESSED_FOLDER / 'balancesheet.csv', header=1)
proc['total_assets'] = pd.to_numeric(proc['total_assets'], errors='coerce')
small = proc[proc['total_assets'] < 100]
print('rows < 100:', len(small))
print(small[['company_id', 'year', 'equity_capital', 'reserves', 'borrowings', 'total_assets']].to_string(index=False))

print('\nInspecting suspected companies in raw/proc balancesheet...')
for ticker in ['BEL','HAL','INDIGO','LT']:
    print('\n', ticker)
    raw = pd.read_excel(RAW_FOLDER / 'balancesheet.xlsx', header=1)
    raw_subset = raw[raw['company_id'] == ticker]
    print('RAW', raw_subset[['year','total_assets']].head(20).to_string(index=False))
    proc = pd.read_csv(PROCESSED_FOLDER / 'balancesheet.csv', header=1)
    proc_subset = proc[proc['company_id'] == ticker]
    print('PROC', proc_subset[['year','total_assets']].head(20).to_string(index=False))
