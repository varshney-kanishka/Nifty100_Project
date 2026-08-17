import pandas as pd
import streamlit as st
from utils.db import get_companies, get_ratios, get_sectors
from utils.theme import (
    apply_theme,
    format_percentage,
    format_ratio,
    render_metric_card,
    render_page_header,
    render_section_header,
)

apply_theme()

render_page_header(
    "Financial Screener",
    "Filter the Nifty 100 universe using quality, leverage, and cash-generation thresholds.",
    status="Screening model",
)
st.caption("Adjust thresholds in the sidebar to dynamically narrow the investable universe.")

ratios = get_ratios()

companies = get_companies()
sectors = get_sectors()
df = ratios.merge(
    companies[["id", "company_name"]],
    left_on="company_id",
    right_on="id",
    how="left",
)

df = df.merge(
    sectors[["company_id", "broad_sector"]],
    on="company_id",
    how="left",
)
st.sidebar.header("Filters")

roe = st.sidebar.slider(
    "Minimum ROE",
    0,
    50,
    15,
)

de = st.sidebar.slider(
    "Maximum Debt to Equity",
    0.0,
    5.0,
    1.0,
)

fcf = st.sidebar.number_input(
    "Minimum Free Cash Flow",
    value=0.0,
)
filtered = df.copy()

filtered = filtered[
    filtered["return_on_equity_pct"] >= roe
]

filtered = filtered[
    filtered["debt_to_equity"] <= de
]

filtered = filtered[
    filtered["free_cash_flow_cr"] >= fcf
]

render_section_header("Screen Results")

summary_cols = st.columns(4)
with summary_cols[0]:
    render_metric_card("Matching Companies", len(filtered), "Current filter set")
with summary_cols[1]:
    median_roe = pd.to_numeric(filtered.get("return_on_equity_pct", pd.Series(dtype=float)), errors="coerce").median()
    render_metric_card("Median ROE", format_percentage(median_roe), "Quality center")
with summary_cols[2]:
    median_de = pd.to_numeric(filtered.get("debt_to_equity", pd.Series(dtype=float)), errors="coerce").median()
    render_metric_card("Median Debt/Equity", format_ratio(median_de), "Leverage center")
with summary_cols[3]:
    median_fcf = pd.to_numeric(filtered.get("free_cash_flow_cr", pd.Series(dtype=float)), errors="coerce").median()
    fcf_label = "N/A" if pd.isna(median_fcf) else f"₹{median_fcf:,.2f} Cr"
    render_metric_card("Median FCF", fcf_label, "Cash generation")

display = filtered[
    [
        "company_id",
        "company_name",
        "broad_sector",
        "return_on_equity_pct",
        "debt_to_equity",
        "free_cash_flow_cr",
    ]
].copy()

for col in ["return_on_equity_pct", "debt_to_equity", "free_cash_flow_cr"]:
    if col in display.columns:
        display[col] = pd.to_numeric(display[col], errors="coerce").round(2)

st.dataframe(
    display,
    use_container_width=True,
)
csv = filtered.to_csv(index=False)
st.download_button(
    "Download CSV",
    csv,
    file_name="screener.csv",
    mime="text/csv",
)
