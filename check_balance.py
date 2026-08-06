import pandas as pd

df = pd.read_excel(
    "data/raw/balancesheet.xlsx",
    header=1
)

print(
    df[df["company_id"]=="BEL"][[
        "company_id",
        "year",
        "equity_capital",
        "reserves",
        "total_assets"
    ]]
)
print(
    df[
        df["company_id"] == "BEL"
    ][["company_id", "year"]]
)