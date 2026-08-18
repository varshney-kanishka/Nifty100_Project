import runpy
from pathlib import Path

import streamlit as st
from utils.theme import apply_theme
from utils.db import get_companies, get_sectors

st.set_page_config(
    page_title="Nifty 100 Analytics",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_theme()

st.sidebar.markdown(
    """
    <div class="theme-brand">
        <div class="brand-title">Nifty 100</div>
        <div class="brand-subtitle">Analytics Intelligence</div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.sidebar.caption("Portfolio monitoring and company analytics")

from utils import db as db_utils

# Show DB connection status in the sidebar
try:
    conn = db_utils.get_connection()
    conn.execute("SELECT 1")
    conn.close()
    st.sidebar.markdown("<div class='status-badge positive-badge'>DB connected</div>", unsafe_allow_html=True)
except Exception as exc:  # noqa: BLE001
    st.sidebar.markdown(f"<div class='status-badge negative-badge'>DB error: {exc}</div>", unsafe_allow_html=True)


def _pretty_name(filename: str) -> str:
    name = Path(filename).stem
    # remove numeric prefixes like '01_' and convert underscores
    parts = name.split("_", 1)
    if len(parts) == 2 and parts[0].isdigit():
        name = parts[1]
    return name.replace("_", " ").title()


PAGES_DIR = Path(__file__).parent / "pages"
page_files = sorted([p.name for p in PAGES_DIR.glob("*.py")]) if PAGES_DIR.exists() else []
default_page_map = {_pretty_name(f): f for f in page_files}

custom_order = [
    "Home",
    "Profile",
    "Sectors",
    "Screener",
    "Peers",
    "Trends",
    "Capital",
    "Reports",
]

page_map = {}
for page_name in custom_order:
    if page_name in default_page_map:
        page_map[page_name] = default_page_map[page_name]
for name, filename in default_page_map.items():
    if name not in page_map:
        page_map[name] = filename

if not page_map:
    st.sidebar.info("No pages found in the pages/ directory.")
else:
    st.sidebar.markdown("<div class='nav-section'>Navigation</div>", unsafe_allow_html=True)

    st.sidebar.markdown("<div class='nav-section'>Global Filters</div>", unsafe_allow_html=True)
    companies_df = get_companies()
    sectors_df = get_sectors()

    company_options = ["All"]
    if not companies_df.empty and "id" in companies_df.columns:
        company_options.extend(sorted(companies_df["id"].dropna().astype(str).unique().tolist()))

    sector_options = ["All"]
    if not sectors_df.empty and "broad_sector" in sectors_df.columns:
        sector_options.extend(sorted(sectors_df["broad_sector"].dropna().astype(str).unique().tolist()))

    market_cap_options = ["All"]
    if not sectors_df.empty and "market_cap_category" in sectors_df.columns:
        market_cap_options.extend(sorted(sectors_df["market_cap_category"].dropna().astype(str).unique().tolist()))

    global_company = st.sidebar.selectbox("Company", company_options, help="Applies where company-level filtering is supported.")
    global_sector = st.sidebar.selectbox("Sector", sector_options, help="Applies where sector-level filtering is supported.")
    global_market_cap = st.sidebar.selectbox("Market-Cap Category", market_cap_options, help="Applies where market-cap category data is available.")

    st.session_state["global_filters"] = {
        "company": global_company,
        "sector": global_sector,
        "market_cap_category": global_market_cap,
    }

    selected = st.sidebar.selectbox("Select a page", list(page_map.keys()))
    page_path = PAGES_DIR / page_map[selected]
    # Execute the selected page file in its own namespace so top-level code runs
    runpy.run_path(str(page_path), run_name="__main__")
