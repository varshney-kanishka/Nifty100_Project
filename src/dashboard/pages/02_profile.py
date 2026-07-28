import pandas as pd
import plotly.express as px
import streamlit as st

from utils.db import get_company_list
from utils.db import get_company_profile
from utils.db import get_pros_cons
from utils.db import get_ratios
from utils.db import get_sectors

st.title("🏢 Company Profile")

company_list = get_company_list()
search_value = st.text_input("Search ticker or company name")

if search_value:
    filtered = company_list[
        company_list["company_name"].str.contains(search_value, case=False, na=False)
        | company_list["id"].str.contains(search_value, case=False, na=False)
    ]
else:
    filtered = company_list

if filtered.empty:
    st.warning("No matching company found. Try a different search term.")
    st.stop()

selected_ticker = st.selectbox(
    "Select company",
    options=filtered["id"].tolist(),
    format_func=lambda ticker: f"{ticker} — {company_list.loc[company_list.id == ticker, 'company_name'].iat[0]}",
)

profile = get_company_profile(selected_ticker)
if profile.empty:
    st.error("Company profile not found.")
    st.stop()

company_info = profile.iloc[0]

cols = st.columns([1, 3])
with cols[0]:
    if "company_logo" in profile.columns and pd.notna(company_info.get("company_logo", None)):
        st.image(company_info["company_logo"], width=180)
with cols[1]:
    st.header(company_info.get("company_name", selected_ticker))
    st.write(f"**Ticker:** {selected_ticker}")
    if "website" in profile.columns and pd.notna(company_info.get("website", None)):
        st.markdown(f"[Website]({company_info['website']})")
    if "nse_profile" in profile.columns and pd.notna(company_info.get("nse_profile", None)):
        st.markdown(f"[NSE profile]({company_info['nse_profile']})")
    if "bse_profile" in profile.columns and pd.notna(company_info.get("bse_profile", None)):
        st.markdown(f"[BSE profile]({company_info['bse_profile']})")

if "about_company" in profile.columns and pd.notna(company_info.get("about_company", None)):
    st.markdown("### About")
    st.write(company_info["about_company"])

sector_df = get_sectors()
company_sector = pd.DataFrame()
if not sector_df.empty and "company_id" in sector_df.columns:
    company_sector = sector_df[sector_df["company_id"] == selected_ticker]

if not company_sector.empty:
    sector_values = company_sector.iloc[0]
    st.markdown("### Sector details")
    sector_cols = st.columns(3)
    if "broad_sector" in sector_values.index:
        sector_cols[0].metric("Broad sector", sector_values["broad_sector"])
    if "sub_sector" in sector_values.index:
        sector_cols[1].metric("Sub-sector", sector_values["sub_sector"])
    if "index_weight_pct" in sector_values.index:
        sector_cols[2].metric("Index weight", f"{sector_values['index_weight_pct']}%")

ratios = get_ratios(ticker=selected_ticker)
if ratios.empty:
    st.warning("No financial ratio history is available for this company.")
    st.stop()

ratios = ratios.copy()
if "year" in ratios.columns:
    ratios["year_sort"] = (
        ratios["year"]
        .astype(str)
        .str.extract(r"(\d{4})")
        .iloc[:, 0]
        .astype(float)
        .fillna(0)
    )
    ratios = ratios.sort_values(["year_sort", "year"], ascending=[False, False])

latest = ratios.iloc[0]

st.markdown("---")
st.subheader("Latest performance KPIs")
metric_cols = st.columns(3)

card_values = [
    ("ROE", latest.get("return_on_equity_pct", None), "%"),
    ("Net Profit Margin", latest.get("net_profit_margin_pct", None), "%"),
    ("Operating Profit Margin", latest.get("operating_profit_margin_pct", None), "%"),
    ("Debt to Equity", latest.get("debt_to_equity", None), "x"),
    ("Interest Coverage", latest.get("interest_coverage", None), "x"),
    ("EPS", latest.get("earnings_per_share", None), ""),
]

for index, (label, value, suffix) in enumerate(card_values):
    display = f"{round(value, 2)}{suffix}" if pd.notna(value) else "N/A"
    metric_cols[index % 3].metric(label, display)

st.markdown("### Trend charts")
line_columns = [c for c in ["return_on_equity_pct", "net_profit_margin_pct"] if c in ratios.columns]
if line_columns:
    line_fig = px.line(
        ratios,
        x="year",
        y=line_columns,
        markers=True,
        title="ROE and Profit Margin history",
    )
    st.plotly_chart(line_fig, use_container_width=True)

bar_metrics = []
for row_label, col_name, unit in [
    ("Asset Turnover", "asset_turnover", "x"),
    ("Free Cash Flow", "free_cash_flow_cr", "₹cr"),
    ("Capex", "capex_cr", "₹cr"),
    ("Total Debt", "total_debt_cr", "₹cr"),
]:
    if col_name in latest.index and pd.notna(latest[col_name]):
        bar_metrics.append({"metric": row_label, "value": latest[col_name], "unit": unit})

if bar_metrics:
    bar_df = pd.DataFrame(bar_metrics)
    bar_fig = px.bar(
        bar_df,
        x="metric",
        y="value",
        text="value",
        title="Latest balance-sheet momentum",
    )
    bar_fig.update_traces(texttemplate="%{text:.2f}", textposition="outside")
    st.plotly_chart(bar_fig, use_container_width=True)

pros_cons = get_pros_cons(selected_ticker)
st.markdown("---")
st.subheader("Pros & Cons")
if pros_cons.empty:
    st.info("No pros and cons are available for this company.")
else:
    if "pros" in pros_cons.columns:
        st.markdown("**Pros**")
        for _, row in pros_cons.iterrows():
            if pd.notna(row["pros"]):
                for item in str(row["pros"]).split("\n"):
                    item = item.strip()
                    if item:
                        st.write(f"- {item}")
    if "cons" in pros_cons.columns:
        st.markdown("**Cons**")
        for _, row in pros_cons.iterrows():
            if pd.notna(row["cons"]):
                for item in str(row["cons"]).split("\n"):
                    item = item.strip()
                    if item:
                        st.write(f"- {item}")
