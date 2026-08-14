import sqlite3
from pathlib import Path

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

DB_PATH = BASE_DIR / "data" / "database" / "nifty100.db"

OUTPUT_DIR = BASE_DIR / "reports" / "portfolio"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

PDF_PATH = OUTPUT_DIR / "portfolio_summary.pdf"


# ============================================================
# DATABASE
# ============================================================

conn = sqlite3.connect(DB_PATH)

companies = pd.read_sql(
    "SELECT * FROM companies",
    conn,
)

ratios = pd.read_sql(
    "SELECT * FROM financial_ratios",
    conn,
)

sectors = pd.read_sql(
    "SELECT * FROM sectors",
    conn,
)

conn.close()


# ============================================================
# NORMALIZE
# ============================================================

companies["company_id"] = (
    companies["company_id"]
    .astype(str)
    .str.strip()
)

ratios["company_id"] = (
    ratios["company_id"]
    .astype(str)
    .str.strip()
)

ratios["year"] = (
    ratios["year"]
    .astype(str)
    .str.strip()
)


# ============================================================
# FIND COMPANY / SECTOR COLUMNS
# ============================================================

def find_column(df, candidates):
    for candidate in candidates:
        if candidate in df.columns:
            return candidate
    return None


ticker_col = find_column(
    companies,
    ["ticker", "symbol", "stock_code"],
)

name_col = find_column(
    companies,
    ["company_name", "name"],
)

sector_col = find_column(
    companies,
    ["broad_sector", "sector"],
)


if ticker_col is None:
    raise RuntimeError("Could not find ticker column in companies table.")

if name_col is None:
    raise RuntimeError("Could not find company name column in companies table.")


# ============================================================
# SECTOR MAPPING
# ============================================================

sector_map = {}

if "company_id" in sectors.columns:
    possible_sector = find_column(
        sectors,
        ["broad_sector", "sector", "sector_name"],
    )

    if possible_sector:
        sector_map = dict(
            zip(
                sectors["company_id"].astype(str).str.strip(),
                sectors[possible_sector].astype(str),
            )
        )


# ============================================================
# NUMERIC COLUMNS
# ============================================================

KPI_COLUMNS = {
    "ROE": "return_on_equity_pct",
    "ROCE": None,
    "Revenue CAGR": None,
    "OPM": "operating_profit_margin_pct",
    "Debt / Equity": "debt_to_equity",
    "FCF": "free_cash_flow_cr",
}


# ============================================================
# OPTIONAL ROCE / CAGR DATA
# ============================================================

# ROCE may not exist in financial_ratios.
# Use companies table if available.

roce_col = find_column(
    companies,
    ["roce_pct", "roce_percentage", "return_on_capital_employed_pct"],
)

if roce_col:
    KPI_COLUMNS["ROCE"] = roce_col


# ============================================================
# YEAR SORTING
# ============================================================

def year_sort_key(value):
    value = str(value)

    digits = "".join(ch for ch in value if ch.isdigit())

    if digits:
        return int(digits[:4])

    return 0


ratios["_year_sort"] = ratios["year"].apply(year_sort_key)

ratios = ratios.sort_values(
    ["company_id", "_year_sort"]
)


# ============================================================
# TREND
# ============================================================

def trend_arrow(current, previous):
    """
    Return trend arrow.

    Improved = ↑
    Declined = ↓
    Flat within 2% = →
    """

    if pd.isna(current) or pd.isna(previous):
        return "→"

    try:
        current = float(current)
        previous = float(previous)
    except (TypeError, ValueError):
        return "→"

    if previous == 0:
        if current > 0:
            return "↑"
        if current < 0:
            return "↓"
        return "→"

    change = (current - previous) / abs(previous)

    if abs(change) <= 0.02:
        return "→"

    if change > 0:
        return "↑"

    return "↓"


# ============================================================
# FORMAT
# ============================================================

def fmt(value, suffix=""):
    if pd.isna(value):
        return "N/A"

    try:
        return f"{float(value):,.2f}{suffix}"
    except (TypeError, ValueError):
        return "N/A"


# ============================================================
# COMPANY DATA
# ============================================================

company_rows = []

for _, company in companies.iterrows():

    company_id = str(company["company_id"]).strip()

    ticker = str(
        company[ticker_col]
    ).strip()

    company_name = str(
        company[name_col]
    ).strip()

    if sector_col:
        sector = str(company[sector_col]).strip()
    else:
        sector = sector_map.get(company_id, "Unknown")

    company_ratio = ratios[
        ratios["company_id"] == company_id
    ].copy()

    if company_ratio.empty:
        continue

    company_ratio = company_ratio.sort_values("_year_sort")

    latest = company_ratio.iloc[-1]

    previous = (
        company_ratio.iloc[-2]
        if len(company_ratio) >= 2
        else None
    )

    metrics = {}

    # ROE
    metrics["ROE"] = latest.get(
        "return_on_equity_pct",
        float("nan"),
    )

    # ROCE
    if roce_col:
        metrics["ROCE"] = company.get(
            roce_col,
            float("nan"),
        )
    else:
        metrics["ROCE"] = float("nan")

    # OPM
    metrics["OPM"] = latest.get(
        "operating_profit_margin_pct",
        float("nan"),
    )

    # D/E
    metrics["Debt / Equity"] = latest.get(
        "debt_to_equity",
        float("nan"),
    )

    # FCF
    metrics["FCF"] = latest.get(
        "free_cash_flow_cr",
        float("nan"),
    )

    # Revenue CAGR is not guaranteed to exist in ratios.
    # Leave it unavailable rather than inventing it.
    metrics["Revenue CAGR"] = float("nan")

    trends = {}

    for metric, value in metrics.items():

        column = KPI_COLUMNS.get(metric)

        if (
            metric == "ROCE"
            and roce_col
        ):
            trends[metric] = "→"

        elif (
            column
            and column in company_ratio.columns
            and previous is not None
        ):
            trends[metric] = trend_arrow(
                latest[column],
                previous[column],
            )

        else:
            trends[metric] = "→"

    company_rows.append(
        {
            "ticker": ticker,
            "company_name": company_name,
            "sector": sector,
            "metrics": metrics,
            "trends": trends,
        }
    )


# ============================================================
# ALPHABETICAL ORDER
# ============================================================

company_rows.sort(
    key=lambda x: x["ticker"].upper()
)


print("=" * 70)
print("DAY 35 - PORTFOLIO SUMMARY PDF")
print("=" * 70)

print(
    f"Companies included: {len(company_rows)}"
)


# ============================================================
# PDF STYLES
# ============================================================

title_style = ParagraphStyle(
    "Title",
    fontName="Helvetica-Bold",
    fontSize=20,
    leading=24,
    alignment=TA_CENTER,
    textColor=colors.HexColor("#12355B"),
)

subtitle_style = ParagraphStyle(
    "Subtitle",
    fontName="Helvetica",
    fontSize=10,
    leading=13,
    alignment=TA_CENTER,
    textColor=colors.HexColor("#555555"),
)

section_style = ParagraphStyle(
    "Section",
    fontName="Helvetica-Bold",
    fontSize=11,
    leading=14,
    textColor=colors.HexColor("#12355B"),
)

kpi_style = ParagraphStyle(
    "KPI",
    fontName="Helvetica-Bold",
    fontSize=10,
    leading=13,
    alignment=TA_CENTER,
)

value_style = ParagraphStyle(
    "Value",
    fontName="Helvetica-Bold",
    fontSize=15,
    leading=18,
    alignment=TA_CENTER,
)


# ============================================================
# PDF
# ============================================================

doc = SimpleDocTemplate(
    str(PDF_PATH),
    pagesize=A4,
    rightMargin=15 * mm,
    leftMargin=15 * mm,
    topMargin=15 * mm,
    bottomMargin=15 * mm,
)

story = []


# ============================================================
# PAGE GENERATION
# ============================================================

for index, row in enumerate(company_rows):

    story.append(
        Paragraph(
            row["company_name"],
            title_style,
        )
    )

    story.append(
        Spacer(1, 3 * mm)
    )

    story.append(
        Paragraph(
            f"<b>{row['ticker']}</b> &nbsp;&nbsp; | &nbsp;&nbsp; "
            f"{row['sector']}",
            subtitle_style,
        )
    )

    story.append(
        Spacer(1, 8 * mm)
    )

    story.append(
        Paragraph(
            "Key Financial KPIs",
            section_style,
        )
    )

    story.append(
        Spacer(1, 3 * mm)
    )

    # Six KPI cards
    kpi_names = [
        "ROE",
        "ROCE",
        "Revenue CAGR",
        "OPM",
        "Debt / Equity",
        "FCF",
    ]

    kpi_cells = []

    for metric in kpi_names:

        value = row["metrics"].get(
            metric,
            float("nan"),
        )

        arrow = row["trends"].get(
            metric,
            "→",
        )

        if metric in {
            "ROE",
            "ROCE",
            "Revenue CAGR",
            "OPM",
        }:
            display_value = fmt(value, "%")

        elif metric == "Debt / Equity":
            display_value = fmt(value, "x")

        else:
            display_value = fmt(value, " Cr")

        cell = [
            Paragraph(
                metric,
                kpi_style,
            ),
            Spacer(1, 1 * mm),
            Paragraph(
                f"{display_value} {arrow}",
                value_style,
            ),
        ]

        kpi_cells.append(cell)

    table_data = [
        kpi_cells[0:3],
        kpi_cells[3:6],
    ]

    kpi_table = Table(
        table_data,
        colWidths=[
            57 * mm,
            57 * mm,
            57 * mm,
        ],
        rowHeights=[
            28 * mm,
            28 * mm,
        ],
    )

    kpi_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    colors.HexColor("#F3F6FA"),
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.8,
                    colors.HexColor("#B8C4D1"),
                ),
                (
                    "INNERGRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#D5DDE5"),
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "ALIGN",
                    (0, 0),
                    (-1, -1),
                    "CENTER",
                ),
            ]
        )
    )

    story.append(kpi_table)

    story.append(
        Spacer(1, 10 * mm)
    )

    story.append(
        Paragraph(
            "Trend Interpretation",
            section_style,
        )
    )

    story.append(
        Spacer(1, 3 * mm)
    )

    trend_text = (
        "↑ Improved &nbsp;&nbsp;&nbsp; "
        "↓ Declined &nbsp;&nbsp;&nbsp; "
        "→ Flat (within ±2%)"
    )

    story.append(
        Paragraph(
            trend_text,
            subtitle_style,
        )
    )

    story.append(
        Spacer(1, 10 * mm)
    )

    story.append(
        Paragraph(
            "Portfolio Snapshot",
            section_style,
        )
    )

    story.append(
        Spacer(1, 3 * mm)
    )

    snapshot = [
        [
            "Ticker",
            "Sector",
            "ROE",
            "ROCE",
            "OPM",
            "D/E",
        ],
        [
            row["ticker"],
            row["sector"],
            fmt(row["metrics"]["ROE"], "%"),
            fmt(row["metrics"]["ROCE"], "%"),
            fmt(row["metrics"]["OPM"], "%"),
            fmt(row["metrics"]["Debt / Equity"], "x"),
        ],
    ]

    snapshot_table = Table(
        snapshot,
        colWidths=[
            25 * mm,
            65 * mm,
            25 * mm,
            25 * mm,
            25 * mm,
            25 * mm,
        ],
    )

    snapshot_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#12355B"),
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white,
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold",
                ),
                (
                    "FONTNAME",
                    (0, 1),
                    (-1, -1),
                    "Helvetica",
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#B8C4D1"),
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "ALIGN",
                    (0, 0),
                    (-1, -1),
                    "CENTER",
                ),
                (
                    "WORDWRAP",
                    (0, 0),
                    (-1, -1),
                    True,
                ),
            ]
        )
    )

    story.append(snapshot_table)

    if index < len(company_rows) - 1:
        story.append(PageBreak())


# ============================================================
# BUILD
# ============================================================

doc.build(story)

print("\nPDF generated:")
print(PDF_PATH)

print(
    f"Pages expected: {len(company_rows)}"
)