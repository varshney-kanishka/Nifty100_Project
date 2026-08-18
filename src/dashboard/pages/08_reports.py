import pandas as pd
import streamlit as st
from utils.db import get_companies, get_company_profile
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
        f"{ticker} â€” "
        f"{companies.loc[companies['id'] == ticker, 'company_name'].iloc[0]}"
    ),
)

render_section_header("Report Coverage")
st.caption("Coverage is derived from available company profile links in the database.")

company_profile = get_company_profile(ticker)

if company_profile.empty:
    st.info("No profile records found for this company.")
    st.stop()

profile = company_profile.iloc[0]

report_df = pd.DataFrame(
    {
        "Source": ["Company Website", "NSE Profile", "BSE Profile"],
        "Link": [
            profile.get("website"),
            profile.get("nse_profile"),
            profile.get("bse_profile"),
        ],
    }
)
report_df["Available"] = report_df["Link"].notna() & (report_df["Link"].astype(str).str.strip() != "")

summary_cols = st.columns(3)
with summary_cols[0]:
    render_metric_card("Available Sources", int(report_df["Available"].sum()), "Current link coverage")
with summary_cols[1]:
    render_metric_card("Missing Sources", int((~report_df["Available"]).sum()), "Needs enrichment")
with summary_cols[2]:
    render_metric_card("Coverage Ratio", f"{(report_df['Available'].mean() * 100):.0f}%", "Availability share")

display = report_df.copy()
display["Link"] = display["Link"].fillna("Not available")
display["Available"] = display["Available"].map({True: "Yes", False: "No"})
st.dataframe(display, width="stretch")

