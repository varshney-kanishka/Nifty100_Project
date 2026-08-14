from pathlib import Path
import sqlite3
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[2]

DB = BASE_DIR / "data/database/nifty100.db"

conn = sqlite3.connect(DB)

print("=" * 70)
print("DAY 13 - RATIO REVIEW")
print("=" * 70)

companies = pd.read_sql(
    "SELECT * FROM companies",
    conn,
)

sectors = pd.read_sql(
    "SELECT * FROM sectors",
    conn,
)

ratios = pd.read_sql(
    "SELECT * FROM financial_ratios",
    conn,
)

print("\nTables Loaded")

print("Companies :", len(companies))
print("Sectors   :", len(sectors))
print("Ratios    :", len(ratios))
df = ratios.merge(

    companies[
        [
            "id",
            "company_name",
            "roe_percentage",
            "roce_percentage",
        ]
    ],

    left_on="company_id",

    right_on="id",

    how="left",

)

df = df.merge(

    sectors[
        [
            "company_id",
            "broad_sector",
        ]
    ],

    on="company_id",

    how="left",

)

print("\nMerged Successfully")

print(df.head())
financials = df[

    df["broad_sector"] == "Financials"

]

print("\nFinancial Companies")

print(financials["company_id"].nunique())

print(

    financials[
        [
            "company_id",
            "company_name",
        ]
    ].head(20)

)
df["high_leverage_flag"] = False

mask = (

    (df["debt_to_equity"] > 5)

    &

    (df["broad_sector"] != "Financials")

)

df.loc[mask, "high_leverage_flag"] = True

print(

    "\nHigh Leverage Companies :",

    df["high_leverage_flag"].sum(),

)
# =====================================================
# ROCE VALIDATION
# =====================================================

df["roce_difference"] = (
    df["return_on_capital_employed_pct"]
    - df["roce_percentage"]
).abs()

roce_anomalies = df[
    df["roce_difference"] > 5
]

print(
    "\nROCE Anomalies",
    len(roce_anomalies),
)

df["roe_difference"] = (

    df["return_on_equity_pct"]

    -

    df["roe_percentage"]

).abs()

roe_anomalies = df[

    df["roe_difference"] > 5

]

print(

    "\nROE Anomalies",

    len(roe_anomalies),

)
OUTPUT = BASE_DIR / "output"

OUTPUT.mkdir(

    exist_ok=True

)
log = OUTPUT / "ratio_edge_cases.log"

with open(

    log,

    "w",

    encoding="utf-8",

) as f:

    f.write(

        "Sprint 2 Day 13\n"

    )

    f.write(

        "=" * 60 + "\n\n"

    )

    f.write(

        f"ROCE anomalies : {len(roce_anomalies)}\n"

    )

    f.write(

        f"ROE anomalies : {len(roe_anomalies)}\n"

    )

print(

    "\nLog Created"

)

print(log)
roce_anomalies.to_csv(

    OUTPUT / "roce_anomalies.csv",

    index=False,

)

roe_anomalies.to_csv(

    OUTPUT / "roe_anomalies.csv",

    index=False,

)

print("\nCSV Files Saved")
conn.close()

print("\nDatabase Closed")

print("=" * 70)

print("DAY 13 COMPLETED")

print("=" * 70)