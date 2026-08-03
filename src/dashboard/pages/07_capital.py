import streamlit as st

st.title("💰 Capital Allocation")

st.write("Capital Allocation Map")

import streamlit as st
import plotly.express as px

import pandas as pd
import plotly.express as px
import streamlit as st

from utils.db import get_ratios

st.title("💰 Capital Allocation")
st.write("Capital Allocation Map")

df = get_ratios()

if df.empty:
    st.warning("No financial-ratio data is available.")
    st.stop()

df = df.copy()

df["Pattern"] = "Balanced"

df["treemap_value"] = (
    pd.to_numeric(
        df["free_cash_flow_cr"],
        errors="coerce",
    )
    .abs()
    .fillna(0)
)

df = df[df["treemap_value"] > 0]

if df.empty:
    st.info("No valid capital-allocation values are available.")
else:
    fig = px.treemap(
        df,
        path=["Pattern", "company_id"],
        values="treemap_value",
        color="return_on_equity_pct",
        hover_data=[
            "year",
            "free_cash_flow_cr",
            "debt_to_equity",
        ],
        title="Capital Allocation by Company",
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )