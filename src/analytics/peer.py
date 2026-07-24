from pathlib import Path
import sqlite3
import pandas as pd
print("=" * 70)
print("DAY 18 - PEER COMPARISON")
print("=" * 70)

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

peer = pd.read_sql(
    "SELECT * FROM peer_groups",
    conn,
)

print()

print("Tables Loaded")

print("Ratios :", len(ratios))
print("Companies :", len(companies))
print("Peer Groups :", len(peer))
df = ratios.merge(
    peer,
    on="company_id",
    how="left",
)

df = df.merge(
    companies,
    left_on="company_id",
    right_on="id",
    how="left",
)

print()

print("Merged Successfully")

print(df.head())
metrics = [

    "return_on_equity_pct",

    "net_profit_margin_pct",

    "debt_to_equity",

    "interest_coverage",

    "asset_turnover",

    "free_cash_flow_cr",

]
results = []

for group in df["peer_group_name"].dropna().unique():

    group_df = df[df["peer_group_name"] == group].copy()

    for metric in metrics:

        if metric not in group_df.columns:
            continue

        if metric == "debt_to_equity":

            group_df["percentile_rank"] = (
                1 - group_df[metric].rank(pct=True)
            )

        else:

            group_df["percentile_rank"] = (
                group_df[metric].rank(pct=True)
            )

        temp = group_df[
            [
                "company_id",
                "company_name",
                "year",
            ]
        ].copy()

        temp["peer_group_name"] = group

        temp["metric"] = metric

        temp["value"] = group_df[metric]

        temp["percentile_rank"] = (
            group_df["percentile_rank"]
        )

        results.append(temp)
peer_percentiles = pd.concat(
    results,
    ignore_index=True,
)

print()

print("Peer Percentiles")

print(peer_percentiles.head())

print()

print("Rows")

print(len(peer_percentiles))
missing = df[
    df["peer_group_name"].isna()
]

print()

print("No Peer Group Assigned")

print(len(missing))
peer_percentiles.to_sql(

    "peer_percentiles",

    conn,

    if_exists="replace",

    index=False,

)

print()

print("peer_percentiles table created.")
output = BASE_DIR / "output"

output.mkdir(exist_ok=True)

peer_percentiles.to_csv(

    output / "peer_percentiles.csv",

    index=False,

)

print()

print("CSV Saved")

print(output / "peer_percentiles.csv")
conn.close()

print()

print("=" * 70)

print("DAY 18 COMPLETED")

print("=" * 70)        
        
