import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from utils.db import get_companies, get_peers, get_pl, get_ratios
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
    "Peer Comparison",
    "Benchmark a company against its peer group on quality, profitability, leverage, and cash flow.",
    status="Relative analysis",
)

peer = get_peers()
ratios = get_ratios()
companies = get_companies()
profit_loss = get_pl()

if peer.empty:
    st.warning("Peer groups not available.")
    st.stop()

peer_groups = sorted(peer["peer_group_name"].dropna().unique())
selected_group = st.selectbox("Select Peer Group", peer_groups)

group_df = peer[peer["peer_group_name"] == selected_group].copy()
if group_df.empty:
    st.warning("No companies found for this peer group.")
    st.stop()

company_ids = [str(company_id) for company_id in group_df["company_id"].dropna().astype(str).tolist()]
selected_company = st.selectbox("Select Company", company_ids)

company_lookup = companies.set_index("id") if not companies.empty and "id" in companies.columns else pd.DataFrame(index=[])


def _latest_row(df, company_id):
    if df.empty or "company_id" not in df.columns:
        return None

    company_rows = df[df["company_id"] == company_id]
    if company_rows.empty:
        return None

    if "year" in company_rows.columns:
        company_rows = company_rows.sort_values("year", ascending=False)

    return company_rows.iloc[0]


def _safe_float(value):
    if value is None or pd.isna(value):
        return 0.0
    return float(value)


def _build_metric_values(company_id):
    ratio_row = _latest_row(ratios, company_id)
    pl_row = _latest_row(profit_loss, company_id)
    profile_row = company_lookup.loc[company_id] if company_id in company_lookup.index else None

    roe = _safe_float(ratio_row.get("return_on_equity_pct")) if ratio_row is not None else 0.0
    roce = _safe_float(profile_row.get("roce_percentage")) if profile_row is not None and hasattr(profile_row, "get") else 0.0
    npm = _safe_float(ratio_row.get("net_profit_margin_pct")) if ratio_row is not None else 0.0
    debt_to_equity = _safe_float(ratio_row.get("debt_to_equity")) if ratio_row is not None else 0.0
    fcf = _safe_float(ratio_row.get("free_cash_flow_cr")) if ratio_row is not None else 0.0
    pat = _safe_float(pl_row.get("net_profit")) if pl_row is not None else 0.0
    revenue = _safe_float(pl_row.get("sales")) if pl_row is not None else 0.0

    return [roe, roce, npm, debt_to_equity, fcf, pat, revenue]


metrics = ["ROE", "ROCE", "NPM", "D/E", "FCF", "PAT", "Revenue"]
selected_values = _build_metric_values(selected_company)
peer_values = [_build_metric_values(company_id) for company_id in company_ids]

peer_averages = []
for index in range(len(metrics)):
    values = [row[index] for row in peer_values]
    peer_averages.append(sum(values) / len(values) if values else 0.0)

fig = go.Figure()
fig.add_trace(go.Scatterpolar(r=selected_values, theta=metrics, fill="toself", name=selected_company))
fig.add_trace(go.Scatterpolar(r=peer_averages, theta=metrics, name="Peer Average"))
fig.update_layout(
    title="Company vs Peer Radar",
    polar={"radialaxis": {"visible": True, "range": [0, max(100, max(selected_values + peer_averages) * 1.2)]}},
    paper_bgcolor="#111827",
    plot_bgcolor="#111827",
    font={"color": "#F8FAFC"},
    showlegend=True,
)

render_section_header("Peer Snapshot")
summary = st.columns(3)
with summary[0]:
    render_metric_card("ROE vs Peers", f"{format_percentage(selected_values[0])} / {format_percentage(peer_averages[0])}", "Selected / average")
with summary[1]:
    render_metric_card("Debt/Equity vs Peers", f"{format_ratio(selected_values[3])} / {format_ratio(peer_averages[3])}", "Selected / average")
with summary[2]:
    render_metric_card("NPM vs Peers", f"{format_percentage(selected_values[2])} / {format_percentage(peer_averages[2])}", "Selected / average")

st.plotly_chart(fig, use_container_width=True)

table = group_df.merge(
    companies,
    left_on="company_id",
    right_on="id",
    how="left",
)

render_section_header("Peer Companies")

display_cols = [
    col
    for col in ["company_id", "company_name", "peer_group_name", "is_benchmark", "roce_percentage", "roe_percentage"]
    if col in table.columns
]
peer_display = table[display_cols].copy()
if "is_benchmark" in peer_display.columns:
    peer_display["is_benchmark"] = peer_display["is_benchmark"].map({1: "Yes", 0: "No"}).fillna("No")

st.dataframe(peer_display, use_container_width=True)

benchmark = table[table["is_benchmark"] == 1]
render_section_header("Benchmark Company")
if benchmark.empty:
    st.info("No benchmark company is tagged for this peer group.")
else:
    benchmark_cols = [col for col in ["company_id", "company_name", "peer_group_name"] if col in benchmark.columns]
    st.dataframe(benchmark[benchmark_cols], use_container_width=True)