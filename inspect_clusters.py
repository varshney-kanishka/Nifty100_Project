import pandas as pd

df = pd.read_csv("output/company_clusters.csv")

cols = [
    "company_id",
    "company_name",
    "sector",
    "net_profit_margin_pct",
    "operating_profit_margin_pct",
    "debt_to_equity",
    "interest_coverage",
    "free_cash_flow_cr",
    "cash_from_operations_cr",
    "market_cap_crore",
]

for cluster in sorted(df["cluster"].unique()):
    print("\n" + "=" * 70)
    print(f"CLUSTER {cluster}")
    print("=" * 70)

    cluster_df = (
        df[df["cluster"] == cluster][cols]
        .sort_values("company_name")
    )

    print(cluster_df.to_string(index=False))