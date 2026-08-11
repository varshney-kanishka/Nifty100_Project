import pandas as pd
import glob
import os

MASTER = r"data\processed\companies.csv"
PROCESSED = r"data\processed"

# -----------------------------
# 1. Load master company IDs
# -----------------------------
companies = pd.read_csv(MASTER)

master_ids = set(
    companies["id"]
    .astype(str)
    .str.strip()
    .str.upper()
)

print("=" * 70)
print("MASTER COMPANY CHECK")
print("=" * 70)

print("Master company count:", len(master_ids))
print("Master column:", "id")

# -----------------------------
# 2. Check every processed CSV
# -----------------------------
all_child_ids = set()

for file in glob.glob(os.path.join(PROCESSED, "*.csv")):

    if os.path.basename(file) == "companies.csv":
        continue

    df = pd.read_csv(file)

    if "company_id" not in df.columns:
        continue

    ids = set(
        df["company_id"]
        .dropna()
        .astype(str)
        .str.strip()
        .str.upper()
    )

    missing = ids - master_ids

    all_child_ids.update(ids)

    print()
    print("-" * 70)
    print(os.path.basename(file))
    print("Rows:", len(df))
    print("Unique company IDs:", len(ids))

    if missing:
        print("MISSING FROM MASTER:")
        for company_id in sorted(missing):
            print("  ", company_id)
    else:
        print("All company IDs exist in master.")

# -----------------------------
# 3. Overall missing IDs
# -----------------------------
overall_missing = all_child_ids - master_ids

print()
print("=" * 70)
print("OVERALL RESULT")
print("=" * 70)

print("Master companies:", len(master_ids))
print("Unique child company IDs:", len(all_child_ids))
print("Missing company IDs:", len(overall_missing))

for company_id in sorted(overall_missing):
    print(" ", company_id)

# -----------------------------
# 4. Possible ATGL / AGTL typo
# -----------------------------
if "ATGL" in master_ids and "AGTL" in overall_missing:
    print()
    print("=" * 70)
    print("POSSIBLE ID TYPO DETECTED")
    print("=" * 70)
    print("Master contains: ATGL")
    print("Child tables contain: AGTL")
    print("Likely normalization mapping: AGTL -> ATGL")