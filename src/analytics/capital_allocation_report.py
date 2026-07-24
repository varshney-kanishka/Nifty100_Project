from pathlib import Path
import sqlite3
import pandas as pd

from cashflow_kpis import capital_allocation_pattern

BASE_DIR = Path(__file__).resolve().parents[2]

DB = BASE_DIR / "data/database/nifty100.db"

OUTPUT = BASE_DIR / "output"

OUTPUT.mkdir(exist_ok=True)

conn = sqlite3.connect(DB)

cashflow = pd.read_sql(
    "SELECT company_id,year,operating_activity,investing_activity,financing_activity FROM cashflow",
    conn,
)

cashflow["pattern_label"] = cashflow.apply(

    lambda row: capital_allocation_pattern(

        row["operating_activity"],
        row["investing_activity"],
        row["financing_activity"],

    ),

    axis=1,

)

cashflow["cfo_sign"] = cashflow["operating_activity"].apply(
    lambda x: "+" if x >= 0 else "-"
)

cashflow["cfi_sign"] = cashflow["investing_activity"].apply(
    lambda x: "+" if x >= 0 else "-"
)

cashflow["cff_sign"] = cashflow["financing_activity"].apply(
    lambda x: "+" if x >= 0 else "-"
)

output = cashflow[
    [
        "company_id",
        "year",
        "cfo_sign",
        "cfi_sign",
        "cff_sign",
        "pattern_label",
    ]
]

output.to_csv(
    OUTPUT / "capital_allocation.csv",
    index=False,
)

print(output.head())

print("\nSaved to output/capital_allocation.csv")
