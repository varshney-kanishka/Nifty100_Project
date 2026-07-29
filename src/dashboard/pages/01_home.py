import pandas as pd
import plotly.express as px
import streamlit as st

from utils.db import get_companies, get_market_cap, get_pl, get_ratios, get_sectors, get_years


st.title("Nifty 100 Analytics Dashboard")


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

st.markdown(f"## Market snapshot for {selected_year}")

if ratios.empty:
    st.warning(f"No financial ratios are available for {selected_year}.")
    st.stop()

active_company_ids = [company_id for company_id in ratios["company_id"].dropna().astype(str).tolist() if company_id]

kpi_columns = st.columns(3)
metric_specs = [
    ("Average ROE", _safe_median(ratios["return_on_equity_pct"]) if "return_on_equity_pct" in ratios.columns else None, "%"),
    ("Median PE", _safe_median(market_cap["pe_ratio"]) if not market_cap.empty and "pe_ratio" in market_cap.columns else None, "x"),
    ("Median Debt to Equity", _safe_median(ratios["debt_to_equity"]) if "debt_to_equity" in ratios.columns else None, "x"),
    ("Total Companies", len(active_company_ids), ""),
    ("Median Revenue CAGR", None, "%"),
    ("Debt Free Companies", int((pd.to_numeric(ratios["debt_to_equity"], errors="coerce") <= 0.01).sum()) if "debt_to_equity" in ratios.columns else 0, ""),
]

for index, (label, value, suffix) in enumerate(metric_specs):
    if label == "Median Revenue CAGR":
        cagr_values = []
        for company_id in active_company_ids:
            cagr_value = _calculate_revenue_cagr(get_pl(company_id))
            if cagr_value is not None:
                cagr_values.append(cagr_value)
        value = _safe_median(pd.Series(cagr_values))

    display_value = "N/A"
    if value is not None:
        display_value = f"{value:.2f}{suffix}" if isinstance(value, (int, float)) else str(value)

    kpi_columns[index % 3].metric(label, display_value)

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
        )
        st.plotly_chart(fig, use_container_width=True)
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
    st.subheader("Top 5 companies by composite quality score")
    st.dataframe(ranked_ratios[display_columns].reset_index(drop=True), use_container_width=True)
else:
    st.info("No ranked company data is available for this year.")
