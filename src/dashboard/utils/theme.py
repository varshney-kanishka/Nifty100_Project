from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

COLORS = {
    "bg": "#0F172A",
    "surface": "#111827",
    "panel": "#1A2438",
    "primary": "#2563EB",
    "positive": "#16A34A",
    "negative": "#DC2626",
    "warning": "#D97706",
    "text": "#E5E7EB",
    "muted": "#9CA3AF",
    "border": "#2B3851",
}


def apply_theme() -> None:
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap');

        :root {{
            --bg: {COLORS['bg']};
            --surface: {COLORS['surface']};
            --panel: {COLORS['panel']};
            --primary: {COLORS['primary']};
            --positive: {COLORS['positive']};
            --negative: {COLORS['negative']};
            --warning: {COLORS['warning']};
            --text: {COLORS['text']};
            --muted: {COLORS['muted']};
            --border: {COLORS['border']};
            --font-ui: 'IBM Plex Sans', 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
            --font-mono: 'IBM Plex Mono', 'Consolas', 'Monaco', monospace;
        }}

        .stApp {{
            background: var(--bg);
            color: var(--text);
            font-family: var(--font-ui);
            font-feature-settings: 'tnum' 1, 'lnum' 1;
            letter-spacing: 0.005em;
        }}

        .stApp .main .block-container {{
            padding-top: 1rem;
            padding-bottom: 2.5rem;
            max-width: 1540px;
        }}

        div[data-testid="stSidebar"] {{
            background: #0f172a;
            border-right: 1px solid var(--border);
        }}

        .theme-brand {{
            background: rgba(37, 99, 235, 0.08);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 0.9rem 0.9rem 0.75rem 0.9rem;
            margin-bottom: 1rem;
        }}

        .brand-title {{
            font-size: 1.05rem;
            font-weight: 700;
            letter-spacing: 0.14em;
            text-transform: uppercase;
            color: var(--text);
            margin: 0;
            font-family: var(--font-ui);
        }}

        .brand-subtitle {{
            font-size: 0.72rem;
            color: var(--muted);
            margin-top: 0.2rem;
            letter-spacing: 0.06em;
            text-transform: uppercase;
        }}

        .nav-section {{
            color: var(--muted);
            font-size: 0.68rem;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            margin: 1.1rem 0 0.5rem 0;
            padding-left: 0.4rem;
        }}

        .theme-header {{
            border: 1px solid var(--border);
            background: rgba(17, 24, 39, 0.92);
            border-radius: 16px;
            padding: 1rem 1.25rem;
            margin-bottom: 1.25rem;
        }}

        .theme-page-title {{
            margin: 0;
            font-size: clamp(1.8rem, 2vw, 2.5rem);
            font-weight: 700;
            letter-spacing: 0.02em;
            color: var(--text);
            font-family: var(--font-ui);
        }}

        .theme-page-subtitle {{
            margin: 0.15rem 0 0 0;
            color: var(--muted);
            font-size: 0.96rem;
        }}

        .status-row {{
            display: flex;
            align-items: center;
            gap: 0.45rem;
            color: var(--muted);
            font-size: 0.76rem;
            margin-top: 0.5rem;
        }}

        .status-dot {{
            width: 0.55rem;
            height: 0.55rem;
            border-radius: 50%;
            background: var(--positive);
            box-shadow: 0 0 12px rgba(34,197,94,0.8);
        }}

        .metric-card {{
            background: rgba(17, 24, 39, 0.96);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 0.9rem 1rem;
            min-height: 110px;
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.03);
        }}

        .metric-card .label {{
            color: var(--muted);
            font-size: 0.72rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 0.35rem;
        }}

        .metric-card .value {{
            color: var(--text);
            font-size: 1.55rem;
            font-weight: 700;
            line-height: 1.2;
            font-family: var(--font-ui);
        }}

        .metric-card .delta {{
            color: var(--muted);
            font-size: 0.72rem;
            margin-top: 0.3rem;
        }}

        .section-header {{
            color: var(--text);
            font-size: 1.1rem;
            font-weight: 700;
            margin-top: 1.4rem;
            margin-bottom: 0.6rem;
            padding-bottom: 0.25rem;
            border-bottom: 1px solid var(--border);
        }}

        .panel {{
            background: var(--panel);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 0.9rem 1rem;
        }}

        .status-badge {{
            display: inline-block;
            font-size: 0.72rem;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            padding: 0.32rem 0.6rem;
            border-radius: 999px;
            border: 1px solid var(--border);
            background: rgba(59,130,246,0.08);
            color: var(--text);
        }}

        .positive-badge {{
            background: rgba(34,197,94,0.1);
            border-color: rgba(34,197,94,0.4);
            color: #A7F3D0;
        }}

        .negative-badge {{
            background: rgba(239,68,68,0.08);
            border-color: rgba(239,68,68,0.4);
            color: #FCA5A5;
        }}

        .warning-badge {{
            background: rgba(245,158,11,0.08);
            border-color: rgba(245,158,11,0.4);
            color: #FCD34D;
        }}

        .stMetric {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 0.7rem 0.8rem;
        }}

        [data-testid="stMetricValue"],
        [data-testid="stMetricDelta"] {{
            font-family: var(--font-ui);
        }}

        [data-testid="stMetricValue"] {{
            font-weight: 700;
            color: var(--text);
        }}

        .stDataFrame {{
            border: 1px solid var(--border);
            border-radius: 12px;
            overflow: hidden;
        }}

        div[data-testid="stDataFrame"] > div > div > table {{
            background: #0f172a;
        }}

        .stTable th {{
            background: rgba(17,24,39,1);
            color: var(--text);
        }}

        .stTable td {{
            color: var(--text);
            border-bottom: 1px solid var(--border);
        }}

        .stDownloadButton > button {{
            background: rgba(59,130,246,0.12);
            color: var(--text);
            border: 1px solid var(--border);
            border-radius: 10px;
            font-weight: 600;
        }}

        .stButton > button {{
            background: rgba(37, 99, 235, 0.12);
            color: var(--text);
            border: 1px solid var(--border);
            border-radius: 10px;
            font-weight: 600;
        }}

        .stButton > button:hover,
        .stDownloadButton > button:hover {{
            border-color: rgba(37, 99, 235, 0.7);
            background: rgba(37, 99, 235, 0.2);
        }}

        .stSelectbox [data-baseweb="select"] > div,
        .stTextInput input,
        .stNumberInput input {{
            background: rgba(15, 23, 42, 0.9);
            border: 1px solid var(--border);
            border-radius: 10px;
            color: var(--text);
        }}

        [data-baseweb="tooltip"] {{
            font-family: var(--font-ui);
            font-size: 0.78rem;
            border: 1px solid var(--border);
            background: #111827;
            color: var(--text);
        }}

        .stSelectbox label, .stSlider label, .stNumberInput label, .stTextInput label {{
            color: var(--muted);
            font-weight: 600;
        }}

        .stTabs [role="tablist"] {{
            background: rgba(17,24,39,0.8);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 0.25rem;
        }}

        .stTabs [role="tab"] {{
            color: var(--muted);
        }}

        .stTabs [role="tab"][aria-selected="true"] {{
            background: rgba(59,130,246,0.12);
            border: 1px solid var(--border);
            color: var(--text);
            border-radius: 10px;
        }}

        .small-caption {{
            color: var(--muted);
            font-size: 0.75rem;
            letter-spacing: 0.04em;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_page_header(title: str, subtitle: str, status: str = "Data Connected") -> None:
    st.markdown(
        f"""
        <div class="theme-header">
            <div class="theme-page-title">{title}</div>
            <div class="theme-page-subtitle">{subtitle}</div>
            <div class="status-row">
                <span class="status-dot"></span>
                <span>{status}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section_header(title: str) -> None:
    st.markdown(f"<div class='section-header'>{title}</div>", unsafe_allow_html=True)


def render_metric_card(label: str, value: Any, delta: str | None = None) -> None:
    delta_html = f"<div class='delta'>{delta}</div>" if delta else ""
    st.markdown(
        f"""
        <div class='metric-card'>
            <div class='label'>{label}</div>
            <div class='value'>{value}</div>
            {delta_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_status_badge(text: str, tone: str = "neutral") -> str:
    tone_class = "status-badge"
    if tone == "positive":
        tone_class += " positive-badge"
    elif tone == "negative":
        tone_class += " negative-badge"
    elif tone == "warning":
        tone_class += " warning-badge"
    return f"<span class='{tone_class}'>{text}</span>"


def format_currency(value: Any) -> str:
    if value is None or pd.isna(value):
        return "N/A"
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return str(value)
    if abs(numeric) >= 10000000:
        return f"₹{numeric / 10000000:.2f} Cr"
    return f"₹{numeric:,.2f} Cr"


def format_percentage(value: Any, digits: int = 2) -> str:
    if value is None or pd.isna(value):
        return "N/A"
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return str(value)
    return f"{numeric:.{digits}f}%"


def format_ratio(value: Any, digits: int = 2) -> str:
    if value is None or pd.isna(value):
        return "N/A"
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return str(value)
    return f"{numeric:.{digits}f}x"


def apply_chart_theme(
    fig: Any,
    title: str | None = None,
    x_title: str | None = None,
    y_title: str | None = None,
    show_legend: bool = True,
) -> Any:
    if title is not None:
        fig.update_layout(title=title)

    fig.update_layout(
        paper_bgcolor=COLORS["surface"],
        plot_bgcolor=COLORS["surface"],
        font={"color": COLORS["text"], "family": "IBM Plex Sans, Segoe UI, sans-serif", "size": 13},
        title_font={"size": 16, "color": COLORS["text"]},
        margin={"l": 14, "r": 14, "t": 56, "b": 14},
        showlegend=show_legend,
        legend={"bgcolor": "rgba(15, 23, 42, 0.55)", "bordercolor": COLORS["border"], "borderwidth": 1},
        hoverlabel={"bgcolor": "#0F172A", "bordercolor": COLORS["border"], "font": {"color": COLORS["text"], "size": 12}},
    )

    fig.update_xaxes(
        title_text=x_title,
        showline=True,
        linewidth=1,
        linecolor=COLORS["border"],
        showgrid=False,
        zeroline=False,
    )

    fig.update_yaxes(
        title_text=y_title,
        showline=True,
        linewidth=1,
        linecolor=COLORS["border"],
        showgrid=True,
        gridcolor="rgba(156, 163, 175, 0.12)",
        zeroline=False,
    )

    return fig
