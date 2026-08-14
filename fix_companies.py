import pandas as pd
from pathlib import Path

file = Path("data/raw/companies.xlsx")

# Read existing master
df = pd.read_excel(file, header=1)

# Normalize column names
df.columns = df.columns.astype(str).str.strip()

missing_companies = [
    {
        "id": "ULTRACEMCO",
        "company_name": "UltraTech Cement Ltd"
    },
    {
        "id": "UNIONBANK",
        "company_name": "Union Bank of India"
    },
    {
        "id": "UNITDSPR",
        "company_name": "United Spirits Ltd"
    },
    {
        "id": "VBL",
        "company_name": "Varun Beverages Ltd"
    },
    {
        "id": "VEDL",
        "company_name": "Vedanta Ltd"
    },
    {
        "id": "WIPRO",
        "company_name": "Wipro Ltd"
    },
    {
        "id": "ZOMATO",
        "company_name": "Zomato Ltd"
    },
    {
        "id": "ZYDUSLIFE",
        "company_name": "Zydus Lifesciences Ltd"
    }
]

existing_ids = set(
    df["id"]
    .dropna()
    .astype(str)
    .str.strip()
    .str.upper()
)

rows_to_add = []

for company in missing_companies:
    if company["id"] not in existing_ids:
        row = {column: pd.NA for column in df.columns}
        row["id"] = company["id"]
        row["company_name"] = company["company_name"]
        rows_to_add.append(row)

if rows_to_add:
    df = pd.concat(
        [df, pd.DataFrame(rows_to_add)],
        ignore_index=True
    )

# Remove accidental duplicate IDs
df = df.drop_duplicates(
    subset=["id"],
    keep="first"
).reset_index(drop=True)

# Write back with the same 12-column structure
with pd.ExcelWriter(file, engine="openpyxl") as writer:
    df.to_excel(
        writer,
        sheet_name="Companies",
        index=False,
        startrow=1
    )

print("Updated:", file)
print("Rows:", len(df))
print("Unique IDs:", df["id"].nunique())
print()
print("Added companies:")
print(df[df["id"].isin([x["id"] for x in missing_companies])]
      [["id", "company_name"]]
      .to_string(index=False))
