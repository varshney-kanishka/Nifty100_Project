import pandas as pd
from pathlib import Path

PROCESSED = Path("data/processed")

# sectors.csv defines the authoritative 92-company universe
sectors_path = PROCESSED / "sectors.csv"

sectors = pd.read_csv(sectors_path)
master_ids = set(sectors["company_id"].dropna().astype(str).str.strip())

print("=" * 70)
print(f"Authoritative master companies: {len(master_ids)}")
print("=" * 70)

if len(master_ids) != 92:
    raise ValueError(
        f"Expected 92 master companies, found {len(master_ids)}"
    )

for path in sorted(PROCESSED.glob("*.csv")):

    # Never modify sectors.csv itself
    if path.name == "sectors.csv":
        continue

    df = pd.read_csv(path)

    if "company_id" not in df.columns:
        continue

    before = len(df)

    df["company_id"] = df["company_id"].astype(str).str.strip()

    df = df[df["company_id"].isin(master_ids)].copy()

    removed = before - len(df)

    df.to_csv(path, index=False)

    print(
        f"{path.name:<25} "
        f"Before: {before:<6} "
        f"After: {len(df):<6} "
        f"Removed: {removed}"
    )

print("=" * 70)
print("✅ Filtering completed")
print("=" * 70)
