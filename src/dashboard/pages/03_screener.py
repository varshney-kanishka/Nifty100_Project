import streamlit as st
import pandas as pd

from utils.db import get_ratios
from utils.db import get_companies
from utils.db import get_sectors
st.title("Financial Screener")

st.markdown("Filter Nifty 100 companies using financial metrics.")

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
st.subheader(
    f"{len(filtered)} Companies Match"
)
st.dataframe(
    filtered[
        [
            "company_id",
            "company_name",
            "broad_sector",
            "return_on_equity_pct",
            "debt_to_equity",
            "free_cash_flow_cr",
        ]
    ]
)
csv = filtered.to_csv(index=False)

st.download_button(

    "Download CSV",

    csv,

    file_name="screener.csv",

    mime="text/csv",

)
