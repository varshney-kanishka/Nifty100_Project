from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine
base = Path('c:/Users/varsh/Desktop/Nifty100_Project')
proc = base / 'data' / 'processed'

bs = pd.read_csv(proc / 'balancesheet.csv')
pl = pd.read_csv(proc / 'profitandloss.csv')
print('BS BEL 2013')
print(bs[(bs['company_id']=='BEL') & (bs['year']==2013)][['year','total_assets']].to_string(index=False))
print('PL BEL 2013')
print(pl[(pl['company_id']=='BEL') & (pl['year']==2013)][['year','sales']].to_string(index=False))

engine = create_engine(f"sqlite:///{base/'data'/'database'/'nifty100.db'}")
with engine.connect() as conn:
    db_bs = pd.read_sql('SELECT company_id, year, total_assets FROM balancesheet WHERE company_id = "BEL" AND year = 2013', conn)
    db_pl = pd.read_sql('SELECT company_id, year, sales FROM profitandloss WHERE company_id = "BEL" AND year = 2013', conn)
print('DB BS BEL 2013')
print(db_bs.to_string(index=False))
print('DB PL BEL 2013')
print(db_pl.to_string(index=False))
