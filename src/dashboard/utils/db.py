import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).resolve().parents[3]
DB = BASE_DIR / "data/database/nifty100.db"


def get_connection():
    return sqlite3.connect(DB)


def _table_exists(conn, table_name):
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    )
    return cursor.fetchone() is not None


def _get_columns(conn, table_name):
    if not _table_exists(conn, table_name):
        return []
    return [row[1] for row in conn.execute(f"PRAGMA table_info({table_name})")]


def _has_column(conn, table_name, column_name):
    return column_name in _get_columns(conn, table_name)


@st.cache_data(ttl=600)
def get_companies():
    conn = get_connection()
    if not _table_exists(conn, "companies"):
        conn.close()
        return pd.DataFrame()

    df = pd.read_sql_query("SELECT * FROM companies", conn)
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_ratios(ticker=None, year=None):
    conn = get_connection()
    if not _table_exists(conn, "financial_ratios"):
        conn.close()
        return pd.DataFrame()

    query = "SELECT * FROM financial_ratios"
    params = []
    conditions = []

    if ticker is not None:
        conditions.append("company_id = ?")
        params.append(ticker)

    if year is not None:
        conditions.append("year = ?")
        params.append(str(year))

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_pl(ticker=None, year=None):
    conn = get_connection()
    if not _table_exists(conn, "profitandloss"):
        conn.close()
        return pd.DataFrame()

    query = "SELECT * FROM profitandloss"
    params = []
    conditions = []

    if ticker is not None:
        conditions.append("company_id = ?")
        params.append(ticker)

    if year is not None:
        conditions.append("year = ?")
        params.append(str(year))

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_bs(ticker=None):
    conn = get_connection()
    if not _table_exists(conn, "balancesheet"):
        conn.close()
        return pd.DataFrame()

    query = "SELECT * FROM balancesheet"
    params = []
    if ticker is not None:
        query += " WHERE company_id = ?"
        params.append(ticker)

    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_cf(ticker=None):
    conn = get_connection()
    if not _table_exists(conn, "cashflow"):
        conn.close()
        return pd.DataFrame()

    query = "SELECT * FROM cashflow"
    params = []
    if ticker is not None:
        query += " WHERE company_id = ?"
        params.append(ticker)

    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_sectors():
    conn = get_connection()
    if not _table_exists(conn, "sectors"):
        conn.close()
        return pd.DataFrame()

    df = pd.read_sql_query("SELECT * FROM sectors", conn)
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_peers(group_name=None):
    conn = get_connection()
    if not _table_exists(conn, "peer_groups"):
        conn.close()
        return pd.DataFrame()

    if group_name is None:
        df = pd.read_sql_query("SELECT * FROM peer_groups", conn)
    else:
        df = pd.read_sql_query(
            "SELECT * FROM peer_groups WHERE peer_group_name = ?",
            conn,
            params=(group_name,),
        )

    conn.close()
    return df


@st.cache_data(ttl=600)
def get_market_cap(year=None):
    conn = get_connection()
    if not _table_exists(conn, "market_cap"):
        conn.close()
        return pd.DataFrame()

    query = "SELECT * FROM market_cap"
    params = []
    if year is not None:
        query += " WHERE year = ?"
        params.append(int(year))

    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_valuation(ticker):
    conn = get_connection()
    if not _table_exists(conn, "valuation"):
        conn.close()
        return pd.DataFrame()

    df = pd.read_sql_query(
        "SELECT * FROM valuation WHERE company_id = ?",
        conn,
        params=(ticker,),
    )
    conn.close()
    return df


# -------------------------------
# Dashboard Helper Functions
# -------------------------------

@st.cache_data(ttl=600)
def get_company_list():
    conn = get_connection()
    if not _table_exists(conn, "companies"):
        conn.close()
        return pd.DataFrame(columns=["id", "company_name"])

    df = pd.read_sql_query(
        """
        SELECT
            id,
            company_name
        FROM companies
        ORDER BY company_name
    """,
        conn,
    )

    conn.close()
    return df


@st.cache_data(ttl=600)
def get_latest_year():
    conn = get_connection()
    if not _table_exists(conn, "financial_ratios"):
        conn.close()
        return None

    year = pd.read_sql_query(
        """
        SELECT MAX(year) AS latest_year
        FROM financial_ratios
    """,
        conn,
    )

    conn.close()
    return year.iloc[0]["latest_year"] if not year.empty else None


@st.cache_data(ttl=600)
def get_years():
    conn = get_connection()
    if not _table_exists(conn, "financial_ratios"):
        conn.close()
        return []

    years = pd.read_sql_query(
        """
        SELECT DISTINCT year
        FROM financial_ratios
        WHERE year <> 'TTM'
        ORDER BY year
    """,
        conn,
    )

    conn.close()
    return years["year"].tolist() if not years.empty else []


@st.cache_data(ttl=600)
def get_company_profile(ticker):
    conn = get_connection()
    if not _table_exists(conn, "companies"):
        conn.close()
        return pd.DataFrame()

    df = pd.read_sql_query(
        "SELECT * FROM companies WHERE id = ?",
        conn,
        params=(ticker,),
    )

    conn.close()
    return df


@st.cache_data(ttl=600)
def get_top_companies(limit=5):
    conn = get_connection()
    if not _table_exists(conn, "financial_ratios"):
        conn.close()
        return pd.DataFrame()

    df = pd.read_sql_query(
        """
    SELECT
        company_id,
        return_on_equity_pct,
        net_profit_margin_pct
    FROM financial_ratios
    ORDER BY return_on_equity_pct DESC
    LIMIT ?
    """,
        conn,
        params=(limit,),
    )

    conn.close()
    return df


@st.cache_data(ttl=600)
def get_pros_cons(ticker):
    conn = get_connection()
    if not _table_exists(conn, "prosandcons"):
        conn.close()
        return pd.DataFrame()

    df = pd.read_sql_query(
        "SELECT * FROM prosandcons WHERE company_id = ?",
        conn,
        params=(ticker,),
    )

    conn.close()
    return df


@st.cache_data(ttl=600)
def get_stock_prices(ticker=None):
    conn = get_connection()
    if not _table_exists(conn, "stock_prices"):
        conn.close()
        return pd.DataFrame()

    query = "SELECT * FROM stock_prices"
    params = []
    if ticker is not None:
        query += " WHERE company_id = ?"
        params.append(ticker)

    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df