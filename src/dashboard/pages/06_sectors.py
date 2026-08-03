import streamlit as st

st.title("🏭 Sectors")

st.write("Sector Analysis")

import streamlit as st
import plotly.express as px

from utils.db import get_sectors
from utils.db import get_companies
from utils.db import get_ratios
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
import pandas as pd

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
fig = px.scatter(
    filtered,
    x="asset_turnover",
    y="return_on_equity_pct",
    size="bubble_size",
    hover_name="company_id",
    color="broad_sector",
    title=f"{sector} Company Analysis",
)

st.plotly_chart(
    fig,
    use_container_width=True,
)