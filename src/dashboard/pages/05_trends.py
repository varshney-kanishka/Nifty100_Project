import pandas as pd
import plotly.express as px
import streamlit as st
from utils.db import get_companies, get_pl
from utils.theme import (
    apply_chart_theme,
    apply_theme,
    format_currency,
    render_metric_card,
    render_page_header,
    render_section_header,
)

apply_theme()

render_page_header(
    "Trend Analysis",
    "Review multi-year operating trends across revenue, profit, and business momentum.",
    status="Historical view",
)
st.caption("Compare historical movements across major profit-and-loss metrics for any covered company.")

companies = get_companies()

ticker = st.selectbox(
    "Select Company",
    options=companies["id"].tolist(),
    format_func=lambda ticker: (
        f"{ticker} â€” "
        f"{companies.loc[companies['id'] == ticker, 'company_name'].iloc[0]}"
    ),
)

pl = get_pl(ticker)
if pl.empty:
    st.warning("No historical data is available for this company.")
    st.stop()

pl = pl.copy()
if "year" in pl.columns:
    pl["year_num"] = pl["year"].astype(str).str.extract(r"(\d{4})", expand=False)
    pl["year_num"] = pd.to_numeric(pl["year_num"], errors="coerce")
    pl = pl.sort_values("year_num")

metric = st.selectbox(

    "Metric",

    [
        "sales",
        "net_profit",
        "operating_profit"
    ]

)
fig = px.line(

    pl,

    x="year",

    y=metric,

    markers=True,

    title=metric

)

fig.update_layout(
    title=metric,
)
apply_chart_theme(fig, x_title="Year", y_title=metric.replace("_", " ").title(), show_legend=False)

render_section_header("Trend Snapshot")
latest = pl.dropna(subset=[metric]).tail(1)
previous = pl.dropna(subset=[metric]).tail(2).head(1)
latest_val = float(latest.iloc[0][metric]) if not latest.empty else None
prev_val = float(previous.iloc[0][metric]) if not previous.empty else None
delta_text = "N/A"
if latest_val is not None and prev_val is not None:
    delta_text = f"YoY change: {latest_val - prev_val:,.2f}"

summary_cols = st.columns(3)
with summary_cols[0]:
    render_metric_card("Selected Metric", metric.replace("_", " ").title(), "Current chart")
with summary_cols[1]:
    render_metric_card("Latest Value", format_currency(latest_val), delta_text)
with summary_cols[2]:
    render_metric_card("Data Points", int(pl[metric].notna().sum()), "Historical observations")

st.plotly_chart(
    fig,
    width="stretch"
)

