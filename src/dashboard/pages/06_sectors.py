import pandas as pd
import plotly.express as px
import streamlit as st
from utils.db import get_companies, get_ratios, get_sectors
from utils.theme import (
    apply_chart_theme,
    apply_theme,
    format_percentage,
    render_metric_card,
    render_page_header,
    render_section_header,
)

apply_theme()

render_page_header(
    "Sector Analysis",
    "Compare company performance and capital efficiency by sector and business model.",
    status="Portfolio structure",
)

companies = get_companies()
sectors = get_sectors()
ratios = get_ratios()
df = ratios.merge(

    sectors,

    on="company_id",

    how="left"

)
sector = st.selectbox(

    "Sector",

    sorted(df["broad_sector"].dropna().unique())

)
filtered = df[
    df["broad_sector"] == sector
]
filtered = filtered.copy()

filtered["bubble_size"] = (
    pd.to_numeric(
        filtered["free_cash_flow_cr"],
        errors="coerce",
    )
    .abs()
    .fillna(0)
)

filtered = filtered[
    filtered["bubble_size"] > 0
]
render_section_header("Sector Snapshot")
summary_cols = st.columns(3)
with summary_cols[0]:
    render_metric_card("Companies", int(filtered["company_id"].nunique()) if not filtered.empty else 0, "In selected sector")
with summary_cols[1]:
    sector_roe = pd.to_numeric(filtered.get("return_on_equity_pct", pd.Series(dtype=float)), errors="coerce").median()
    render_metric_card("Median ROE", format_percentage(sector_roe), "Sector quality")
with summary_cols[2]:
    sector_turnover = pd.to_numeric(filtered.get("asset_turnover", pd.Series(dtype=float)), errors="coerce").median()
    turnover_text = "N/A" if pd.isna(sector_turnover) else f"{sector_turnover:.2f}x"
    render_metric_card("Median Asset Turnover", turnover_text, "Operating efficiency")

fig = px.scatter(
    filtered,
    x="asset_turnover",
    y="return_on_equity_pct",
    size="bubble_size",
    hover_name="company_id",
    color="broad_sector",
    title=f"{sector} Company Analysis",
)

fig.update_layout(
    title=f"{sector} Company Analysis",
)
apply_chart_theme(fig, x_title="Asset Turnover", y_title="ROE (%)")

st.plotly_chart(
    fig,
    width="stretch",
)

render_section_header("Top ROE Companies in Sector")
leader_cols = [col for col in ["company_id", "return_on_equity_pct", "asset_turnover", "free_cash_flow_cr"] if col in filtered.columns]
leaders = filtered[leader_cols].copy()
if "return_on_equity_pct" in leaders.columns:
    leaders = leaders.sort_values("return_on_equity_pct", ascending=False)
leaders = leaders.head(10)
for col in ["return_on_equity_pct", "asset_turnover", "free_cash_flow_cr"]:
    if col in leaders.columns:
        leaders[col] = pd.to_numeric(leaders[col], errors="coerce").round(2)

st.plotly_chart(
    apply_chart_theme(
        px.bar(
        leaders,
        x="company_id",
        y="return_on_equity_pct" if "return_on_equity_pct" in leaders.columns else leaders.columns[1],
        color="return_on_equity_pct" if "return_on_equity_pct" in leaders.columns else None,
        color_continuous_scale="Blues",
        title="Top 10 by ROE",
        ),
        x_title="Company",
        y_title="ROE (%)",
    ).update_layout(coloraxis_showscale=False),
    width="stretch",
)

st.dataframe(leaders.reset_index(drop=True), width="stretch")
