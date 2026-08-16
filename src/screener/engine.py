from .presets import (
    quality_compounder,
    value_pick,
    growth_accelerator,
    dividend_champion,
    debt_free_bluechip,
    turnaround_watch,
)
from pathlib import Path
import sqlite3

import yaml
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[2]

DB = BASE_DIR / "data/database/nifty100.db"

conn = sqlite3.connect(DB)

print("=" * 70)
print("CONNECTED TO DATABASE")
print("=" * 70)
ratios = pd.read_sql(
    "SELECT * FROM financial_ratios",
    conn,
)

companies = pd.read_sql(
    "SELECT * FROM companies",
    conn,
)

sectors = pd.read_sql(
    "SELECT * FROM sectors",
    conn,
)
print()

print("Rows")

print("Ratios :", len(ratios))
print("Companies :", len(companies))
print("Sectors :", len(sectors))
CONFIG = BASE_DIR / "config/screener_config.yaml"

with open(CONFIG, "r") as file:
    config = yaml.safe_load(file)

print()

print("Configuration Loaded")

print(config)
df = ratios.merge(
    companies[
        [
            "id",
            "company_name",
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

print()

print("Merged Successfully")

print(df.head())
df["composite_quality_score"] = 0
def apply_filters(data, config):

    filtered = data.copy()

    filters = config["filters"]

    return filtered
result = apply_filters(df, config)

print()

print("Filter Engine Ready")

print(result.shape)

print(result.head())
conn.close()

print()

print("=" * 70)
print("DAY 15 COMPLETED")
print("=" * 70)
quality = quality_compounder(df)

value = value_pick(df)

growth = growth_accelerator(df)

dividend = dividend_champion(df)

bluechip = debt_free_bluechip(df)

turnaround = turnaround_watch(df)
print("\nQuality Compounder :", len(quality))

print("Value Pick :", len(value))

print("Growth Accelerator :", len(growth))

print("Dividend Champion :", len(dividend))

print("Debt-Free Blue Chip :", len(bluechip))

print("Turnaround Watch :", len(turnaround))
print("\nQuality Compounder")

print(
    quality[
        [
            "company_id",
            "year",
            "return_on_equity_pct",
            "debt_to_equity",
        ]
    ].head(10)
)
conn.close()

print("\n" + "=" * 70)
print("DAY 16 COMPLETED")
print("=" * 70)