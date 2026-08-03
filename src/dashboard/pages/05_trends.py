import streamlit as st

st.title("📈 Trends")

st.write("Trend Analysis")

import streamlit as st
import plotly.express as px

from utils.db import get_companies
from utils.db import get_pl
st.title("Trend Analysis")
companies = get_companies()

ticker = st.selectbox(
    "Select Company",
    options=companies["id"].tolist(),
    format_func=lambda ticker: (
        f"{ticker} — "
        f"{companies.loc[companies['id'] == ticker, 'company_name'].iloc[0]}"
    ),
)

pl = get_pl(ticker)
if pl.empty:
    st.warning("No historical data is available for this company.")
    st.stop()
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

st.plotly_chart(
    fig,
    use_container_width=True
)
