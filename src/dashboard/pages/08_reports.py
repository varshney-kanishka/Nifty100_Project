import streamlit as st

st.title("📄 Annual Reports")
st.write("Annual Reports")
import streamlit as st

from utils.db import get_companies
st.title("Annual Reports")

companies = get_companies()

ticker = st.selectbox(
    "Company",
    options=companies["id"].tolist(),
    format_func=lambda ticker: (
        f"{ticker} — "
        f"{companies.loc[companies['id'] == ticker, 'company_name'].iloc[0]}"
    ),
)

ticker = st.selectbox(

    "Company",

    companies["id"]

)
st.table({

    "Year":[2024,2023,2022],

    "Report":[

        "Available",

        "Available",

        "Unavailable"

    ]

})
