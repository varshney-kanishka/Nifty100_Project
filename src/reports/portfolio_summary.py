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
# NORMALIZE IDS
# ============================================================

companies["id"] = (
    companies["id"]
    .astype(str)
    .str.strip()
)

ratios["company_id"] = (
    ratios["company_id"]
    .astype(str)
    .str.strip()
)

sectors["company_id"] = (
    sectors["company_id"]
    .astype(str)
    .str.strip()
)

ratios["year"] = (
    ratios["year"]
    .astype(str)
    .str.strip()
)


# ============================================================
# YEAR SORTING
# ============================================================

def year_sort_key(value):
    value = str(value)

    digits = "".join(
        ch for ch in value
        if ch.isdigit()
    )

    if digits:
        return int(digits[:4])

    return 0


ratios["_year_sort"] = ratios["year"].apply(
    year_sort_key
)

ratios = ratios.sort_values(
    ["company_id", "_year_sort"]
)


# ============================================================
# SECTOR MAPPING
# ============================================================

sector_map = {}

if not sectors.empty:

    sector_map = dict(
        zip(
            sectors["company_id"],
            sectors["broad_sector"].fillna("Unknown"),
        )
    )


# ============================================================
# TICKER
# ============================================================

# The companies table has no ticker column.
# The company ID is therefore used as the ticker/code.

ticker_col = "id"
name_col = "company_name"


# ============================================================
# TREND
# ============================================================

def trend_arrow(current, previous):

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

    change = (
        (current - previous)
        / abs(previous)
    )

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

    company_id = str(
        company["id"]
    ).strip()

    ticker = company_id

    company_name = str(
        company[name_col]
    ).strip()

    sector = sector_map.get(
        company_id,
        "Unknown",
    )


    # --------------------------------------------------------
    # Company ratios
    # --------------------------------------------------------

    company_ratio = ratios[
        ratios["company_id"] == company_id
    ].copy()


    if company_ratio.empty:
        continue


    company_ratio = company_ratio.sort_values(
        "_year_sort"
    )


    latest = company_ratio.iloc[-1]


    previous = (
        company_ratio.iloc[-2]
        if len(company_ratio) >= 2
        else None
    )


    # --------------------------------------------------------
    # Metrics
    # --------------------------------------------------------

    metrics = {}


    # ROE
    roe_ratio = latest.get(
        "return_on_equity_pct",
        float("nan"),
    )

    roe_company = company.get(
        "roe_percentage",
        float("nan"),
    )

    metrics["ROE"] = (
        roe_company
        if not pd.isna(roe_company)
        else roe_ratio
    )


    # ROCE
    roce_company = company.get(
        "roce_percentage",
        float("nan"),
    )

    roce_ratio = latest.get(
        "return_on_capital_employed_pct",
        float("nan"),
    )

    metrics["ROCE"] = (
        roce_company
        if not pd.isna(roce_company)
        else roce_ratio
    )


    # Revenue CAGR
    # Not available in current schema.
    metrics["Revenue CAGR"] = float("nan")


    # OPM
    metrics["OPM"] = latest.get(
        "operating_profit_margin_pct",
        float("nan"),
    )


    # Debt / Equity
    metrics["Debt / Equity"] = latest.get(
        "debt_to_equity",
        float("nan"),
    )


    # FCF
    metrics["FCF"] = latest.get(
        "free_cash_flow_cr",
        float("nan"),
    )


    # --------------------------------------------------------
    # Trends
    # --------------------------------------------------------

    trends = {}


    if previous is not None:

        trends["ROE"] = trend_arrow(
            latest.get(
                "return_on_equity_pct",
                float("nan"),
            ),
            previous.get(
                "return_on_equity_pct",
                float("nan"),
            ),
        )


        trends["ROCE"] = trend_arrow(
            latest.get(
                "return_on_capital_employed_pct",
                float("nan"),
            ),
            previous.get(
                "return_on_capital_employed_pct",
                float("nan"),
            ),
        )


        trends["OPM"] = trend_arrow(
            latest.get(
                "operating_profit_margin_pct",
                float("nan"),
            ),
            previous.get(
                "operating_profit_margin_pct",
                float("nan"),
            ),
        )


        trends["Debt / Equity"] = trend_arrow(
            latest.get(
                "debt_to_equity",
                float("nan"),
            ),
            previous.get(
                "debt_to_equity",
                float("nan"),
            ),
        )


        trends["FCF"] = trend_arrow(
            latest.get(
                "free_cash_flow_cr",
                float("nan"),
            ),
            previous.get(
                "free_cash_flow_cr",
                float("nan"),
            ),
        )

    else:

        trends = {
            "ROE": "→",
            "ROCE": "→",
            "Revenue CAGR": "→",
            "OPM": "→",
            "Debt / Equity": "→",
            "FCF": "→",
        }


    trends["Revenue CAGR"] = "→"


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


# ============================================================
# VALIDATION
# ============================================================

print("=" * 70)
print("DAY 35 - PORTFOLIO SUMMARY PDF")
print("=" * 70)

print(
    f"Companies in database: {len(companies)}"
)

print(
    f"Companies included in report: {len(company_rows)}"
)


if len(company_rows) != len(companies):

    missing = set(
        companies["id"]
    ) - {
        row["ticker"]
        for row in company_rows
    }

    print(
        f"WARNING: {len(missing)} companies have no ratio data."
    )

    print(
        "Missing:",
        sorted(missing),
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
# PDF DOCUMENT
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

    # --------------------------------------------------------
    # Title
    # --------------------------------------------------------

    story.append(
        Paragraph(
            row["company_name"],
            title_style,
        )
    )

    story.append(
        Spacer(1, 3 * mm)
    )


    # --------------------------------------------------------
    # Company metadata
    # --------------------------------------------------------

    story.append(
        Paragraph(
            f"<b>{row['ticker']}</b> "
            f"&nbsp;&nbsp; | &nbsp;&nbsp; "
            f"{row['sector']}",
            subtitle_style,
        )
    )

    story.append(
        Spacer(1, 8 * mm)
    )


    # --------------------------------------------------------
    # KPI heading
    # --------------------------------------------------------

    story.append(
        Paragraph(
            "Key Financial KPIs",
            section_style,
        )
    )

    story.append(
        Spacer(1, 3 * mm)
    )


    # --------------------------------------------------------
    # KPI cards
    # --------------------------------------------------------

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

            display_value = fmt(
                value,
                "%",
            )

        elif metric == "Debt / Equity":

            display_value = fmt(
                value,
                "x",
            )

        else:

            display_value = fmt(
                value,
                " Cr",
            )


        cell = [
            Paragraph(
                metric,
                kpi_style,
            ),
            Spacer(
                1,
                1 * mm,
            ),
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


    # --------------------------------------------------------
    # Trend interpretation
    # --------------------------------------------------------

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


    # --------------------------------------------------------
    # Portfolio snapshot
    # --------------------------------------------------------

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
            fmt(
                row["metrics"]["ROE"],
                "%",
            ),
            fmt(
                row["metrics"]["ROCE"],
                "%",
            ),
            fmt(
                row["metrics"]["OPM"],
                "%",
            ),
            fmt(
                row["metrics"]["Debt / Equity"],
                "x",
            ),
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


    # --------------------------------------------------------
    # New page
    # --------------------------------------------------------

    if index < len(company_rows) - 1:

        story.append(
            PageBreak()
        )


# ============================================================
# BUILD
# ============================================================

doc.build(story)


print()
print("PDF generated:")
print(PDF_PATH)

print(
    f"Pages expected: {len(company_rows)}"
)

print("=" * 70)