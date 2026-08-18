import pandas as pd
import plotly.express as px
import streamlit as st

try:
    from src.screener.presets import (
        debt_free_bluechip,
        dividend_champion,
        growth_accelerator,
        quality_compounder,
        turnaround_watch,
        value_pick,
    )
except ModuleNotFoundError:
    from src.screener.presets import (
        debt_free_bluechip,
        dividend_champion,
        growth_accelerator,
        quality_compounder,
        turnaround_watch,
        value_pick,
    )
from utils.db import get_companies, get_ratios, get_sectors
from utils.theme import (
    apply_chart_theme,
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

PRESETS = {
    "None": None,
    "Quality Compounder": quality_compounder,
    "Value Pick": value_pick,
    "Growth Accelerator": growth_accelerator,
    "Dividend Champion": dividend_champion,
    "Debt Free Bluechip": debt_free_bluechip,
    "Turnaround Watch": turnaround_watch,
}

ratios = get_ratios()

companies = get_companies()
sectors = get_sectors()

required_ratio_cols = {"company_id", "return_on_equity_pct", "debt_to_equity", "free_cash_flow_cr"}
missing_ratio_cols = sorted(list(required_ratio_cols - set(ratios.columns)))
if missing_ratio_cols:
    st.error(
        "Screener cannot run because required ratio columns are missing: "
        + ", ".join(missing_ratio_cols)
    )
    st.stop()

if companies.empty or not {"id", "company_name"}.issubset(companies.columns):
    st.error("Screener cannot run because companies data is unavailable.")
    st.stop()

if sectors.empty or not {"company_id", "broad_sector"}.issubset(sectors.columns):
    st.warning("Sector data is incomplete. Sector filter will be limited.")
    sectors = pd.DataFrame(columns=["company_id", "broad_sector"])

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

if "year" in df.columns:
    df["_year_num"] = pd.to_numeric(df["year"].astype(str).str.extract(r"(\d{4})", expand=False), errors="coerce")
    df = df.sort_values(["company_id", "_year_num"]).groupby("company_id", as_index=False).tail(1)

st.sidebar.header("Filters")

preset_name = st.sidebar.selectbox(
    "Preset Selector",
    list(PRESETS.keys()),
    help="Applies existing screening preset logic before custom threshold filters.",
)

if PRESETS[preset_name] is not None:
    try:
        df = PRESETS[preset_name](df.copy())
    except KeyError as exc:
        st.warning(f"Selected preset requires unavailable column: {exc}. Showing available rows.")

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

if filtered.empty:
    render_section_header("Screen Results")
    st.info("No companies match current screener settings. Relax the filters or choose a different preset.")
    st.dataframe(
        pd.DataFrame(
            columns=[
                "company_id",
                "company_name",
                "broad_sector",
                "return_on_equity_pct",
                "debt_to_equity",
                "free_cash_flow_cr",
            ]
        ),
        width="stretch",
    )
    st.download_button(
        "Download CSV",
        filtered.to_csv(index=False),
        file_name="screener.csv",
        mime="text/csv",
    )
    st.stop()

sector_filter = st.sidebar.selectbox(
    "Sector",
    ["All"] + sorted(filtered["broad_sector"].dropna().astype(str).unique().tolist()),
    help="Optional sector-level filter for screener results.",
)

if sector_filter != "All":
    filtered = filtered[filtered["broad_sector"] == sector_filter]

sort_col = st.selectbox(
    "Sort Results By",
    ["return_on_equity_pct", "debt_to_equity", "free_cash_flow_cr"],
    help="Sort key for result ranking.",
)
sort_dir = st.radio("Sort Order", ["Descending", "Ascending"], horizontal=True)
filtered = filtered.sort_values(sort_col, ascending=(sort_dir == "Ascending"))

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
    fcf_label = "N/A" if pd.isna(median_fcf) else f"â‚¹{median_fcf:,.2f} Cr"
    render_metric_card("Median FCF", fcf_label, "Cash generation")

if not filtered.empty:
    viz_metric = st.selectbox(
        "Distribution Metric",
        ["return_on_equity_pct", "debt_to_equity", "free_cash_flow_cr"],
        help="Visualizes distribution of the selected metric across screened companies.",
    )
    hist = px.histogram(
        filtered,
        x=viz_metric,
        nbins=20,
        title=f"Distribution of {viz_metric}",
    )
    apply_chart_theme(hist, x_title=viz_metric, y_title="Company Count", show_legend=False)
    st.plotly_chart(hist, width="stretch")

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

search = st.text_input("Search Results", placeholder="Search by ticker or company name")
if search:
    display = display[
        display["company_id"].astype(str).str.contains(search, case=False, na=False)
        | display["company_name"].astype(str).str.contains(search, case=False, na=False)
    ]

page_size = st.selectbox("Rows per page", [10, 20, 50], index=1, help="Simple pagination control for the result table.")
total_pages = max(1, (len(display) - 1) // page_size + 1)
page = st.number_input("Page", min_value=1, max_value=total_pages, value=1)
start = (page - 1) * page_size
end = start + page_size

st.dataframe(
    display.iloc[start:end],
    width="stretch",
)
csv = filtered.to_csv(index=False)
st.download_button(
    "Download CSV",
    csv,
    file_name="screener.csv",
    mime="text/csv",
)

