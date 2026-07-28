import pandas as pd
import plotly.express as px
import streamlit as st

from utils.db import get_companies
from utils.db import get_years
from utils.db import get_ratios
from utils.db import get_sectors

st.title("Nifty 100 Analytics Dashboard")

years = get_years()
selected_year = st.selectbox("Select year", years, index=len(years) - 1 if years else 0)

ratios = get_ratios(year=selected_year)
companies = get_companies()
sectors = get_sectors()

st.markdown(f"## Market snapshot for {selected_year}")

if ratios.empty:
    st.warning(f"No financial ratios are available for {selected_year}.")
    st.stop()

# KPI cards

def safe_mean(series):
    numeric = pd.to_numeric(series, errors="coerce").dropna()
    return round(numeric.mean(), 2) if not numeric.empty else None

kpis = {
    "Average ROE": (ratios, "return_on_equity_pct", "%"),
    "Average Net Profit Margin": (ratios, "net_profit_margin_pct", "%"),
    "Average Operating Profit Margin": (ratios, "operating_profit_margin_pct", "%"),
    "Average Debt to Equity": (ratios, "debt_to_equity", "x"),
    "Average Interest Coverage": (ratios, "interest_coverage", "x"),
    "Companies in Year": (ratios["company_id"].dropna().nunique(), None, ""),
}

cols = st.columns(3)
for index, (label, spec) in enumerate(kpis.items()):
    value = None
    unit = ""
    if spec[1] is None:
        value = spec[0]
        unit = spec[2]
    else:
        value = safe_mean(spec[0][spec[1]])
        unit = spec[2]

    cols[index % 3].metric(label, f"{value}{unit}" if value is not None else "N/A")

st.markdown("---")

# Sector donut chart

if not sectors.empty and "company_id" in sectors.columns and "broad_sector" in sectors.columns:
    active_sector = sectors[sectors["company_id"].isin(ratios["company_id"].dropna())]
    if not active_sector.empty:
        if "index_weight_pct" in active_sector.columns:
            sector_agg = active_sector.groupby("broad_sector", dropna=False)["index_weight_pct"].sum().reset_index()
            sector_agg = sector_agg.rename(columns={"index_weight_pct": "weight"})
        else:
            sector_agg = active_sector.groupby("broad_sector", dropna=False)["company_id"].count().reset_index()
            sector_agg = sector_agg.rename(columns={"company_id": "weight"})

        sector_agg = sector_agg.sort_values("weight", ascending=False)

        fig = px.pie(
            sector_agg,
            names="broad_sector",
            values="weight",
            title="Sector distribution",
            hole=0.45,
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Sector information is not available for the companies in the selected year.")
else:
    st.info("Sector data is missing or incomplete.")

st.markdown("---")

# Top 5 companies table

top5 = ratios.sort_values("return_on_equity_pct", ascending=False).head(5)
if not top5.empty:
    if not companies.empty and "company_name" in companies.columns:
        top5 = top5.merge(
            companies[["id", "company_name"]],
            left_on="company_id",
            right_on="id",
            how="left",
        )
    display_columns = [col for col in ["company_id", "company_name", "return_on_equity_pct", "net_profit_margin_pct", "operating_profit_margin_pct"] if col in top5.columns]
    st.subheader("Top 5 companies by ROE")
    st.dataframe(top5[display_columns].reset_index(drop=True), use_container_width=True)
else:
    st.info("No top company data is available for this year.")
