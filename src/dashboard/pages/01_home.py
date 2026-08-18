import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils.db import (
    get_companies,
    get_market_cap,
    get_ratios,
    get_sectors,
    get_stock_prices,
    get_years,
)
from utils.theme import (
    apply_chart_theme,
    apply_theme,
    format_currency,
    format_percentage,
    render_metric_card,
    render_page_header,
    render_section_header,
)


def _extract_year(value):
    if pd.isna(value):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        match = pd.Series([value]).str.extract(r"(\d{4})", expand=False).iat[0]
        return int(match) if pd.notna(match) else None
    return None


def _latest_by_company(df, year_col="year"):
    if df.empty or "company_id" not in df.columns:
        return df
    work = df.copy()
    if year_col in work.columns:
        work["_year_num"] = pd.to_numeric(work[year_col].map(_extract_year), errors="coerce")
        work = work.sort_values(["company_id", "_year_num"]).groupby("company_id", as_index=False).tail(1)
        work = work.drop(columns=["_year_num"], errors="ignore")
    return work


def _build_returns(prices_df):
    if prices_df.empty:
        return pd.DataFrame(columns=["company_id", "return_pct", "volatility_pct", "start_date", "end_date"])

    work = prices_df.copy()
    work["close_price"] = pd.to_numeric(work.get("close_price"), errors="coerce")
    work["date"] = pd.to_datetime(work.get("date"), errors="coerce")
    work = work.dropna(subset=["company_id", "date", "close_price"])
    if work.empty:
        return pd.DataFrame(columns=["company_id", "return_pct", "volatility_pct", "start_date", "end_date"])

    work = work.sort_values(["company_id", "date"])

    first_prices = work.groupby("company_id", as_index=False).first()[["company_id", "close_price", "date"]]
    first_prices = first_prices.rename(columns={"close_price": "start_price", "date": "start_date"})

    last_prices = work.groupby("company_id", as_index=False).last()[["company_id", "close_price", "date"]]
    last_prices = last_prices.rename(columns={"close_price": "end_price", "date": "end_date"})

    returns = first_prices.merge(last_prices, on="company_id", how="inner")
    returns = returns[returns["start_price"] > 0]
    returns["return_pct"] = ((returns["end_price"] - returns["start_price"]) / returns["start_price"]) * 100

    work["daily_return"] = work.groupby("company_id")["close_price"].pct_change()
    vol = (
        work.groupby("company_id", as_index=False)["daily_return"]
        .std()
        .rename(columns={"daily_return": "volatility_pct"})
    )
    vol["volatility_pct"] = vol["volatility_pct"] * 100

    return returns.merge(vol, on="company_id", how="left")


apply_theme()

render_page_header(
    "Nifty 100 Financial Intelligence",
    "Executive portfolio view with market structure, return distribution, company leaders, and sector ranking.",
    status="Production analytics",
)

years = get_years()
if not years:
    st.warning("No financial year data is available.")
    st.stop()

global_filters = st.session_state.get("global_filters", {})
selected_year = st.sidebar.selectbox("Analysis Year", years, index=len(years) - 1, help="Financial year used for ratio and market-cap analytics.")

ratios_raw = get_ratios(year=selected_year)
market_cap_raw = get_market_cap(year=_extract_year(selected_year))
companies = get_companies()
sectors = get_sectors()
prices = get_stock_prices()

if ratios_raw.empty:
    st.warning(f"No financial ratio records available for {selected_year}.")
    st.stop()

ratios = _latest_by_company(ratios_raw)
market_cap = _latest_by_company(market_cap_raw) if not market_cap_raw.empty else market_cap_raw
returns_df = _build_returns(prices)

base = ratios.merge(companies[["id", "company_name"]], left_on="company_id", right_on="id", how="left")
base = base.merge(sectors[["company_id", "broad_sector", "market_cap_category"]], on="company_id", how="left")
if not market_cap.empty:
    mc_cols = [c for c in ["company_id", "market_cap_crore", "pe_ratio", "pb_ratio", "dividend_yield_pct"] if c in market_cap.columns]
    base = base.merge(market_cap[mc_cols], on="company_id", how="left")
base = base.merge(returns_df[["company_id", "return_pct", "volatility_pct"]], on="company_id", how="left")

if global_filters.get("sector") and global_filters["sector"] != "All":
    base = base[base["broad_sector"] == global_filters["sector"]]
if global_filters.get("market_cap_category") and global_filters["market_cap_category"] != "All":
    base = base[base["market_cap_category"] == global_filters["market_cap_category"]]
if global_filters.get("company") and global_filters["company"] != "All":
    base = base[base["company_id"] == global_filters["company"]]

if base.empty:
    st.info("No rows match current global filters. Reset filters to view the market.")
    st.stop()

base["market_cap_crore"] = pd.to_numeric(base.get("market_cap_crore"), errors="coerce")
base["return_pct"] = pd.to_numeric(base.get("return_pct"), errors="coerce")
base["return_on_equity_pct"] = pd.to_numeric(base.get("return_on_equity_pct"), errors="coerce")

render_section_header("Executive KPI Board")
st.caption("Portfolio-level KPIs summarize size, return characteristics, and breadth of the current filtered universe.")

total_companies = int(base["company_id"].nunique())
total_market_cap = base["market_cap_crore"].sum(min_count=1)
avg_market_cap = base["market_cap_crore"].mean()
avg_return = base["return_pct"].mean()
avg_roe = base["return_on_equity_pct"].mean()
sector_count = int(base["broad_sector"].dropna().nunique())

top_row = base.dropna(subset=["return_pct"]).sort_values("return_pct", ascending=False).head(1)
bottom_row = base.dropna(subset=["return_pct"]).sort_values("return_pct", ascending=True).head(1)
top_name = top_row.iloc[0]["company_name"] if not top_row.empty else "N/A"
top_ret = top_row.iloc[0]["return_pct"] if not top_row.empty else None
bottom_name = bottom_row.iloc[0]["company_name"] if not bottom_row.empty else "N/A"
bottom_ret = bottom_row.iloc[0]["return_pct"] if not bottom_row.empty else None

kpi_a = st.columns(4)
with kpi_a[0]:
    render_metric_card("Total Companies", total_companies, "Active in current filter")
with kpi_a[1]:
    render_metric_card("Total Market Cap", format_currency(total_market_cap), "Aggregate valuation")
with kpi_a[2]:
    render_metric_card("Average Market Cap", format_currency(avg_market_cap), "Per company")
with kpi_a[3]:
    render_metric_card("Average Return", format_percentage(avg_return), "Price performance")

kpi_b = st.columns(4)
with kpi_b[0]:
    render_metric_card("Top Performing Company", top_name, format_percentage(top_ret))
with kpi_b[1]:
    render_metric_card("Worst Performing Company", bottom_name, format_percentage(bottom_ret))
with kpi_b[2]:
    render_metric_card("Number of Sectors", sector_count, "Diversification breadth")
with kpi_b[3]:
    render_metric_card("Average ROE", format_percentage(avg_roe), "Profitability quality")

render_section_header("Market Overview")

sort_order = st.selectbox(
    "Market-cap ranking order",
    ["Highest to Lowest", "Lowest to Highest"],
    help="Controls market-cap bar chart ranking direction.",
)

ranked = base.dropna(subset=["market_cap_crore", "company_name"]).copy()
ranked = ranked.sort_values("market_cap_crore", ascending=(sort_order == "Lowest to Highest")).head(15)

bar = px.bar(
    ranked,
    x="market_cap_crore",
    y="company_name",
    orientation="h",
    color="market_cap_crore",
    color_continuous_scale="Blues",
    title="Top Companies by Market Capitalization",
    labels={"market_cap_crore": "Market Cap (Rs Cr)", "company_name": "Company"},
)
apply_chart_theme(bar, x_title="Market Cap (Rs Cr)", y_title="Company")
bar.update_layout(coloraxis_showscale=False)
bar.update_traces(hovertemplate="%{y}<br>Market Cap: Rs %{x:,.0f} Cr<extra></extra>")
st.plotly_chart(bar, width="stretch")

sector_frame = (
    base.dropna(subset=["broad_sector"])
    .groupby("broad_sector", as_index=False)
    .agg(
        company_count=("company_id", "nunique"),
        market_cap_crore=("market_cap_crore", "sum"),
        avg_return_pct=("return_pct", "mean"),
    )
)

if not sector_frame.empty:
    donut = px.pie(
        sector_frame,
        names="broad_sector",
        values="market_cap_crore" if sector_frame["market_cap_crore"].notna().any() else "company_count",
        hole=0.58,
        title="Sector Distribution",
    )
    apply_chart_theme(donut, show_legend=True)
    st.plotly_chart(donut, width="stretch")

    sector_perf = sector_frame.dropna(subset=["avg_return_pct"]).sort_values("avg_return_pct", ascending=True)
    if not sector_perf.empty:
        perf = px.bar(
            sector_perf,
            x="avg_return_pct",
            y="broad_sector",
            orientation="h",
            color="avg_return_pct",
            color_continuous_scale=[[0, "#ef4444"], [0.5, "#9ca3af"], [1, "#22c55e"]],
            title="Sector Performance Ranking (Average Return)",
            labels={"avg_return_pct": "Average Return (%)", "broad_sector": "Sector"},
        )
        apply_chart_theme(perf, x_title="Average Return (%)", y_title="Sector")
        perf.update_layout(coloraxis_showscale=False)
        st.plotly_chart(perf, width="stretch")

distribution = base.dropna(subset=["return_pct"])
if not distribution.empty:
    hist = px.histogram(
        distribution,
        x="return_pct",
        nbins=24,
        title="Return Distribution",
        labels={"return_pct": "Return (%)"},
    )
    avg_line = distribution["return_pct"].mean()
    hist.add_vline(x=avg_line, line_dash="dash", line_color="#22c55e", annotation_text="Average Return")
    apply_chart_theme(hist, x_title="Return (%)", y_title="Company Count", show_legend=False)
    st.plotly_chart(hist, width="stretch")

render_section_header("Company Performance")
st.caption("Company ranking and risk-return view based on available price history and market-cap records.")

perf = base.dropna(subset=["return_pct", "company_name"]).copy()
if perf.empty:
    st.info("No performance data available in stock_prices for the current filter.")
else:
    top10 = perf.sort_values("return_pct", ascending=False).head(10)
    bottom10 = perf.sort_values("return_pct", ascending=True).head(10)

    col_l, col_r = st.columns(2)
    with col_l:
        top_bar = px.bar(
            top10.sort_values("return_pct", ascending=True),
            x="return_pct",
            y="company_name",
            orientation="h",
            title="Top 10 Performers",
            color_discrete_sequence=["#22c55e"],
        )
        apply_chart_theme(top_bar, x_title="Return (%)", y_title="Company", show_legend=False)
        st.plotly_chart(top_bar, width="stretch")
    with col_r:
        bottom_bar = px.bar(
            bottom10,
            x="return_pct",
            y="company_name",
            orientation="h",
            title="Bottom 10 Performers",
            color_discrete_sequence=["#ef4444"],
        )
        apply_chart_theme(bottom_bar, x_title="Return (%)", y_title="Company", show_legend=False)
        st.plotly_chart(bottom_bar, width="stretch")

    scatter = perf.dropna(subset=["market_cap_crore"]).copy()
    if not scatter.empty:
        scatter_plot = px.scatter(
            scatter,
            x="market_cap_crore",
            y="return_pct",
            color="broad_sector" if "broad_sector" in scatter.columns else None,
            hover_name="company_name",
            hover_data={"company_id": True, "market_cap_crore": ":,.0f", "return_pct": ":.2f", "volatility_pct": ":.2f"},
            title="Market Cap vs Return",
            labels={"market_cap_crore": "Market Cap (Rs Cr)", "return_pct": "Return (%)"},
        )
        apply_chart_theme(scatter_plot, x_title="Market Cap (Rs Cr)", y_title="Return (%)")
        st.plotly_chart(scatter_plot, width="stretch")

    query = st.text_input("Search Company in Ranking", placeholder="Type company name or ticker", help="Use search with sorting and pagination controls below.")
    ranking = perf[["company_id", "company_name", "broad_sector", "market_cap_crore", "return_pct", "volatility_pct"]].copy()
    if query:
        ranking = ranking[
            ranking["company_name"].astype(str).str.contains(query, case=False, na=False)
            | ranking["company_id"].astype(str).str.contains(query, case=False, na=False)
        ]

    ranking = ranking.sort_values("return_pct", ascending=False).reset_index(drop=True)
    ranking.index = ranking.index + 1
    page_size = st.selectbox("Rows per page", [10, 20, 30], index=0)
    page_num = st.number_input("Page", min_value=1, max_value=max(1, (len(ranking) - 1) // page_size + 1), value=1)
    start = (page_num - 1) * page_size
    end = start + page_size
    page_df = ranking.iloc[start:end].copy()
    page_df["market_cap_crore"] = pd.to_numeric(page_df["market_cap_crore"], errors="coerce").round(2)
    page_df["return_pct"] = pd.to_numeric(page_df["return_pct"], errors="coerce").round(2)
    page_df["volatility_pct"] = pd.to_numeric(page_df["volatility_pct"], errors="coerce").round(2)
    st.dataframe(page_df, width="stretch")

render_section_header("Sector Analysis")
sector_options = sorted(base["broad_sector"].dropna().astype(str).unique().tolist())
if not sector_options:
    st.info("Sector data not available for this filter.")
else:
    default_sector = global_filters.get("sector") if global_filters.get("sector") in sector_options else sector_options[0]
    selected_sector = st.selectbox("Select Sector", sector_options, index=sector_options.index(default_sector), help="Updates sector-specific charts and rankings below.")
    sector_view = base[base["broad_sector"] == selected_sector].copy()

    s_cols = st.columns(4)
    with s_cols[0]:
        render_metric_card("Company Count", int(sector_view["company_id"].nunique()), "Sector breadth")
    with s_cols[1]:
        render_metric_card("Sector Market Cap", format_currency(sector_view["market_cap_crore"].sum(min_count=1)), "Aggregate")
    with s_cols[2]:
        render_metric_card("Sector Avg Return", format_percentage(sector_view["return_pct"].mean()), "Price performance")
    with s_cols[3]:
        render_metric_card("Sector Avg ROE", format_percentage(sector_view["return_on_equity_pct"].mean()), "Profitability")

    sector_rank = sector_view[["company_name", "return_pct", "market_cap_crore", "return_on_equity_pct"]].copy()
    sector_rank = sector_rank.sort_values("return_pct", ascending=False).head(15)
    sector_rank["return_pct"] = pd.to_numeric(sector_rank["return_pct"], errors="coerce").round(2)
    sector_rank["market_cap_crore"] = pd.to_numeric(sector_rank["market_cap_crore"], errors="coerce").round(2)
    sector_rank["return_on_equity_pct"] = pd.to_numeric(sector_rank["return_on_equity_pct"], errors="coerce").round(2)

    sector_chart = px.bar(
        sector_rank.sort_values("return_pct", ascending=True),
        x="return_pct",
        y="company_name",
        orientation="h",
        color="return_pct",
        color_continuous_scale=[[0, "#ef4444"], [0.5, "#9ca3af"], [1, "#22c55e"]],
        title=f"{selected_sector} Return Ranking",
    )
    apply_chart_theme(sector_chart, x_title="Return (%)", y_title="Company")
    sector_chart.update_layout(coloraxis_showscale=False)
    st.plotly_chart(sector_chart, width="stretch")
    st.dataframe(sector_rank, width="stretch")

render_section_header("Company Detail Visualization")
company_options = sorted(base["company_id"].dropna().astype(str).unique().tolist())
selected_company = st.selectbox("Select Company for Detail View", company_options, help="Shows company-level price, return, valuation, and peer context.")
company_row = base[base["company_id"] == selected_company].head(1)

if company_row.empty:
    st.info("Company details are unavailable for current filters.")
else:
    row = company_row.iloc[0]
    detail_cols = st.columns(2)
    with detail_cols[0]:
        render_metric_card("Company", row.get("company_name", selected_company), row.get("broad_sector", "N/A"))
        render_metric_card("Market Cap", format_currency(row.get("market_cap_crore")), "Current record")
        render_metric_card("Return", format_percentage(row.get("return_pct")), "From available history")
    with detail_cols[1]:
        render_metric_card("ROE", format_percentage(row.get("return_on_equity_pct")), "Latest financial ratio")
        render_metric_card("Volatility", format_percentage(row.get("volatility_pct")), "Std. dev. of daily returns")
        render_metric_card("Market-Cap Category", row.get("market_cap_category", "N/A"), "Sector metadata")

    company_prices = get_stock_prices(selected_company)
    if not company_prices.empty and "date" in company_prices.columns and "close_price" in company_prices.columns:
        company_prices = company_prices.copy()
        company_prices["date"] = pd.to_datetime(company_prices["date"], errors="coerce")
        company_prices["close_price"] = pd.to_numeric(company_prices["close_price"], errors="coerce")
        company_prices = company_prices.dropna(subset=["date", "close_price"]).sort_values("date")

        period = st.selectbox(
            "Price History Range",
            ["All", "5Y", "3Y", "1Y", "6M"],
            help="Filters historical price chart range.",
        )
        if period != "All" and not company_prices.empty:
            max_date = company_prices["date"].max()
            if period == "5Y":
                cutoff = max_date - pd.DateOffset(years=5)
            elif period == "3Y":
                cutoff = max_date - pd.DateOffset(years=3)
            elif period == "1Y":
                cutoff = max_date - pd.DateOffset(years=1)
            else:
                cutoff = max_date - pd.DateOffset(months=6)
            company_prices = company_prices[company_prices["date"] >= cutoff]

        line = px.line(
            company_prices,
            x="date",
            y="close_price",
            title="Historical Price",
            labels={"date": "Date", "close_price": "Close Price"},
        )
        apply_chart_theme(line, x_title="Date", y_title="Close Price", show_legend=False)
        st.plotly_chart(line, width="stretch")

    peer_context = base[base["broad_sector"] == row.get("broad_sector")].copy()
    peer_context = peer_context[["company_id", "company_name", "return_pct", "market_cap_crore", "return_on_equity_pct"]]
    if not peer_context.empty:
        peer_context = peer_context.sort_values("return_pct", ascending=False)
        st.caption("Peer comparison in selected sector")
        st.dataframe(peer_context.head(10), width="stretch")
