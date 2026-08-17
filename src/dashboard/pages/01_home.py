import pandas as pd
import plotly.express as px
import streamlit as st
from utils.db import (
    get_companies,
    get_market_cap,
    get_pl,
    get_ratios,
    get_sectors,
    get_years,
)
from utils.theme import (
    apply_theme,
    format_percentage,
    format_ratio,
    render_metric_card,
    render_page_header,
    render_section_header,
)

apply_theme()

render_page_header(
    "Nifty 100 Analytics",
    "Market snapshot, performance quality, and sector distribution for the active year.",
    status="Live fundamentals",
)
def _extract_year(value):
    if pd.isna(value):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        digits = [part for part in value.split() if part.isdigit()]
        if digits:
            return int(digits[-1])
        import re

        match = re.search(r"(\d{4})", value)
        if match:
            return int(match.group(1))
    return None


def _safe_numeric(series):
    return pd.to_numeric(series, errors="coerce")


def _safe_median(series):
    numeric = _safe_numeric(series).dropna()
    return round(float(numeric.median()), 2) if not numeric.empty else None


def _calculate_revenue_cagr(pl_df):
    if pl_df.empty or "sales" not in pl_df.columns:
        return None

    working = pl_df.copy()
    working["year_num"] = working["year"].apply(_extract_year)
    working = working.dropna(subset=["year_num", "sales"])
    working = working.sort_values("year_num")

    if working.shape[0] < 2:
        return None

    start_value = float(working.iloc[0]["sales"])
    end_value = float(working.iloc[-1]["sales"])

    if start_value <= 0 or end_value <= 0:
        return None

    periods = max(1, working.shape[0] - 1)
    return round(((end_value / start_value) ** (1 / periods) - 1) * 100, 2)


def _build_composite_quality_score(ratios_df):
    if ratios_df.empty:
        return ratios_df

    score_df = ratios_df.copy()
    score_values = pd.Series(0.0, index=score_df.index)

    if "return_on_equity_pct" in score_df.columns:
        score_values += _safe_numeric(score_df["return_on_equity_pct"]) * 0.4
    if "net_profit_margin_pct" in score_df.columns:
        score_values += _safe_numeric(score_df["net_profit_margin_pct"]) * 0.3
    if "interest_coverage" in score_df.columns:
        score_values += _safe_numeric(score_df["interest_coverage"]) * 0.1
    if "debt_to_equity" in score_df.columns:
        score_values -= _safe_numeric(score_df["debt_to_equity"]) * 5

    score_df["composite_quality_score"] = score_values
    return score_df


years = get_years()
if not years:
    st.warning("No year data is available in the financial ratios table.")
    st.stop()

selected_year = st.sidebar.selectbox("Year selector", years, index=len(years) - 1)

ratios = get_ratios(year=selected_year)
companies = get_companies()
sectors = get_sectors()
market_cap = get_market_cap(year=_extract_year(selected_year))

if ratios.empty:
    st.warning(f"No financial ratios are available for {selected_year}.")
    st.stop()

active_company_ids = [company_id for company_id in ratios["company_id"].dropna().astype(str).tolist() if company_id]

render_section_header(f"Market Snapshot | {selected_year}")
st.caption("Use this view to monitor market quality, leverage profile, and sector concentration for the selected year.")

cagr_values = []
for company_id in active_company_ids:
    cagr_value = _calculate_revenue_cagr(get_pl(company_id))
    if cagr_value is not None:
        cagr_values.append(cagr_value)

median_revenue_cagr = _safe_median(pd.Series(cagr_values))
median_roe = _safe_median(ratios["return_on_equity_pct"]) if "return_on_equity_pct" in ratios.columns else None
median_pe = _safe_median(market_cap["pe_ratio"]) if not market_cap.empty and "pe_ratio" in market_cap.columns else None
median_de = _safe_median(ratios["debt_to_equity"]) if "debt_to_equity" in ratios.columns else None
debt_free_companies = int((pd.to_numeric(ratios["debt_to_equity"], errors="coerce") <= 0.01).sum()) if "debt_to_equity" in ratios.columns else 0

kpi_columns = st.columns(3)
with kpi_columns[0]:
    render_metric_card("Median ROE", format_percentage(median_roe), "Across active universe")
with kpi_columns[1]:
    render_metric_card("Median PE", format_ratio(median_pe), "Valuation center")
with kpi_columns[2]:
    render_metric_card("Median Debt/Equity", format_ratio(median_de), "Balance-sheet leverage")

kpi_columns_2 = st.columns(3)
with kpi_columns_2[0]:
    render_metric_card("Total Companies", len(active_company_ids), "Coverage in selected year")
with kpi_columns_2[1]:
    render_metric_card("Median Revenue CAGR", format_percentage(median_revenue_cagr), "Multi-year growth")
with kpi_columns_2[2]:
    render_metric_card("Debt Free Companies", debt_free_companies, "Debt/Equity <= 0.01")

st.markdown("---")

if not sectors.empty and "company_id" in sectors.columns and "broad_sector" in sectors.columns:
    active_sector_rows = sectors[sectors["company_id"].isin(active_company_ids)]
    if not active_sector_rows.empty:
        sector_counts = (
            active_sector_rows.groupby("broad_sector", dropna=False)["company_id"]
            .nunique()
            .reset_index(name="company_count")
            .sort_values("company_count", ascending=False)
        )
        fig = px.pie(
            sector_counts,
            names="broad_sector",
            values="company_count",
            hole=0.45,
            title="Company count by sector",
            color_discrete_sequence=["#3B82F6", "#22C55E", "#F59E0B", "#EF4444", "#06B6D4", "#8B5CF6", "#F97316"],
        )
        fig.update_layout(
            paper_bgcolor="#111827",
            plot_bgcolor="#111827",
            font={"color": "#F8FAFC"},
            legend_title_text="Sector",
            margin={"l": 10, "r": 10, "t": 60, "b": 10},
        )
        st.plotly_chart(fig, use_container_width=True)

        sector_quality = ratios.merge(sectors[["company_id", "broad_sector"]], on="company_id", how="left")
        if "return_on_equity_pct" in sector_quality.columns:
            sector_roe = (
                sector_quality.groupby("broad_sector", dropna=False)["return_on_equity_pct"]
                .median()
                .reset_index(name="median_roe")
                .dropna()
                .sort_values("median_roe", ascending=False)
                .head(8)
            )
            if not sector_roe.empty:
                bar_fig = px.bar(
                    sector_roe,
                    x="median_roe",
                    y="broad_sector",
                    orientation="h",
                    title="Top Sectors by Median ROE",
                    color="median_roe",
                    color_continuous_scale="Blues",
                )
                bar_fig.update_layout(
                    paper_bgcolor="#111827",
                    plot_bgcolor="#111827",
                    font={"color": "#F8FAFC"},
                    coloraxis_showscale=False,
                    margin={"l": 10, "r": 10, "t": 60, "b": 10},
                )
                st.plotly_chart(bar_fig, use_container_width=True)
    else:
        st.info("Sector information is not available for the selected year.")
else:
    st.info("Sector data is missing or incomplete.")

st.markdown("---")

ranked_ratios = _build_composite_quality_score(ratios.copy())
if not ranked_ratios.empty and "composite_quality_score" in ranked_ratios.columns:
    ranked_ratios = ranked_ratios.sort_values("composite_quality_score", ascending=False).head(5)
    if not companies.empty and "company_name" in companies.columns:
        ranked_ratios = ranked_ratios.merge(
            companies[["id", "company_name"]],
            left_on="company_id",
            right_on="id",
            how="left",
        )

    display_columns = [
        column
        for column in ["company_id", "company_name", "composite_quality_score", "return_on_equity_pct", "net_profit_margin_pct"]
        if column in ranked_ratios.columns
    ]
    render_section_header("Top 5 by Composite Quality")
    present = ranked_ratios[display_columns].reset_index(drop=True).copy()
    if "composite_quality_score" in present.columns:
        present["composite_quality_score"] = pd.to_numeric(present["composite_quality_score"], errors="coerce").round(2)
    if "return_on_equity_pct" in present.columns:
        present["return_on_equity_pct"] = pd.to_numeric(present["return_on_equity_pct"], errors="coerce").round(2)
    if "net_profit_margin_pct" in present.columns:
        present["net_profit_margin_pct"] = pd.to_numeric(present["net_profit_margin_pct"], errors="coerce").round(2)

    st.dataframe(present, use_container_width=True)
else:
    st.info("No ranked company data is available for this year.")
