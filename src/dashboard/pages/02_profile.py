import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils.db import get_bs, get_company_list, get_company_profile, get_pl, get_pros_cons, get_ratios, get_sectors


st.title("Company Profile")


def _extract_year(value):
    if pd.isna(value):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        import re

        match = re.search(r"(\d{4})", value)
        if match:
            return int(match.group(1))
    return None


def _safe_numeric(series):
    return pd.to_numeric(series, errors="coerce")


def _format_metric(value, suffix="", decimals=2):
    if value is None or pd.isna(value):
        return "N/A"
    return f"{float(value):.{decimals}f}{suffix}"


def _build_roce_history(company_id):
    pl_df = get_pl(company_id)
    bs_df = get_bs(company_id)

    if pl_df.empty or bs_df.empty:
        return pd.DataFrame(columns=["year", "roce_pct"])

    pl_working = pl_df.copy()
    bs_working = bs_df.copy()
    pl_working["year_num"] = pl_working["year"].apply(_extract_year)
    bs_working["year_num"] = bs_working["year"].apply(_extract_year)

    merged = pl_working.merge(
        bs_working[["company_id", "year_num", "equity_capital", "reserves", "borrowings"]],
        on=["company_id", "year_num"],
        how="inner",
    )

    if merged.empty:
        return pd.DataFrame(columns=["year", "roce_pct"])

    if "operating_profit" in merged.columns:
        merged["capital_employed"] = (
            _safe_numeric(merged["equity_capital"]) + _safe_numeric(merged["reserves"]) + _safe_numeric(merged["borrowings"])
        )
        merged["roce_pct"] = (_safe_numeric(merged["operating_profit"]) / merged["capital_employed"]) * 100
    else:
        merged["roce_pct"] = pd.NA

    result = merged[["year", "roce_pct"]].dropna(subset=["roce_pct"])
    result = result.sort_values("year")
    return result


def _build_revenue_cagr(pl_df):
    if pl_df.empty or "sales" not in pl_df.columns:
        return None

    working = pl_df.copy()
    working["year_num"] = working["year"].apply(_extract_year)
    working = working.dropna(subset=["year_num", "sales"]).sort_values("year_num")

    if working.shape[0] < 2:
        return None

    start_value = float(working.iloc[0]["sales"])
    end_value = float(working.iloc[-1]["sales"])
    if start_value <= 0 or end_value <= 0:
        return None

    periods = max(1, working.shape[0] - 1)
    return round(((end_value / start_value) ** (1 / periods) - 1) * 100, 2)


company_list = get_company_list()
if company_list.empty:
    st.warning("No company data is available yet.")
    st.stop()

search_value = st.text_input("Search company name or ticker", placeholder="Try AIRTEL or HDFCBANK")

if search_value:
    filtered = company_list[
        company_list["company_name"].str.contains(search_value, case=False, na=False)
        | company_list["id"].str.contains(search_value, case=False, na=False)
    ]
else:
    filtered = company_list

if filtered.empty:
    st.warning("Ticker not found. Please try another.")
    st.stop()

selected_ticker = st.selectbox(
    "Select company",
    options=filtered["id"].tolist(),
    format_func=lambda ticker: f"{ticker} — {company_list.loc[company_list['id'] == ticker, 'company_name'].iat[0]}",
)

profile = get_company_profile(selected_ticker)
if profile.empty:
    st.warning("Ticker not found. Please try another.")
    st.stop()

company_info = profile.iloc[0]
company_name = company_info.get("company_name", selected_ticker)
st.subheader(company_name)

sector_df = get_sectors()
sector_info = pd.DataFrame()
if not sector_df.empty and "company_id" in sector_df.columns:
    sector_info = sector_df[sector_df["company_id"] == selected_ticker]

company_meta = st.columns([1.2, 1.2, 1.2, 1.2])
company_meta[0].metric("Ticker", selected_ticker)
company_meta[1].metric("Sector", sector_info.iloc[0]["broad_sector"] if not sector_info.empty and "broad_sector" in sector_info.columns else "N/A")
company_meta[2].metric("Sub-sector", sector_info.iloc[0]["sub_sector"] if not sector_info.empty and "sub_sector" in sector_info.columns else "N/A")
company_meta[3].metric("Website", company_info.get("website", "N/A") if pd.notna(company_info.get("website", None)) else "N/A")

if "about_company" in profile.columns and pd.notna(company_info.get("about_company", None)):
    st.markdown("### About company")
    st.write(company_info["about_company"])

ratios = get_ratios(ticker=selected_ticker)
if ratios.empty:
    st.info("No financial ratio history is available for this company.")
else:
    ratios = ratios.copy()
    ratios["year_sort"] = ratios["year"].apply(_extract_year)
    ratios = ratios.sort_values(["year_sort", "year"], ascending=[False, False])
    latest = ratios.iloc[0]

    st.markdown("---")
    st.subheader("Key performance indicators")
    metric_columns = st.columns(3)
    card_values = [
        ("ROE", latest.get("return_on_equity_pct", None), "%"),
        ("ROCE", company_info.get("roce_percentage", None), "%"),
        ("Net Profit Margin", latest.get("net_profit_margin_pct", None), "%"),
        ("Debt to Equity", latest.get("debt_to_equity", None), "x"),
        ("Revenue CAGR", None, "%"),
        ("Free Cash Flow", latest.get("free_cash_flow_cr", None), "₹ Cr"),
    ]

    for index, (label, value, suffix) in enumerate(card_values):
        if label == "Revenue CAGR":
            pl_df = get_pl(selected_ticker)
            value = _build_revenue_cagr(pl_df)
        display_value = _format_metric(value, suffix=suffix)
        metric_columns[index % 3].metric(label, display_value)

    st.markdown("---")
    st.subheader("Performance trends")

    pl_df = get_pl(selected_ticker)
    if not pl_df.empty and "sales" in pl_df.columns:
        revenue_history = pl_df[["year", "sales"]].copy()
        revenue_history["year_num"] = revenue_history["year"].apply(_extract_year)
        revenue_history = revenue_history.dropna(subset=["year_num", "sales"]).sort_values("year_num")
        revenue_history = revenue_history.tail(10)
        revenue_fig = px.bar(
            revenue_history,
            x="year",
            y="sales",
            text="sales",
            title="10-year Revenue",
        )
        revenue_fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
        st.plotly_chart(revenue_fig, use_container_width=True)

    if not pl_df.empty and "net_profit" in pl_df.columns:
        profit_history = pl_df[["year", "net_profit"]].copy()
        profit_history["year_num"] = profit_history["year"].apply(_extract_year)
        profit_history = profit_history.dropna(subset=["year_num", "net_profit"]).sort_values("year_num")
        profit_history = profit_history.tail(10)
        profit_fig = px.bar(
            profit_history,
            x="year",
            y="net_profit",
            text="net_profit",
            title="10-year Net Profit",
        )
        profit_fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
        st.plotly_chart(profit_fig, use_container_width=True)

    roe_history = ratios[["year", "return_on_equity_pct"]].copy().rename(columns={"return_on_equity_pct": "roe"})
    roce_history = _build_roce_history(selected_ticker).rename(columns={"roce_pct": "roce"})
    chart_df = roe_history.merge(roce_history, on="year", how="outer")
    chart_df = chart_df.dropna(subset=["roe", "roce"], how="all")
    if not chart_df.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=chart_df["year"], y=chart_df["roe"], mode="lines+markers", name="ROE", yaxis="y"))
        fig.add_trace(go.Scatter(x=chart_df["year"], y=chart_df["roce"], mode="lines+markers", name="ROCE", yaxis="y2"))
        fig.update_layout(
            title="ROE vs ROCE",
            yaxis=dict(title="ROE (%)"),
            yaxis2=dict(title="ROCE (%)", overlaying="y", side="right"),
        )
        st.plotly_chart(fig, use_container_width=True)

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
                        st.markdown(
                            f"<span style='display:inline-block;padding:4px 10px;margin:4px 0;border-radius:999px;background:#e8f5e9;color:#2e7d32;'>{item}</span>",
                            unsafe_allow_html=True,
                        )
    if "cons" in pros_cons.columns:
        st.markdown("**Cons**")
        for _, row in pros_cons.iterrows():
            if pd.notna(row["cons"]):
                for item in str(row["cons"]).split("\n"):
                    item = item.strip()
                    if item:
                        st.markdown(
                            f"<span style='display:inline-block;padding:4px 10px;margin:4px 0;border-radius:999px;background:#ffebee;color:#c62828;'>{item}</span>",
                            unsafe_allow_html=True,
                        )
