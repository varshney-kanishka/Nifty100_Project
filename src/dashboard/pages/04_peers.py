import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from dashboard.utils.db import get_peers
from dashboard.utils.db import get_ratios
from dashboard.utils.db import get_companies

st.title("Peer Comparison")

st.markdown("Compare companies within the same peer group.")
peer = get_peers()

ratios = get_ratios()

companies = get_companies()
if peer.empty:

    st.warning("Peer groups not available.")

    st.stop()
groups = sorted(peer["peer_group_name"].dropna().unique())

selected_group = st.selectbox(

    "Select Peer Group",

    groups

)
group_df = peer[
    peer["peer_group_name"] == selected_group
]
company = st.selectbox(

    "Select Company",

    group_df["company_id"]

)
company_ratio = ratios[
    ratios["company_id"] == company
]

company_ratio = company_ratio.tail(1)
metrics = [

    "ROE",

    "ROCE",

    "NPM",

    "D/E",

    "FCF",

    "PAT",

    "Revenue",

    "Score"

]

company_values = [

    70,

    65,

    60,

    55,

    75,

    80,

    72,

    78

]

peer_average = [

    60,

    60,

    55,

    60,

    65,

    70,

    68,

    70

]
fig = go.Figure()

fig.add_trace(

    go.Scatterpolar(

        r=company_values,

        theta=metrics,

        fill="toself",

        name=company

    )

)

fig.add_trace(

    go.Scatterpolar(

        r=peer_average,

        theta=metrics,

        name="Peer Average"

    )

)

fig.update_layout(

    polar=dict(

        radialaxis=dict(

            visible=True,

            range=[0,100]

        )

    ),

    showlegend=True

)

st.plotly_chart(

    fig,

    use_container_width=True

)
table = group_df.merge(

    companies,

    left_on="company_id",

    right_on="company_id",

    how="left"

)

st.subheader("Peer Companies")

st.dataframe(table)
benchmark = table[
    table["is_benchmark"] == 1
]

st.subheader("Benchmark Company")

st.dataframe(benchmark)    