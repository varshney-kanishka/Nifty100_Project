import sqlite3
from pathlib import Path

import pandas as pd
print("=" * 70)
print("DAY 30 - AUTO PROS & CONS GENERATOR")
print("=" * 70)
BASE_DIR = Path(__file__).resolve().parents[2]

DB = BASE_DIR / "data/database/nifty100.db"

OUTPUT = BASE_DIR / "output"

conn = sqlite3.connect(DB)
ratios = pd.read_sql(
    "SELECT * FROM financial_ratios",
    conn,
)

companies = pd.read_sql(
    "SELECT * FROM companies",
    conn,
)

analysis = pd.read_sql(
    "SELECT * FROM analysis",
    conn,
)

profit = pd.read_sql(
    "SELECT * FROM profitandloss",
    conn,
)

balance = pd.read_sql(
    "SELECT * FROM balancesheet",
    conn,
)
print("\nTables Loaded")

print("Ratios :", len(ratios))
print("Companies :", len(companies))
print("Analysis :", len(analysis))
print("Profit :", len(profit))
print("Balance :", len(balance))
# Keep only valid company IDs
valid_companies = companies["id"].astype(str).str.strip().unique()

ratios["company_id"] = ratios["company_id"].astype(str).str.strip()

ratios = ratios[
    ratios["company_id"].isin(valid_companies)
]

print("Unique Ratio Companies :", ratios["company_id"].nunique())
latest = (
    ratios[
        ratios["year"] != "TTM"
    ]
    .copy()
)

latest["year_num"] = (
    latest["year"]
    .str.extract(r"(\d{4})")[0]
    .astype(int)
)

latest = (
    latest.sort_values("year_num")
    .drop_duplicates(
        subset="company_id",
        keep="last",
    )
)

print("\nLatest Companies :", len(latest))
records = []
for _, row in latest.iterrows():

    company = row["company_id"]

    match = companies.loc[
    companies["id"] == company,
    "company_name",
]

    if match.empty:
     continue

    company_name = match.iloc[0]
    if row["return_on_equity_pct"] > 20:

        records.append(
            {
                "company_id": company,
                "company_name": company_name,
                "type": "Pro",
                "rule_id": "P1",
                "text": "Consistently high return on equity above 20% demonstrates exceptional capital efficiency.",
                "confidence_pct": 90,
            }
        )
    if row["debt_to_equity"] == 0:

         records.append(
            {
                "company_id": company,
                "company_name": company_name,
                "type": "Pro",
                "rule_id": "P2",
                "text": "Debt-free balance sheet provides financial flexibility.",
                "confidence_pct": 85,
            }
        )   
    if row["free_cash_flow_cr"] > 0:

         records.append(
            {
                "company_id": company,
                "company_name": company_name,
                "type": "Pro",
                "rule_id": "P3",
                "text": "Positive free cash flow indicates healthy business fundamentals.",
                "confidence_pct": 80,
            }
        ) 
    if row["debt_to_equity"] > 2:

         records.append(
            {
                "company_id": company,
                "company_name": company_name,
                "type": "Con",
                "rule_id": "C1",
                "text": "Debt-to-equity ratio is high and should be monitored.",
                "confidence_pct": 88,
            }
        ) 
    
    if row["free_cash_flow_cr"] < 0:

         records.append(
            {
                "company_id": company,
                "company_name": company_name,
                "type": "Con",
                "rule_id": "C2",
                "text": "Negative free cash flow raises concern about cash generation quality.",
                "confidence_pct": 85,
            }
        ) 
    if row["return_on_equity_pct"] < 10:

          records.append(
            {
                "company_id": company,
                "company_name": company_name,
                "type": "Con",
                "rule_id": "C3",
                "text": "Low return on equity indicates weak capital efficiency.",
                "confidence_pct": 75,
            }
        ) 
          
    if row["operating_profit_margin_pct"] > 25:
     records.append({
        "company_id": company,
        "company_name": company_name,
        "type": "Pro",
        "rule_id": "P4",
        "text": "Operating profit margin above 25% indicates strong pricing power and cost discipline.",
        "confidence_pct": 85,
    })
     if row["interest_coverage"] > 10:
      records.append({
        "company_id": company,
        "company_name": company_name,
        "type": "Pro",
        "rule_id": "P5",
        "text": "Very high interest coverage reflects negligible financial stress.",
        "confidence_pct": 82,
    })
    if row["earnings_per_share"] > 0:
      records.append({
         "company_id": company,
        "company_name": company_name,
        "type": "Pro",
        "rule_id": "P6",
        "text": "Positive earnings per share indicate profitable operations.",
        "confidence_pct": 78,
    }) 
    if row["interest_coverage"] < 1.5:
     records.append({
        "company_id": company,
        "company_name": company_name,
        "type": "Con",
        "rule_id": "C4",
        "text": "Low interest coverage indicates debt servicing risk.",
        "confidence_pct": 90,
    })
     if row["operating_profit_margin_pct"] < 10:
      records.append({
        "company_id": company,
        "company_name": company_name,
        "type": "Con",
        "rule_id": "C5",
        "text": "Low operating margin indicates weak profitability.",
        "confidence_pct": 78,
    })
      
    if row["earnings_per_share"] < 0:
     records.append({
        "company_id": company,
        "company_name": company_name,
        "type": "Con",
        "rule_id": "C6",
        "text": "Negative earnings per share indicate losses.",
        "confidence_pct": 90,
    })
pros_cons = pd.DataFrame(records)  
print("\nPros :", len(pros_cons[pros_cons["type"] == "Pro"]))
print("Cons :", len(pros_cons[pros_cons["type"] == "Con"]))

print("\nCompanies Covered :",
      pros_cons["company_id"].nunique())
print("\nGenerated Records :", len(pros_cons))

print(
    pros_cons.head()
)

print("\nOutput File")

print(
    OUTPUT / "pros_cons_generated.csv"
)

print("\n" + "=" * 70)
print("DAY 30 PART 1 COMPLETED")
print("=" * 70)    