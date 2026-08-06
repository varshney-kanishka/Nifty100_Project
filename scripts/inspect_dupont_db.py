import sqlite3
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DB = BASE_DIR / "data/database/nifty100.db"

conn = sqlite3.connect(DB)

companies_to_check = ["BEL", "HAL", "INDIGO"]

profit = pd.read_sql("SELECT * FROM profitandloss", conn)
balance = pd.read_sql("SELECT * FROM balancesheet", conn)

print('Rows in profitandloss:', len(profit))
print('Rows in balancesheet:', len(balance))

# Clean and mirror logic from dupont_analysis
profit = profit[profit['year'] != 'TTM'].copy()
profit['year_num'] = pd.to_numeric(profit['year'].str.extract(r"(\d{4})")[0], errors='coerce')
profit = profit.dropna(subset=['year_num'])
profit['year_num'] = profit['year_num'].astype(int)

balance = balance.copy()
balance['year_num'] = pd.to_numeric(balance['year'].str.extract(r"(\d{4})")[0], errors='coerce')

for cid in companies_to_check:
    print('\n---', cid, '---')
    p = profit[profit['company_id']==cid].sort_values('year_num')
    b = balance[balance['company_id']==cid].sort_values('year_num')
    print('profit rows:', len(p))
    print(p.tail(5).to_string(index=False))
    print('\nbalance rows:', len(b))
    print(b.tail(5).to_string(index=False))

    # Merge latest like dupont: get latest profit row then left-join balance
    if len(p)==0:
        print('No profit rows, skipping')
        continue
    latest_p = p.sort_values('year_num').drop_duplicates(subset='company_id', keep='last')
    cid_row = latest_p.iloc[0]
    yr = cid_row['year_num']
    # try to find matching balance for same year
    bal_match = b[b['year_num']==yr]
    if bal_match.empty:
        print('No balance row for same year; showing most recent balance:')
        bal_row = b.sort_values('year_num').drop_duplicates(subset='company_id', keep='last')
    else:
        bal_row = bal_match.iloc[[0]]

    print('\nSelected profit row:')
    print(cid_row[['company_id','year','sales','net_profit']].to_string())
    print('\nSelected balance row:')
    # sum equity capital and reserves
    try:
        equity_cap = float(bal_row.iloc[0]['equity_capital'])
        reserves = float(bal_row.iloc[0]['reserves'])
        total_assets = float(bal_row.iloc[0]['total_assets'])
    except Exception as e:
        print('Error reading numeric balance fields:', e)
        print(bal_row.head().to_string())
        continue

    print('equity_capital:', equity_cap)
    print('reserves:', reserves)
    print('equity (cap+res):', equity_cap+reserves)
    print('total_assets:', total_assets)

    sales = float(cid_row['sales']) if pd.notna(cid_row['sales']) else None
    net_profit = float(cid_row['net_profit']) if pd.notna(cid_row['net_profit']) else None
    print('sales:', sales)
    print('net_profit:', net_profit)

    # compute dupont
    profit_margin = None
    asset_turnover = None
    equity_multiplier = None
    roe = None
    if sales and sales !=0:
        profit_margin = net_profit / sales
    if total_assets and total_assets !=0:
        asset_turnover = sales / total_assets
    equity = equity_cap + reserves
    if equity and equity !=0:
        equity_multiplier = total_assets / equity
    if profit_margin is not None and asset_turnover is not None and equity_multiplier is not None:
        roe = profit_margin * asset_turnover * equity_multiplier * 100
    print('\nComputed DuPont pieces:')
    print('profit_margin:', profit_margin)
    print('asset_turnover:', asset_turnover)
    print('equity_multiplier:', equity_multiplier)
    print('roe %:', roe)

conn.close()
