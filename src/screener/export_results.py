import sqlite3
from pathlib import Path

import pandas as pd
from presets import *

BASE_DIR = Path(__file__).resolve().parents[2]

DB = BASE_DIR / "data/database/nifty100.db"

conn = sqlite3.connect(DB)
ratios = pd.read_sql(

    "SELECT * FROM financial_ratios",

    conn,

)
companies = pd.read_sql(

    "SELECT id, company_name FROM companies",

    conn,

)
df = ratios.merge(

    companies,

    left_on="company_id",

    right_on="id",

    how="left",

)

print(df.head())
df["composite_quality_score"] = (

    df["return_on_equity_pct"].fillna(0)

    + df["net_profit_margin_pct"].fillna(0)

    + df["asset_turnover"].fillna(0) * 10

    + (1 - df["debt_to_equity"].fillna(1)) * 10

)
maximum = df["composite_quality_score"].max()

df["composite_quality_score"] = (

    df["composite_quality_score"]

    / maximum

) * 100
df = df.sort_values(

    by="composite_quality_score",

    ascending=False,

)
quality = quality_compounder(df)

value = value_pick(df)

growth = growth_accelerator(df)

dividend = dividend_champion(df)

bluechip = debt_free_bluechip(df)

turnaround = turnaround_watch(df)

output = BASE_DIR / "output"

output.mkdir(exist_ok=True)
with pd.ExcelWriter(

    output / "screener_output.xlsx",

    engine="openpyxl",

) as writer:

    quality.to_excel(

        writer,

        sheet_name="Quality",

        index=False,

    )

    value.to_excel(

        writer,

        sheet_name="Value",

        index=False,

    )

    growth.to_excel(

        writer,

        sheet_name="Growth",

        index=False,

    )

    dividend.to_excel(

        writer,

        sheet_name="Dividend",

        index=False,

    )

    bluechip.to_excel(

        writer,

        sheet_name="BlueChip",

        index=False,

    )

    turnaround.to_excel(

        writer,

        sheet_name="Turnaround",

        index=False,

    )
print()

print("=" * 70)

print("SCREENER OUTPUT CREATED")

print("=" * 70)

print()

print("Quality :", len(quality))

print("Value :", len(value))

print("Growth :", len(growth))

print("Dividend :", len(dividend))

print("BlueChip :", len(bluechip))

print("Turnaround :", len(turnaround))

print()

print("Saved to")

print(output / "screener_output.xlsx")
conn.close()

print()

print("=" * 70)

print("DAY 17 COMPLETED")

print("=" * 70)    
