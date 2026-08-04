import os
import runpy
from pathlib import Path

import streamlit as st

st.set_page_config(
    page_title="Nifty 100 Analytics",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("Nifty 100 Analytics Dashboard")

st.write("Welcome to the Nifty 100 Analytics Project")

from utils import db as db_utils

# Show DB connection status in the sidebar
try:
    conn = db_utils.get_connection()
    conn.execute("SELECT 1")
    conn.close()
    st.sidebar.success("DB connected")
except Exception as exc:  # pragma: no cover - surface errors to user
    st.sidebar.error(f"DB connection error: {exc}")


def _pretty_name(filename: str) -> str:
    name = Path(filename).stem
    # remove numeric prefixes like '01_' and convert underscores
    parts = name.split("_", 1)
    if len(parts) == 2 and parts[0].isdigit():
        name = parts[1]
    return name.replace("_", " ").title()


PAGES_DIR = Path(__file__).parent / "pages"
page_files = sorted([p.name for p in PAGES_DIR.glob("*.py")]) if PAGES_DIR.exists() else []
page_map = { _pretty_name(f): f for f in page_files }

if not page_map:
    st.sidebar.info("No pages found in the pages/ directory.")
else:
    selected = st.sidebar.selectbox("Select a page", list(page_map.keys()))
    page_path = PAGES_DIR / page_map[selected]
    # Execute the selected page file in its own namespace so top-level code runs
    runpy.run_path(str(page_path), run_name="__main__")
