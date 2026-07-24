from pathlib import Path
import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
print("=" * 70)
print("DAY 19 - RADAR CHARTS")
print("=" * 70)

BASE_DIR = Path(__file__).resolve().parents[2]

DB = BASE_DIR / "data/database/nifty100.db"

conn = sqlite3.connect(DB)
ratios = pd.read_sql(
    "SELECT * FROM financial_ratios",
    conn,
)

peer = pd.read_sql(
    "SELECT * FROM peer_groups",
    conn,
)

companies = pd.read_sql(
    "SELECT id, company_name FROM companies",
    conn,
)

print()

print("Tables Loaded")

print("Ratios :", len(ratios))
print("Peer :", len(peer))
print("Companies :", len(companies))
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
chart_folder = BASE_DIR / "reports" / "radar_charts"

chart_folder.mkdir(
    parents=True,
    exist_ok=True,
)

print()

print("Folder Created")

print(chart_folder)

metrics = [

    "return_on_equity_pct",

    "net_profit_margin_pct",

    "asset_turnover",

    "debt_to_equity",

    "interest_coverage",

    "free_cash_flow_cr",

]

companies_list = df["company_id"].dropna().unique()

count = 0

for company in companies_list:

    company_df = df[df["company_id"] == company]

    if company_df.empty:
        continue

    row = company_df.iloc[-1]

    values = []

    labels = []

    for metric in metrics:

        value = row.get(metric, 0)

        if pd.isna(value):
            value = 0

        values.append(value)

        labels.append(metric)

    values += values[:1]

    angles = np.linspace(
        0,
        2*np.pi,
        len(labels),
        endpoint=False,
    ).tolist()

    angles += angles[:1]

    plt.figure(figsize=(6,6))

    ax = plt.subplot(111, polar=True)

    ax.plot(
        angles,
        values,
        linewidth=2,
    )

    ax.fill(
        angles,
        values,
        alpha=0.25,
    )

    ax.set_xticks(
        angles[:-1]
    )

    ax.set_xticklabels(
        labels,
        fontsize=8,
    )

    plt.title(company)

    plt.savefig(

        chart_folder / f"{company}_radar.png",

        dpi=200,

        bbox_inches="tight",

    )

    plt.close()

    count += 1
    
    print()

print("=" * 70)

print("Radar Charts Generated")

print(count)

print("charts")

print(chart_folder)

conn.close()

print()

print("=" * 70)

print("DAY 19 COMPLETED")

print("=" * 70)