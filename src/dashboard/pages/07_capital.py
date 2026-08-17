import pandas as pd
import plotly.express as px
import streamlit as st
from utils.db import get_ratios
from utils.theme import (
    apply_theme,
    format_currency,
    format_percentage,
    render_metric_card,
    render_page_header,
    render_section_header,
)

apply_theme()

render_page_header(
    "Capital Allocation",
    "Map free cash flow and return on equity across the portfolio to understand capital efficiency.",
    status="Capital view",
)

df = get_ratios()

if df.empty:
    st.warning("No financial-ratio data is available.")
    st.stop()

df = df.copy()

df["free_cash_flow_cr"] = pd.to_numeric(df.get("free_cash_flow_cr"), errors="coerce")
df["debt_to_equity"] = pd.to_numeric(df.get("debt_to_equity"), errors="coerce")
df["return_on_equity_pct"] = pd.to_numeric(df.get("return_on_equity_pct"), errors="coerce")

def _allocation_pattern(row):
    if pd.isna(row["free_cash_flow_cr"]) or pd.isna(row["debt_to_equity"]):
        return "Unclassified"
    if row["free_cash_flow_cr"] < 0:
        return "Cash Burn"
    if row["debt_to_equity"] > 1.5:
        return "Leveraged Expansion"
    if row["free_cash_flow_cr"] > 0 and row["debt_to_equity"] <= 1.5:
        return "Balanced"
    return "Transitional"

df["Pattern"] = df.apply(_allocation_pattern, axis=1)

df["treemap_value"] = (
    pd.to_numeric(
        df["free_cash_flow_cr"],
        errors="coerce",
    )
    .abs()
    .fillna(0)
)

df = df[df["treemap_value"] > 0]

if df.empty:
    st.info("No valid capital-allocation values are available.")
else:
    render_section_header("Capital Allocation Snapshot")
    summary_cols = st.columns(4)
    with summary_cols[0]:
        render_metric_card("Companies", int(df["company_id"].nunique()), "With non-zero FCF values")
    with summary_cols[1]:
        render_metric_card("Median FCF", format_currency(df["free_cash_flow_cr"].median()), "Cash generation")
    with summary_cols[2]:
        render_metric_card("Median ROE", format_percentage(df["return_on_equity_pct"].median()), "Capital productivity")
    with summary_cols[3]:
        render_metric_card("High Leverage", int((df["debt_to_equity"] > 1.5).sum()), "Debt/Equity > 1.5")

    fig = px.treemap(
        df,
        path=["Pattern", "company_id"],
        values="treemap_value",
        color="return_on_equity_pct",
        hover_data=[
            "year",
            "free_cash_flow_cr",
            "debt_to_equity",
        ],
        title="Capital Allocation by Company",
        color_continuous_scale="RdYlGn",
    )

    fig.update_layout(
        paper_bgcolor="#111827",
        plot_bgcolor="#111827",
        font={"color": "#F8FAFC"},
        margin={"l": 10, "r": 10, "t": 60, "b": 10},
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

    render_section_header("Allocation Patterns")
    pattern_summary = (
        df.groupby("Pattern", dropna=False)["company_id"]
        .nunique()
        .reset_index(name="company_count")
        .sort_values("company_count", ascending=False)
    )
    st.dataframe(pattern_summary, use_container_width=True)