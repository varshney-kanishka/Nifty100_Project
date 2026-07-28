from pathlib import Path
import sqlite3
import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).resolve().parents[3]
DB = BASE_DIR / "data/database/nifty100.db"



def get_connection():
    return sqlite3.connect(DB)


@st.cache_data(ttl=600)
def get_companies():
    conn = get_connection()
    return pd.read_sql("SELECT * FROM companies", conn)


@st.cache_data(ttl=600)
def get_ratios(ticker=None, year=None):

    conn = get_connection()

    query = "SELECT * FROM financial_ratios"

    conditions = []

    if ticker:
        conditions.append(f"company_id='{ticker}'")

    if year:
        conditions.append(f"year='{year}'")

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    return pd.read_sql(query, conn)


@st.cache_data(ttl=600)
def get_pl(ticker):

    conn = get_connection()

    return pd.read_sql(
        f"SELECT * FROM profitandloss WHERE company_id='{ticker}'",
        conn,
    )


@st.cache_data(ttl=600)
def get_bs(ticker):

    conn = get_connection()

    return pd.read_sql(
        f"SELECT * FROM balancesheet WHERE company_id='{ticker}'",
        conn,
    )


@st.cache_data(ttl=600)
def get_cf(ticker):

    conn = get_connection()

    return pd.read_sql(
        f"SELECT * FROM cashflow WHERE company_id='{ticker}'",
        conn,
    )


@st.cache_data(ttl=600)
def get_sectors():

    conn = get_connection()

    return pd.read_sql(
        "SELECT * FROM sectors",
        conn,
    )


@st.cache_data(ttl=600)
def get_peers(group_name):

    conn = get_connection()

    return pd.read_sql(
        f"SELECT * FROM peer_groups WHERE peer_group_name='{group_name}'",
        conn,
    )


@st.cache_data(ttl=600)
def get_valuation(ticker):

    conn = get_connection()

    return pd.read_sql(
        f"SELECT * FROM valuation WHERE company_id='{ticker}'",
        conn,
    )
    
# -------------------------------
# Dashboard Helper Functions
# -------------------------------

@st.cache_data(ttl=600)
def get_company_list():
    conn = get_connection()

    df = pd.read_sql("""
        SELECT
            id,
            company_name
        FROM companies
        ORDER BY company_name
    """, conn)

    conn.close()
    return df


@st.cache_data(ttl=600)
def get_latest_year():

    conn = get_connection()

    year = pd.read_sql("""
        SELECT MAX(year) AS latest_year
        FROM financial_ratios
    """, conn)

    conn.close()

    return year.iloc[0]["latest_year"]


@st.cache_data(ttl=600)
def get_years():

    conn = get_connection()

    years = pd.read_sql("""
        SELECT DISTINCT year
        FROM financial_ratios
        WHERE year <> 'TTM'
        ORDER BY year
    """, conn)

    conn.close()

    return years["year"].tolist()

@st.cache_data(ttl=600)
def get_company_profile(ticker):

    conn = get_connection()

    query = f"""
        SELECT *
        FROM companies
        WHERE id='{ticker}'
    """

    df = pd.read_sql(query, conn)

    conn.close()

    return df


@st.cache_data(ttl=600)
def get_top_companies(limit=5):

    conn = get_connection()

    query = f"""
    SELECT
        company_id,
        return_on_equity_pct,
        net_profit_margin_pct
    FROM financial_ratios
    ORDER BY return_on_equity_pct DESC
    LIMIT {limit}
    """

    df = pd.read_sql(query, conn)

    conn.close()

    return df


@st.cache_data(ttl=600)
def get_pros_cons(ticker):

    conn = get_connection()

    df = pd.read_sql(
        f"""
        SELECT *
        FROM prosandcons
        WHERE company_id='{ticker}'
        """,
        conn,
    )

    conn.close()

    return df    