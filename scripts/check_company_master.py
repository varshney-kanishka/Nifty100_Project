import pandas as pd
import glob
import os

MASTER_FILE = r"data\processed\companies.csv"

master = set(
    pd.read_csv(MASTER_FILE)["id"]
    .astype(str)
    .str.strip()
    .str.upper()
)

print("MASTER COMPANY CHECK")
print("====================")
print("Master companies:", len(master))
print()

all_child_ids = set()

for file in glob.glob(r"data\processed\*.csv"):

    df = pd.read_csv(file)

    if "company_id" not in df.columns:
        continue

    ids = (
        df["company_id"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    all_child_ids.update(ids)

    missing = sorted(set(ids) - master)

    print(os.path.basename(file))
    print("Rows:", len(df))
    print("Unique company IDs:", ids.nunique())

    if missing:
        print("Missing from master:")
        for company_id in missing:
            print(" ", company_id)
    else:
        print("All company IDs exist in master.")

    print()

print("SUMMARY")
print("=======")

missing_all = sorted(all_child_ids - master)

print("Master companies:", len(master))
print("Unique child IDs:", len(all_child_ids))
print("Missing IDs:", len(missing_all))

for company_id in missing_all:
    print(company_id)

print()
print("Known normalization:")
print("AGTL -> ATGL")