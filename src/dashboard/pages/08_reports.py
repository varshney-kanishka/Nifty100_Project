import pandas as pd
import streamlit as st
from utils.db import get_companies
from utils.theme import (
    apply_theme,
    render_metric_card,
    render_page_header,
    render_section_header,
)

apply_theme()

render_page_header(
    "Annual Reports",
    "Coverage overview for company reporting availability across recent fiscal years.",
    status="Documenting coverage",
)


companies = get_companies()

ticker = st.selectbox(
    "Company",
    options=companies["id"].tolist(),
    format_func=lambda ticker: (
        f"{ticker} — "
        f"{companies.loc[companies['id'] == ticker, 'company_name'].iloc[0]}"
    ),
)

render_section_header("Report Coverage")
st.caption(f"Showing placeholder report availability timeline for {ticker}.")

report_df = pd.DataFrame(
    {
        "Year": [2024, 2023, 2022],
        "Report": ["Available", "Available", "Unavailable"],
    }
)

summary_cols = st.columns(3)
with summary_cols[0]:
    render_metric_card("Available Reports", int((report_df["Report"] == "Available").sum()), "Last 3 fiscal years")
with summary_cols[1]:
    render_metric_card("Missing Reports", int((report_df["Report"] == "Unavailable").sum()), "Requires follow-up")
with summary_cols[2]:
    render_metric_card("Coverage Ratio", f"{((report_df['Report'] == 'Available').mean() * 100):.0f}%", "Availability share")

st.dataframe(report_df, use_container_width=True)
