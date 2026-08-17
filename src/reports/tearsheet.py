"""
Sprint 5 - Day 33
Company Tearsheet Generator

Generates a 2-page PDF company tearsheet.

Day 33 requirements:
- Page 1:
    * Navy header with company name + ticker
    * 6 KPI tiles in 2 rows x 3 columns
    * 10-year Revenue + Net Profit bar chart
    * ROE + ROCE dual-axis line chart

- Page 2:
    * Balance Sheet composition stacked bar
    * Cash Flow waterfall
    * Pros
    * Cons
    * Capital Allocation badge

- Uses actual Nifty100_Project database schema.
- Uses:
    output/pros_cons_generated.csv
    output/cashflow_intelligence.xlsx

- Test mode generates 5 sample companies.
"""

import argparse
import io
import sqlite3
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

DB = BASE_DIR / "data" / "database" / "nifty100.db"

OUTPUT_DIR = BASE_DIR / "reports" / "tearsheets"

PROS_CONS_FILE = BASE_DIR / "output" / "pros_cons_generated.csv"

CASHFLOW_INTELLIGENCE_FILE = (
    BASE_DIR / "output" / "cashflow_intelligence.xlsx"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# CONSTANTS
# ============================================================

PAGE_WIDTH, PAGE_HEIGHT = A4

NAVY = colors.HexColor("#0B1F3A")
LIGHT_NAVY = colors.HexColor("#163B63")

GREEN = colors.HexColor("#198754")
LIGHT_GREEN = colors.HexColor("#EAF7EF")

RED = colors.HexColor("#C0392B")
LIGHT_RED = colors.HexColor("#FCEDEC")

LIGHT_GREY = colors.HexColor("#F4F6F8")
MID_GREY = colors.HexColor("#D9DEE5")
DARK_GREY = colors.HexColor("#555555")

WHITE = colors.white
BLACK = colors.black


# ============================================================
# REPORTLAB STYLES
# ============================================================

styles = getSampleStyleSheet()

TITLE_STYLE = ParagraphStyle(
    "TearsheetTitle",
    parent=styles["Normal"],
    fontName="Helvetica-Bold",
    fontSize=18,
    leading=21,
    textColor=WHITE,
    alignment=TA_LEFT,
    spaceAfter=0,
)

SUBTITLE_STYLE = ParagraphStyle(
    "TearsheetSubtitle",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=9,
    leading=11,
    textColor=colors.HexColor("#DCE6F2"),
    alignment=TA_LEFT,
)

SECTION_STYLE = ParagraphStyle(
    "Section",
    parent=styles["Heading2"],
    fontName="Helvetica-Bold",
    fontSize=11,
    leading=13,
    textColor=NAVY,
    spaceBefore=3,
    spaceAfter=5,
)

BODY_STYLE = ParagraphStyle(
    "Body",
    parent=styles["BodyText"],
    fontName="Helvetica",
    fontSize=8,
    leading=10,
    textColor=colors.HexColor("#222222"),
)

SMALL_STYLE = ParagraphStyle(
    "Small",
    parent=styles["BodyText"],
    fontName="Helvetica",
    fontSize=6.8,
    leading=8.2,
    textColor=DARK_GREY,
)

KPI_LABEL_STYLE = ParagraphStyle(
    "KPILabel",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=7,
    leading=8,
    textColor=DARK_GREY,
    alignment=TA_CENTER,
)

KPI_VALUE_STYLE = ParagraphStyle(
    "KPIValue",
    parent=styles["Normal"],
    fontName="Helvetica-Bold",
    fontSize=12,
    leading=14,
    textColor=NAVY,
    alignment=TA_CENTER,
)

BULLET_STYLE = ParagraphStyle(
    "Bullet",
    parent=styles["BodyText"],
    fontName="Helvetica",
    fontSize=7.5,
    leading=9.5,
    leftIndent=10,
    firstLineIndent=-7,
    textColor=colors.HexColor("#222222"),
)

BADGE_STYLE = ParagraphStyle(
    "Badge",
    parent=styles["Normal"],
    fontName="Helvetica-Bold",
    fontSize=10,
    leading=12,
    textColor=WHITE,
    alignment=TA_CENTER,
)


# ============================================================
# HELPERS
# ============================================================

def safe_float(value):
    """Convert a value to float safely."""

    if value is None:
        return np.nan

    try:
        if pd.isna(value):
            return np.nan
    except (TypeError, ValueError):
        pass

    try:
        return float(value)
    except (ValueError, TypeError):
        return np.nan


def clean_year(value):
    """
    Extract a 4-digit year from values such as:
    Mar 2024
    Mar-24
    Dec 2012
    2024
    """

    if value is None:
        return np.nan

    text = str(value).strip()

    # Four digit year
    import re

    match = re.search(r"(19|20)\d{2}", text)

    if match:
        return int(match.group(0))

    # Handle Mar-24 / Mar 24
    match = re.search(r"[-\s](\d{2})$", text)

    if match:
        yy = int(match.group(1))

        if yy <= 30:
            return 2000 + yy

        return 1900 + yy

    return np.nan


def format_number(value, decimals=1):
    """Format numeric values for display."""

    value = safe_float(value)

    if pd.isna(value):
        return "N/A"

    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:.{decimals}f}M"

    if abs(value) >= 100_000:
        return f"{value / 100_000:.{decimals}f}L"

    if abs(value) >= 1_000:
        return f"{value / 1_000:.{decimals}f}K"

    return f"{value:,.{decimals}f}"


def format_pct(value, decimals=1):
    """Format percentage."""

    value = safe_float(value)

    if pd.isna(value):
        return "N/A"

    return f"{value:.{decimals}f}%"


def truncate_text(text, max_chars=240):
    """Prevent very long paragraphs."""

    if text is None:
        return ""

    text = str(text).strip()

    if len(text) <= max_chars:
        return text

    return text[: max_chars - 3] + "..."


def normalize_company_id(value):
    """Normalize company identifiers."""

    if pd.isna(value):
        return ""

    return str(value).strip().upper()


def safe_column(df, column, default=np.nan):
    """Return column if available, otherwise a default series."""

    if column in df.columns:
        return df[column]

    return pd.Series(default, index=df.index)


# ============================================================
# DATABASE LOADING
# ============================================================

def load_database():
    """Load all required tables from SQLite."""

    if not DB.exists():
        raise FileNotFoundError(
            f"Database not found:\n{DB}"
        )

    conn = sqlite3.connect(DB)

    try:
        companies = pd.read_sql(
            "SELECT * FROM companies",
            conn,
        )

        profit = pd.read_sql(
            "SELECT * FROM profitandloss",
            conn,
        )

        cashflow = pd.read_sql(
            "SELECT * FROM cashflow",
            conn,
        )

        balance = pd.read_sql(
            "SELECT * FROM balancesheet",
            conn,
        )

        sectors = pd.read_sql(
            "SELECT * FROM sectors",
            conn,
        )

    finally:
        conn.close()

    return (
        companies,
        profit,
        cashflow,
        balance,
        sectors,
    )


# ============================================================
# LOAD EXTERNAL OUTPUTS
# ============================================================

def load_external_outputs():
    """Load Day 30 and Day 31 outputs."""

    if PROS_CONS_FILE.exists():
        pros_cons = pd.read_csv(PROS_CONS_FILE)
    else:
        print(
            f"WARNING: Pros/Cons file not found:\n"
            f"{PROS_CONS_FILE}"
        )

        pros_cons = pd.DataFrame(
            columns=[
                "company_id",
                "type",
                "rule_id",
                "text",
                "confidence_pct",
            ]
        )

    if CASHFLOW_INTELLIGENCE_FILE.exists():
        cashflow_intelligence = pd.read_excel(
            CASHFLOW_INTELLIGENCE_FILE
        )
    else:
        print(
            f"WARNING: Cash flow intelligence file not found:\n"
            f"{CASHFLOW_INTELLIGENCE_FILE}"
        )

        cashflow_intelligence = pd.DataFrame()

    return pros_cons, cashflow_intelligence


# ============================================================
# NORMALIZATION
# ============================================================

def normalize_data(
    companies,
    profit,
    cashflow,
    balance,
    sectors,
    pros_cons,
    cashflow_intelligence,
):
    """Normalize company IDs and years."""

    # -------------------------
    # Company IDs
    # -------------------------

    for df, column in [
        (companies, "id"),
        (profit, "company_id"),
        (cashflow, "company_id"),
        (balance, "company_id"),
        (sectors, "company_id"),
    ]:
        if column in df.columns:
            df[column] = (
                df[column]
                .astype(str)
                .str.strip()
                .str.upper()
            )

    if "company_id" in pros_cons.columns:
        pros_cons["company_id"] = (
            pros_cons["company_id"]
            .astype(str)
            .str.strip()
            .str.upper()
        )

    if "company_id" in cashflow_intelligence.columns:
        cashflow_intelligence["company_id"] = (
            cashflow_intelligence["company_id"]
            .astype(str)
            .str.strip()
            .str.upper()
        )

    # -------------------------
    # Years
    # -------------------------

    for df in [
        profit,
        cashflow,
        balance,
    ]:
        if "year" in df.columns:
            df["year_num"] = df["year"].apply(
                clean_year
            )

    return (
        companies,
        profit,
        cashflow,
        balance,
        sectors,
        pros_cons,
        cashflow_intelligence,
    )


# ============================================================
# COMPANY NAME / SECTOR
# ============================================================

def get_company_name(company_row, company_id):
    """Get best available company name."""

    possible_columns = [
        "company_name",
        "name",
    ]

    for column in possible_columns:

        if column in company_row.index:

            value = company_row[column]

            if (
                value is not None
                and not pd.isna(value)
                and str(value).strip()
                and str(value).strip().lower()
                != "nan"
            ):
                return str(value).strip()

    return company_id


def get_sector(company_id, company_row, sectors):
    """Get sector from sectors table or companies table."""

    if (
        "sector" in company_row.index
        and pd.notna(company_row["sector"])
    ):
        return str(company_row["sector"])

    if not sectors.empty:

        match = sectors[
            sectors["company_id"] == company_id
        ]

        if not match.empty and "broad_sector" in match.columns:
            value = match.iloc[0]["broad_sector"]

            if pd.notna(value):
                return str(value)

    return "Unknown Sector"


# ============================================================
# LATEST RECORD
# ============================================================

def get_latest_record(df):
    """Return latest year record."""

    if df.empty:
        return None

    temp = df.copy()

    if "year_num" in temp.columns:
        temp = temp.sort_values(
            "year_num",
            na_position="first",
        )

    return temp.iloc[-1]


# ============================================================
# KPI CALCULATION
# ============================================================

def calculate_kpis(
    company_id,
    profit_company,
    cashflow_company,
    balance_company,
    company_row,
    cashflow_intelligence,
):
    """Calculate six primary tearsheet KPIs."""

    latest_profit = get_latest_record(
        profit_company
    )

    latest_cashflow = get_latest_record(
        cashflow_company
    )

    latest_balance = get_latest_record(
        balance_company
    )

    # -------------------------
    # Revenue
    # -------------------------

    revenue = np.nan

    if latest_profit is not None:
        revenue = safe_float(
            latest_profit.get("sales")
        )

    # -------------------------
    # Net Profit
    # -------------------------

    net_profit = np.nan

    if latest_profit is not None:
        net_profit = safe_float(
            latest_profit.get("net_profit")
        )

    # -------------------------
    # ROE
    # -------------------------

    roe = np.nan

    if (
        "roe_percentage" in company_row.index
    ):
        roe = safe_float(
            company_row["roe_percentage"]
        )

    # If company-level ROE unavailable,
    # try latest profit ratio fields.

    if pd.isna(roe) and (
        latest_profit is not None
        and "roe_percentage"
        in latest_profit.index
    ):
        roe = safe_float(
            latest_profit["roe_percentage"]
        )

    # -------------------------
    # ROCE
    # -------------------------

    roce = np.nan

    if (
        "roce_percentage" in company_row.index
    ):
        roce = safe_float(
            company_row["roce_percentage"]
        )

    # -------------------------
    # OPM
    # -------------------------

    opm = np.nan

    if latest_profit is not None:
        opm = safe_float(
            latest_profit.get(
                "opm_percentage"
            )
        )

    # -------------------------
    # EPS
    # -------------------------

    eps = np.nan

    if latest_profit is not None:
        eps = safe_float(
            latest_profit.get("eps")
        )

    # -------------------------
    # Cash Flow Intelligence
    # -------------------------

    intelligence = None

    if not cashflow_intelligence.empty:

        matches = cashflow_intelligence[
            cashflow_intelligence["company_id"]
            == company_id
        ]

        if not matches.empty:
            intelligence = matches.iloc[0]

    return {
        "revenue": revenue,
        "net_profit": net_profit,
        "roe": roe,
        "roce": roce,
        "opm": opm,
        "eps": eps,
        "intelligence": intelligence,
        "latest_profit": latest_profit,
        "latest_cashflow": latest_cashflow,
        "latest_balance": latest_balance,
    }


# ============================================================
# CHART 1
# ============================================================

def create_revenue_profit_chart(
    profit_company,
):
    """
    Create 10-year Revenue + Net Profit bar chart.
    """

    data = profit_company.copy()

    data = data.dropna(
        subset=["year_num"]
    )

    data = (
        data
        .sort_values("year_num")
        .drop_duplicates(
            subset=["year_num"],
            keep="last",
        )
        .tail(10)
    )

    if data.empty:
        return None

    years = data["year_num"].astype(int)

    revenue = pd.to_numeric(
        data["sales"],
        errors="coerce",
    )

    profit = pd.to_numeric(
        data["net_profit"],
        errors="coerce",
    )

    x = np.arange(len(years))

    fig, ax = plt.subplots(
        figsize=(7.0, 2.45),
        dpi=160,
    )

    width = 0.38

    ax.bar(
        x - width / 2,
        revenue,
        width,
        label="Revenue",
    )

    ax.bar(
        x + width / 2,
        profit,
        width,
        label="Net Profit",
    )

    ax.set_xticks(x)

    ax.set_xticklabels(
        years.astype(str),
        fontsize=7,
    )

    ax.set_title(
        "10-Year Revenue and Net Profit",
        fontsize=10,
        fontweight="bold",
    )

    ax.tick_params(
        axis="y",
        labelsize=7,
    )

    ax.grid(
        axis="y",
        alpha=0.20,
    )

    ax.legend(
        fontsize=7,
        frameon=False,
        loc="upper left",
    )

    fig.tight_layout()

    buffer = io.BytesIO()

    fig.savefig(
        buffer,
        format="png",
        bbox_inches="tight",
    )

    plt.close(fig)

    buffer.seek(0)

    return buffer


# ============================================================
# CHART 2
# ============================================================

def create_roe_roce_chart(
    profit_company,
    company_row,
):
    """
    Create ROE + ROCE dual-axis line chart.

    ROE/ROCE are company-level fields in the supplied schema.
    If historical values are unavailable, the chart displays
    the latest available company-level values.
    """

    # Try historical fields if available.
    historical_roe = (
        "roe_percentage"
        in profit_company.columns
    )

    historical_roce = (
        "roce_percentage"
        in profit_company.columns
    )

    if historical_roe or historical_roce:

        data = profit_company.copy()

        data = data.dropna(
            subset=["year_num"]
        )

        data = (
            data
            .sort_values("year_num")
            .drop_duplicates(
                subset=["year_num"],
                keep="last",
            )
            .tail(10)
        )

        years = data["year_num"].astype(int)

        roe_values = (
            pd.to_numeric(
                data.get(
                    "roe_percentage",
                    np.nan,
                ),
                errors="coerce",
            )
        )

        roce_values = (
            pd.to_numeric(
                data.get(
                    "roce_percentage",
                    np.nan,
                ),
                errors="coerce",
            )
        )

    else:

        # Company-level values.
        latest_year = np.nan

        if "year_num" in profit_company.columns:

            years_available = (
                profit_company["year_num"]
                .dropna()
            )

            if not years_available.empty:
                latest_year = int(
                    years_available.max()
                )

        years = pd.Series(
            [latest_year]
        )

        roe = np.nan

        if (
            "roe_percentage"
            in company_row.index
        ):
            roe = safe_float(
                company_row[
                    "roe_percentage"
                ]
            )

        roce = np.nan

        if (
            "roce_percentage"
            in company_row.index
        ):
            roce = safe_float(
                company_row[
                    "roce_percentage"
                ]
            )

        roe_values = pd.Series([roe])

        roce_values = pd.Series([roce])

    if len(years) == 0:
        return None

    fig, ax1 = plt.subplots(
        figsize=(7.0, 2.45),
        dpi=160,
    )

    x = np.arange(len(years))

    ax1.plot(
        x,
        roe_values,
        marker="o",
        linewidth=1.7,
        label="ROE",
    )

    ax1.set_ylabel(
        "ROE (%)",
        fontsize=7,
    )

    ax1.tick_params(
        axis="y",
        labelsize=7,
    )

    ax1.set_xticks(x)

    ax1.set_xticklabels(
        years.astype(str),
        fontsize=7,
    )

    ax2 = ax1.twinx()

    ax2.plot(
        x,
        roce_values,
        marker="s",
        linewidth=1.7,
        linestyle="--",
        label="ROCE",
    )

    ax2.set_ylabel(
        "ROCE (%)",
        fontsize=7,
    )

    ax2.tick_params(
        axis="y",
        labelsize=7,
    )

    ax1.set_title(
        "ROE and ROCE Trend",
        fontsize=10,
        fontweight="bold",
    )

    ax1.grid(
        axis="y",
        alpha=0.20,
    )

    lines1, labels1 = ax1.get_legend_handles_labels()

    lines2, labels2 = ax2.get_legend_handles_labels()

    ax1.legend(
        lines1 + lines2,
        labels1 + labels2,
        fontsize=7,
        frameon=False,
        loc="upper left",
    )

    fig.tight_layout()

    buffer = io.BytesIO()

    fig.savefig(
        buffer,
        format="png",
        bbox_inches="tight",
    )

    plt.close(fig)

    buffer.seek(0)

    return buffer


# ============================================================
# BALANCE SHEET CHART
# ============================================================

def create_balance_chart(
    balance_company,
):
    """
    Balance Sheet composition stacked bar.

    Equity = equity_capital + reserves
    Borrowings = borrowings
    Other Liabilities = other_liabilities
    """

    data = balance_company.copy()

    data = data.dropna(
        subset=["year_num"]
    )

    data = (
        data
        .sort_values("year_num")
        .drop_duplicates(
            subset=["year_num"],
            keep="last",
        )
        .tail(10)
    )

    if data.empty:
        return None

    years = data["year_num"].astype(int)

    equity_capital = pd.to_numeric(
        safe_column(
            data,
            "equity_capital",
            np.nan,
        ),
        errors="coerce",
    ).fillna(0)

    reserves = pd.to_numeric(
        safe_column(
            data,
            "reserves",
            np.nan,
        ),
        errors="coerce",
    ).fillna(0)

    borrowings = pd.to_numeric(
        safe_column(
            data,
            "borrowings",
            np.nan,
        ),
        errors="coerce",
    ).fillna(0)

    other_liabilities = pd.to_numeric(
        safe_column(
            data,
            "other_liabilities",
            np.nan,
        ),
        errors="coerce",
    ).fillna(0)

    equity = equity_capital + reserves

    x = np.arange(len(years))

    fig, ax = plt.subplots(
        figsize=(7.0, 2.55),
        dpi=160,
    )

    ax.bar(
        x,
        equity,
        label="Equity",
    )

    ax.bar(
        x,
        borrowings,
        bottom=equity,
        label="Borrowings",
    )

    ax.bar(
        x,
        other_liabilities,
        bottom=equity + borrowings,
        label="Other Liabilities",
    )

    ax.set_xticks(x)

    ax.set_xticklabels(
        years.astype(str),
        fontsize=7,
    )

    ax.set_title(
        "Balance Sheet Composition",
        fontsize=10,
        fontweight="bold",
    )

    ax.tick_params(
        axis="y",
        labelsize=7,
    )

    ax.grid(
        axis="y",
        alpha=0.20,
    )

    ax.legend(
        fontsize=6.5,
        frameon=False,
        loc="upper left",
    )

    fig.tight_layout()

    buffer = io.BytesIO()

    fig.savefig(
        buffer,
        format="png",
        bbox_inches="tight",
    )

    plt.close(fig)

    buffer.seek(0)

    return buffer


# ============================================================
# CASH FLOW WATERFALL
# ============================================================

def create_cashflow_waterfall(
    cashflow_company,
):
    """
    Cash Flow waterfall-style chart.

    Components:
    CFO
    CFI
    CFF
    Net Cash Flow
    """

    latest = get_latest_record(
        cashflow_company
    )

    if latest is None:
        return None

    cfo = safe_float(
        latest.get(
            "operating_activity"
        )
    )

    cfi = safe_float(
        latest.get(
            "investing_activity"
        )
    )

    cff = safe_float(
        latest.get(
            "financing_activity"
        )
    )

    net_cash = safe_float(
        latest.get(
            "net_cash_flow"
        )
    )

    labels = [
        "CFO",
        "CFI",
        "CFF",
        "Net Cash Flow",
    ]

    values = [
        cfo,
        cfi,
        cff,
        net_cash,
    ]

    values = [
        0 if pd.isna(v) else v
        for v in values
    ]

    x = np.arange(len(labels))

    fig, ax = plt.subplots(
        figsize=(7.0, 2.35),
        dpi=160,
    )

    ax.bar(
        x,
        values,
        width=0.55,
    )

    ax.axhline(
        0,
        linewidth=0.8,
    )

    ax.set_xticks(x)

    ax.set_xticklabels(
        labels,
        fontsize=7,
    )

    ax.set_title(
        "Latest-Year Cash Flow",
        fontsize=10,
        fontweight="bold",
    )

    ax.tick_params(
        axis="y",
        labelsize=7,
    )

    ax.grid(
        axis="y",
        alpha=0.20,
    )

    for i, value in enumerate(values):

        offset = (
            max(abs(value) * 0.03, 1)
        )

        if value >= 0:
            ypos = value + offset
            va = "bottom"
        else:
            ypos = value - offset
            va = "top"

        ax.text(
            i,
            ypos,
            format_number(value),
            ha="center",
            va=va,
            fontsize=6.5,
        )

    fig.tight_layout()

    buffer = io.BytesIO()

    fig.savefig(
        buffer,
        format="png",
        bbox_inches="tight",
    )

    plt.close(fig)

    buffer.seek(0)

    return buffer


# ============================================================
# HEADER
# ============================================================

def create_header(
    company_name,
    company_id,
    sector,
):
    """Create navy company header."""

    subtitle = (
        f"Ticker: {company_id}   |   "
        f"Sector: {sector}"
    )

    table = Table(
        [
            [
                Paragraph(
                    company_name,
                    TITLE_STYLE,
                )
            ],
            [
                Paragraph(
                    subtitle,
                    SUBTITLE_STYLE,
                )
            ],
        ],
        colWidths=[180 * mm],
        rowHeights=[10 * mm, 7 * mm],
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    NAVY,
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    3,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    3,
                ),
            ]
        )
    )

    return table


# ============================================================
# KPI TILES
# ============================================================

def create_kpi_tiles(kpis):
    """Create 6 KPI tiles in 2 rows x 3 columns."""

    tiles = []

    kpi_data = [
        (
            "Revenue",
            format_number(
                kpis["revenue"]
            ),
        ),
        (
            "Net Profit",
            format_number(
                kpis["net_profit"]
            ),
        ),
        (
            "ROE",
            format_pct(
                kpis["roe"]
            ),
        ),
        (
            "ROCE",
            format_pct(
                kpis["roce"]
            ),
        ),
        (
            "OPM",
            format_pct(
                kpis["opm"]
            ),
        ),
        (
            "EPS",
            format_number(
                kpis["eps"],
                2,
            ),
        ),
    ]

    for label, value in kpi_data:

        tile = Table(
            [
                [
                    Paragraph(
                        label,
                        KPI_LABEL_STYLE,
                    )
                ],
                [
                    Paragraph(
                        value,
                        KPI_VALUE_STYLE,
                    )
                ],
            ],
            colWidths=[57 * mm],
            rowHeights=[7 * mm, 11 * mm],
        )

        tile.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, -1),
                        LIGHT_GREY,
                    ),
                    (
                        "BOX",
                        (0, 0),
                        (-1, -1),
                        0.6,
                        MID_GREY,
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "MIDDLE",
                    ),
                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        3,
                    ),
                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        3,
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        2,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        2,
                    ),
                ]
            )
        )

        tiles.append(tile)

    grid = Table(
        [
            tiles[0:3],
            tiles[3:6],
        ],
        colWidths=[
            59 * mm,
            59 * mm,
            59 * mm,
        ],
        rowHeights=[
            19 * mm,
            19 * mm,
        ],
        hAlign="LEFT",
    )

    grid.setStyle(
        TableStyle(
            [
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    1,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    1,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    1,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    1,
                ),
            ]
        )
    )

    return grid


# ============================================================
# PROS / CONS
# ============================================================

def get_pros_cons(
    company_id,
    pros_cons,
    max_items=4,
):
    """Get strongest Pros and Cons for a company."""

    if pros_cons.empty:
        return [], []

    company_data = pros_cons[
        pros_cons["company_id"]
        == company_id
    ].copy()

    if company_data.empty:
        return [], []

    if "confidence_pct" in company_data.columns:

        company_data[
            "confidence_numeric"
        ] = pd.to_numeric(
            company_data["confidence_pct"],
            errors="coerce",
        )

        company_data = company_data[
            company_data[
                "confidence_numeric"
            ] > 60
        ]

        company_data = company_data.sort_values(
            "confidence_numeric",
            ascending=False,
        )

    pros = company_data[
        company_data["type"]
        .astype(str)
        .str.lower()
        == "pro"
    ]

    cons = company_data[
        company_data["type"]
        .astype(str)
        .str.lower()
        == "con"
    ]

    pro_texts = [
        truncate_text(text)
        for text in pros["text"]
        .head(max_items)
        .tolist()
    ]

    con_texts = [
        truncate_text(text)
        for text in cons["text"]
        .head(max_items)
        .tolist()
    ]

    return pro_texts, con_texts


def create_bullet_section(
    title,
    items,
    positive=True,
):
    """Create wrapped bullet-point section."""

    if positive:
        title_style = ParagraphStyle(
            "ProsTitle",
            parent=SECTION_STYLE,
            textColor=GREEN,
        )

    else:
        title_style = ParagraphStyle(
            "ConsTitle",
            parent=SECTION_STYLE,
            textColor=RED,
        )

    elements = [
        Paragraph(
            title,
            title_style,
        )
    ]

    if not items:

        elements.append(
            Paragraph(
                "No qualifying signals available.",
                SMALL_STYLE,
            )
        )

        return elements

    for item in items:

        safe_item = (
            str(item)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )

        elements.append(
            Paragraph(
                f"• {safe_item}",
                BULLET_STYLE,
            )
        )

        elements.append(
            Spacer(
                1,
                1.2 * mm,
            )
        )

    return elements


# ============================================================
# CAPITAL ALLOCATION BADGE
# ============================================================

def create_capital_allocation_badge(
    intelligence,
):
    """Create capital allocation badge."""

    label = "Unknown"

    if (
        intelligence is not None
        and "capital_allocation_label"
        in intelligence.index
    ):

        value = intelligence[
            "capital_allocation_label"
        ]

        if pd.notna(value):
            label = str(value)

    elif (
        intelligence is not None
        and "capital_allocation"
        in intelligence.index
    ):

        value = intelligence[
            "capital_allocation"
        ]

        if pd.notna(value):
            label = str(value)

    badge = Table(
        [
            [
                Paragraph(
                    "CAPITAL ALLOCATION",
                    SMALL_STYLE,
                )
            ],
            [
                Paragraph(
                    label,
                    BADGE_STYLE,
                )
            ],
        ],
        colWidths=[70 * mm],
        rowHeights=[7 * mm, 12 * mm],
    )

    badge.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    LIGHT_GREY,
                ),
                (
                    "BACKGROUND",
                    (0, 1),
                    (-1, 1),
                    LIGHT_NAVY,
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.7,
                    NAVY,
                ),
                (
                    "ALIGN",
                    (0, 0),
                    (-1, -1),
                    "CENTER",
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    3,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    3,
                ),
            ]
        )
    )

    return badge


# ============================================================
# PAGE FOOTER
# ============================================================

def draw_footer(canvas, doc):
    """Draw page number and footer."""

    canvas.saveState()

    canvas.setStrokeColor(
        MID_GREY
    )

    canvas.line(
        15 * mm,
        10 * mm,
        195 * mm,
        10 * mm,
    )

    canvas.setFont(
        "Helvetica",
        6.5,
    )

    canvas.setFillColor(
        DARK_GREY
    )

    canvas.drawString(
        15 * mm,
        6.5 * mm,
        "Nifty100 Project | Sprint 5 | Day 33",
    )

    canvas.drawRightString(
        195 * mm,
        6.5 * mm,
        f"Page {doc.page}",
    )

    canvas.restoreState()


# ============================================================
# GENERATE TEARSHEET
# ============================================================

def generate_tearsheet(
    company_id,
    companies,
    profit,
    cashflow,
    balance,
    sectors,
    pros_cons,
    cashflow_intelligence,
    output_path=None,
):
    """Generate one complete 2-page tearsheet."""

    company_id = normalize_company_id(
        company_id
    )

    # --------------------------------------------------------
    # COMPANY
    # --------------------------------------------------------

    company_match = companies[
        companies["id"] == company_id
    ]

    if company_match.empty:
        raise ValueError(
            f"Company not found: {company_id}"
        )

    company_row = company_match.iloc[0]

    company_name = get_company_name(
        company_row,
        company_id,
    )

    sector = get_sector(
        company_id,
        company_row,
        sectors,
    )

    # --------------------------------------------------------
    # COMPANY DATA
    # --------------------------------------------------------

    profit_company = profit[
        profit["company_id"]
        == company_id
    ].copy()

    cashflow_company = cashflow[
        cashflow["company_id"]
        == company_id
    ].copy()

    balance_company = balance[
        balance["company_id"]
        == company_id
    ].copy()

    # --------------------------------------------------------
    # KPIs
    # --------------------------------------------------------

    kpis = calculate_kpis(
        company_id,
        profit_company,
        cashflow_company,
        balance_company,
        company_row,
        cashflow_intelligence,
    )

    intelligence = kpis[
        "intelligence"
    ]

    # --------------------------------------------------------
    # OUTPUT PATH
    # --------------------------------------------------------

    if output_path is None:

        output_path = (
            OUTPUT_DIR
            / f"{company_id}_tearsheet.pdf"
        )

    output_path = Path(
        output_path
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # --------------------------------------------------------
    # DOCUMENT
    # --------------------------------------------------------

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=12 * mm,
        bottomMargin=15 * mm,
        title=f"{company_name} - Company Tearsheet",
        author="Nifty100 Project",
    )

    story = []

    # ========================================================
    # PAGE 1
    # ========================================================

    story.append(
        create_header(
            company_name,
            company_id,
            sector,
        )
    )

    story.append(
        Spacer(
            1,
            4 * mm,
        )
    )

    story.append(
        Paragraph(
            "Key Performance Indicators",
            SECTION_STYLE,
        )
    )

    story.append(
        create_kpi_tiles(kpis)
    )

    story.append(
        Spacer(
            1,
            4 * mm,
        )
    )

    # Revenue / Profit chart

    revenue_chart = (
        create_revenue_profit_chart(
            profit_company
        )
    )

    if revenue_chart is not None:

        story.append(
            Image(
                revenue_chart,
                width=180 * mm,
                height=62 * mm,
            )
        )

    else:

        story.append(
            Paragraph(
                "Revenue and net profit history unavailable.",
                SMALL_STYLE,
            )
        )

    story.append(
        Spacer(
            1,
            2 * mm,
        )
    )

    # ROE / ROCE chart

    roe_roce_chart = (
        create_roe_roce_chart(
            profit_company,
            company_row,
        )
    )

    if roe_roce_chart is not None:

        story.append(
            Image(
                roe_roce_chart,
                width=180 * mm,
                height=62 * mm,
            )
        )

    else:

        story.append(
            Paragraph(
                "ROE / ROCE trend unavailable.",
                SMALL_STYLE,
            )
        )

    # ========================================================
    # PAGE 2
    # ========================================================

    story.append(
        PageBreak()
    )

    story.append(
        Paragraph(
            f"{company_name} — Financial Structure & Intelligence",
            SECTION_STYLE,
        )
    )

    # Balance sheet

    balance_chart = create_balance_chart(
        balance_company
    )

    if balance_chart is not None:

        story.append(
            Image(
                balance_chart,
                width=180 * mm,
                height=65 * mm,
            )
        )

    else:

        story.append(
            Paragraph(
                "Balance sheet history unavailable.",
                SMALL_STYLE,
            )
        )

    story.append(
        Spacer(
            1,
            2 * mm,
        )
    )

    # Cash flow

    cashflow_chart = (
        create_cashflow_waterfall(
            cashflow_company
        )
    )

    if cashflow_chart is not None:

        story.append(
            Image(
                cashflow_chart,
                width=180 * mm,
                height=60 * mm,
            )
        )

    else:

        story.append(
            Paragraph(
                "Cash flow information unavailable.",
                SMALL_STYLE,
            )
        )

    story.append(
        Spacer(
            1,
            2 * mm,
        )
    )

    # ========================================================
    # PROS + CONS
    # ========================================================

    pros, cons = get_pros_cons(
        company_id,
        pros_cons,
        max_items=3,
    )

    pros_elements = create_bullet_section(
        "Pros",
        pros,
        positive=True,
    )

    cons_elements = create_bullet_section(
        "Cons",
        cons,
        positive=False,
    )

    pros_table = Table(
        [
            [
                pros_elements,
                cons_elements,
            ]
        ],
        colWidths=[
            88 * mm,
            88 * mm,
        ],
    )

    pros_table.setStyle(
        TableStyle(
            [
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    3,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    3,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    2,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    2,
                ),
                (
                    "BOX",
                    (0, 0),
                    (0, 0),
                    0.5,
                    colors.HexColor(
                        "#D5EEDC"
                    ),
                ),
                (
                    "BOX",
                    (1, 0),
                    (1, 0),
                    0.5,
                    colors.HexColor(
                        "#F1D1CE"
                    ),
                ),
                (
                    "BACKGROUND",
                    (0, 0),
                    (0, 0),
                    LIGHT_GREEN,
                ),
                (
                    "BACKGROUND",
                    (1, 0),
                    (1, 0),
                    LIGHT_RED,
                ),
            ]
        )
    )

    story.append(
        pros_table
    )

    story.append(
        Spacer(
            1,
            3 * mm,
        )
    )

    # ========================================================
    # CAPITAL ALLOCATION
    # ========================================================

    badge = create_capital_allocation_badge(
        intelligence
    )

    badge_table = Table(
        [
            [
                badge,
            ]
        ],
        colWidths=[180 * mm],
    )

    badge_table.setStyle(
        TableStyle(
            [
                (
                    "ALIGN",
                    (0, 0),
                    (-1, -1),
                    "CENTER",
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
            ]
        )
    )

    story.append(
        badge_table
    )

    # ========================================================
    # BUILD
    # ========================================================

    doc.build(
        story,
        onFirstPage=draw_footer,
        onLaterPages=draw_footer,
    )

    return output_path


# ============================================================
# SELECT TEST COMPANIES
# ============================================================

def select_test_companies(
    companies,
):
    """
    Day 33 requested test companies:
    TCS, HDFCBANK, RELIANCE, SUNPHARMA, TATASTEEL

    Only return companies that exist in the current DB.
    """

    preferred = [
        "TCS",
        "HDFCBANK",
        "RELIANCE",
        "SUNPHARMA",
        "TATASTEEL",
    ]

    available = set(
        companies["id"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    selected = [
        company
        for company in preferred
        if company in available
    ]

    return selected


# ============================================================
# MAIN
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description=(
            "Day 33 - Nifty100 Company Tearsheet Generator"
        )
    )

    parser.add_argument(
        "--company",
        type=str,
        help=(
            "Generate tearsheet for one company, "
            "e.g. TCS"
        ),
    )

    parser.add_argument(
        "--test",
        action="store_true",
        help=(
            "Generate the 5 Day-33 test companies"
        ),
    )
    
    parser.add_argument(
    "--batch",
    action="store_true",
    help=(
        "Generate tearsheets for all companies"
        ),
    )

    args = parser.parse_args()

    print("=" * 70)
    print("DAY 33 - COMPANY TEARSHEET GENERATOR")
    print("=" * 70)

    print("\nProject:")
    print(BASE_DIR)

    print("\nDatabase:")
    print(DB)

    # --------------------------------------------------------
    # LOAD
    # --------------------------------------------------------

    (
        companies,
        profit,
        cashflow,
        balance,
        sectors,
    ) = load_database()

    (
        pros_cons,
        cashflow_intelligence,
    ) = load_external_outputs()

    # --------------------------------------------------------
    # NORMALIZE
    # --------------------------------------------------------

    (
        companies,
        profit,
        cashflow,
        balance,
        sectors,
        pros_cons,
        cashflow_intelligence,
    ) = normalize_data(
        companies,
        profit,
        cashflow,
        balance,
        sectors,
        pros_cons,
        cashflow_intelligence,
    )

    print("\nData Loaded:")
    print(
        "Companies           :",
        len(companies),
    )
    print(
        "Profit & Loss       :",
        len(profit),
    )
    print(
        "Cash Flow           :",
        len(cashflow),
    )
    print(
        "Balance Sheet       :",
        len(balance),
    )
    print(
        "Sectors             :",
        len(sectors),
    )
    print(
        "Pros/Cons            :",
        len(pros_cons),
    )
    print(
        "Cashflow Intelligence:",
        len(cashflow_intelligence),
    )

    # --------------------------------------------------------
    # SELECT COMPANIES
    # --------------------------------------------------------

    if args.company:
        company_id = normalize_company_id(
            args.company
        )
        company_ids = [company_id]

    elif args.batch:
        # Day 34:
        # Generate tearsheets for all companies.
        company_ids = sorted(
            companies["id"]
            .dropna()
            .astype(str)
            .str.strip()
            .unique()
        )

    elif args.test:
        company_ids = select_test_companies(
            companies
        )

    else:
        # Default Day 33 behaviour:
        # Generate the required 5 test companies.
        company_ids = select_test_companies(
            companies
        )

    if not company_ids:

        raise RuntimeError(
            "No valid companies found for tearsheet generation."
        )

    print("\nCompanies selected:")

    for company_id in company_ids:
        print(
            " -",
            company_id,
        )

    # --------------------------------------------------------
    # GENERATE
    # --------------------------------------------------------

    generated = []

    for company_id in company_ids:

        print(
            f"\nGenerating tearsheet: {company_id}"
        )

        try:

            output_path = generate_tearsheet(
                company_id=company_id,
                companies=companies,
                profit=profit,
                cashflow=cashflow,
                balance=balance,
                sectors=sectors,
                pros_cons=pros_cons,
                cashflow_intelligence=(
                    cashflow_intelligence
                ),
            )

            size_kb = (
                output_path.stat().st_size
                / 1024
            )

            print(
                "Created:",
                output_path,
            )

            print(
                f"Size: {size_kb:.1f} KB"
            )

            generated.append(
                output_path
            )

        except Exception as exc:  # noqa: BLE001

            print(
                f"ERROR generating {company_id}:"
            )

            print(
                repr(exc)
            )

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("DAY 33 TEARSHEET GENERATION COMPLETED")
    print("=" * 70)

    print(
        "\nGenerated:",
        len(generated),
        "/",
        len(company_ids),
    )

    for path in generated:
        print(
            " -",
            path,
        )

    print(
        "\nReview the generated PDFs visually."
    )

    print(
        "Required Day 33 test companies:"
    )

    print(
        "TCS, HDFCBANK, RELIANCE, SUNPHARMA, TATASTEEL"
    )


if __name__ == "__main__":
    main()