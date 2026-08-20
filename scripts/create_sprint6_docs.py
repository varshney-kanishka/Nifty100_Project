from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)
from reportlab.lib import colors


BASE_DIR = Path(__file__).resolve().parents[1]
DOCS_DIR = BASE_DIR / "docs"
DOCS_DIR.mkdir(parents=True, exist_ok=True)


styles = getSampleStyleSheet()

title_style = ParagraphStyle(
    "TitleCustom",
    parent=styles["Title"],
    fontSize=20,
    leading=24,
    alignment=TA_CENTER,
    spaceAfter=20,
)

heading_style = ParagraphStyle(
    "HeadingCustom",
    parent=styles["Heading1"],
    fontSize=15,
    leading=19,
    spaceBefore=12,
    spaceAfter=8,
)

subheading_style = ParagraphStyle(
    "SubHeadingCustom",
    parent=styles["Heading2"],
    fontSize=12,
    leading=15,
    spaceBefore=8,
    spaceAfter=5,
)

body_style = ParagraphStyle(
    "BodyCustom",
    parent=styles["BodyText"],
    fontSize=9.5,
    leading=14,
    spaceAfter=6,
)


def make_table(data, widths=None):
    table = Table(data, colWidths=widths, repeatRows=1)

    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#333333")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("LEADING", (0, 0), (-1, -1), 11),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1),
                 [colors.white, colors.HexColor("#f5f5f5")]),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )

    return table


def build_analyst_guide():
    path = DOCS_DIR / "analyst_guide.pdf"

    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        rightMargin=42,
        leftMargin=42,
        topMargin=42,
        bottomMargin=42,
        title="Nifty100 Analytics Platform - Analyst Guide",
    )

    story = []

    story.append(
        Paragraph(
            "Nifty100 Analytics Platform",
            title_style,
        )
    )

    story.append(
        Paragraph(
            "Analyst Guide",
            title_style,
        )
    )

    story.append(
        Paragraph(
            "Version: Sprint 6 Release | Dataset: 92 Nifty 100 Companies",
            body_style,
        )
    )

    story.append(Spacer(1, 10))

    story.append(
        Paragraph("1. Platform Overview", heading_style)
    )

    story.append(
        Paragraph(
            "The Nifty100 Analytics Platform is a Python-based financial "
            "analytics platform covering 92 companies from the Nifty 100 "
            "dataset. It combines financial statement analysis, ratios, "
            "cash-flow intelligence, machine-learning clustering, NLP "
            "insights, automated reporting, dashboards and REST APIs.",
            body_style,
        )
    )

    story.append(
        Paragraph("2. Core Analytical Modules", heading_style)
    )

    modules = [
        ["Module", "Purpose"],
        ["Financial Ratios", "Profitability, leverage, efficiency and coverage metrics"],
        ["CAGR", "Historical growth analysis"],
        ["Peer Analysis", "Comparison of companies within sectors"],
        ["Valuation", "P/E, P/B, EV/EBITDA and dividend metrics"],
        ["Capital Allocation", "CapEx, working capital, debt and cash deployment"],
        ["Cash-Flow Intelligence", "CFO quality, FCF, conversion and CapEx intensity"],
        ["Clustering", "KMeans-based financial archetype classification"],
        ["NLP", "Rule-based pros, cons and confidence scoring"],
        ["Screener", "Investment-oriented filtering presets"],
        ["Reporting", "Company tear sheets and sector reports"],
        ["REST API", "Programmatic access to analytical results"],
        ["Dashboard", "Interactive Streamlit/Plotly analytics"],
    ]

    story.append(make_table(modules, [125, 350]))

    story.append(
        Paragraph("3. Cash-Flow Intelligence", heading_style)
    )

    story.append(
        Paragraph(
            "The cash-flow module evaluates the quality and sustainability "
            "of cash generation using CFO/PAT, free cash flow, FCF conversion, "
            "CapEx intensity, cash-flow risk and related metrics.",
            body_style,
        )
    )

    cashflow_rules = [
        ["Metric", "Interpretation"],
        ["CFO / PAT", "Cash generation relative to reported profit"],
        ["FCF", "Cash remaining after capital expenditure"],
        ["FCF Conversion", "Conversion of accounting profit into free cash flow"],
        ["CapEx Intensity", "Capital expenditure relative to operating scale"],
        ["CFO Quality", "Classification of operating cash-flow strength"],
        ["Cash-Flow Risk", "Flag identifying potential cash-generation concerns"],
    ]

    story.append(make_table(cashflow_rules, [130, 345]))

    story.append(
        Paragraph("4. Machine-Learning Clustering", heading_style)
    )

    story.append(
        Paragraph(
            "KMeans clustering is used with five clusters and a fixed "
            "random state of 42. The clustering pipeline assigns all 92 "
            "companies to financial archetypes after preprocessing and "
            "missing-value handling.",
            body_style,
        )
    )

    clusters = [
        ["Cluster", "Archetype"],
        ["0", "High-Leverage / Cash-Flow Stressed"],
        ["1", "Low-Leverage / Cash-Generative Compounders"],
        ["2", "Capital-Efficient High-ROCE Companies"],
        ["3", "Leverage-Heavy / Weak Cash Conversion"],
        ["4", "Capital-Intensive Profit Reinvestment"],
    ]

    story.append(make_table(clusters, [70, 405]))

    story.append(
        Paragraph("5. NLP Intelligence", heading_style)
    )

    story.append(
        Paragraph(
            "The NLP pipeline parses financial analysis records and "
            "generates company-level pros and cons using predefined "
            "financial rules. Statements are assigned confidence scores "
            "and integrated into company tear sheets.",
            body_style,
        )
    )

    story.append(
        Paragraph("6. Automated Reports", heading_style)
    )

    reports = [
        ["Report", "Expected Output"],
        ["Company Tear Sheets", "92 HTML reports"],
        ["Sector Reports", "10 HTML reports"],
        ["Radar Charts", "Company-level analytical visualizations"],
        ["Portfolio Reports", "Portfolio-level analytical summaries"],
        ["Pytest Report", "Automated test execution report"],
    ]

    story.append(make_table(reports, [150, 325]))

    story.append(
        Paragraph("7. REST API", heading_style)
    )

    story.append(
        Paragraph(
            "The FastAPI service exposes analytics through versioned API "
            "routes covering companies, screening, sectors, peers, "
            "valuation, portfolio statistics, documents and health.",
            body_style,
        )
    )

    api_items = [
        ["Area", "Purpose"],
        ["Companies", "Company-level analytical information"],
        ["Screener", "Preset and filter-based company screening"],
        ["Sectors", "Sector-level analytics"],
        ["Peers", "Peer comparison"],
        ["Valuation", "Valuation metrics"],
        ["Portfolio", "Portfolio-level statistics"],
        ["Documents", "Report/document access"],
        ["Health", "Service and database health"],
    ]

    story.append(make_table(api_items, [120, 355]))

    story.append(
        Paragraph("8. Testing", heading_style)
    )

    story.append(
        Paragraph(
            "The project uses pytest for automated validation across ETL, "
            "KPI, analytics and API functionality. The current verification "
            "run completed with 67 passed tests and one dependency deprecation "
            "warning.",
            body_style,
        )
    )

    story.append(
        Paragraph("9. Key Project Commands", heading_style)
    )

    commands = [
        ["Command", "Purpose"],
        ["make load", "Load/refresh data"],
        ["make ratios", "Generate analytical ratios"],
        ["make test", "Run automated tests"],
        ["make report", "Generate reports"],
        ["make dashboard", "Launch dashboard workflow"],
        ["make api", "Launch API workflow"],
        ["make clean", "Clean generated artifacts"],
    ]

    story.append(make_table(commands, [120, 355]))

    story.append(
        Paragraph("10. Output Structure", heading_style)
    )

    story.append(
        Paragraph(
            "Important generated outputs include company_clusters_v4.csv, "
            "cashflow_intelligence_v4.csv, pros_cons_generated.csv, "
            "company tear sheets, sector reports, radar charts, portfolio "
            "reports and pytest_report.html.",
            body_style,
        )
    )

    story.append(
        Paragraph("11. Analyst Interpretation Rules", heading_style)
    )

    rules = [
        "Monetary values are interpreted in INR Crore where applicable.",
        "Financials should be treated carefully when applying generic debt/equity screening logic.",
        "Negative-base CAGR situations should be interpreted as turnaround cases rather than ordinary CAGR.",
        "Zero interest expense should be interpreted as debt-free for relevant reporting logic.",
        "Simulated datasets must be explicitly labelled SIMULATED.",
        "NLP statements are ranked by confidence score.",
        "Analytical outputs should be validated before investment interpretation.",
    ]

    for rule in rules:
        story.append(
            Paragraph("• " + rule, body_style)
        )

    story.append(
        Paragraph("12. Current Release Status", heading_style)
    )

    story.append(
        Paragraph(
            "The current project contains 92 generated company tear sheets, "
            "10 sector reports and an automated test suite with 67 passing "
            "tests. Final Sprint 6 sign-off should additionally verify the "
            "required documentation and acceptance-gate evidence.",
            body_style,
        )
    )

    doc.build(story)

    print(f"Created: {path}")


def build_acceptance_checklist():
    path = DOCS_DIR / "acceptance_checklist.pdf"

    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        rightMargin=42,
        leftMargin=42,
        topMargin=42,
        bottomMargin=42,
        title="Nifty100 Sprint 6 Acceptance Checklist",
    )

    story = []

    story.append(
        Paragraph(
            "Nifty100 Analytics Platform",
            title_style,
        )
    )

    story.append(
        Paragraph(
            "Sprint 6 Acceptance Checklist",
            title_style,
        )
    )

    story.append(
        Paragraph(
            "Release verification document",
            body_style,
        )
    )

    story.append(
        Paragraph("Acceptance Gates", heading_style)
    )

    gates = [
        ["Gate", "Acceptance Requirement", "Status"],
        ["1", "92-company clustering output exists", "PASS"],
        ["2", "Five KMeans clusters are generated", "PASS"],
        ["3", "Cluster archetypes are profiled", "PASS"],
        ["4", "Cash-flow intelligence output exists", "PASS"],
        ["5", "92 unique companies represented in core outputs", "PASS"],
        ["6", "NLP pros/cons output exists", "PASS"],
        ["7", "Company tear sheets generated", "PASS"],
        ["8", "92 company tear sheets verified", "PASS"],
        ["9", "Sector reports generated", "PASS"],
        ["10", "10 sector reports verified", "PASS"],
        ["11", "API test suite exists", "PASS"],
        ["12", "ETL test suite exists", "PASS"],
        ["13", "KPI test suite exists", "PASS"],
        ["14", "Automated pytest execution completed", "PASS"],
        ["15", "67 pytest tests passed", "PASS"],
        ["16", "No pytest test failures", "PASS"],
        ["17", "Dashboard/report artifacts exist", "VERIFY"],
        ["18", "Performance/load-test evidence verified", "VERIFY"],
        ["19", "Analyst guide generated", "VERIFY"],
        ["20", "Acceptance checklist generated", "VERIFY"],
    ]

    story.append(
        make_table(gates, [35, 390, 70])
    )

    story.append(
        Paragraph("Evidence Summary", heading_style)
    )

    evidence = [
        ["Evidence", "Observed Result"],
        ["Company reports", "92 HTML files"],
        ["Sector reports", "10 HTML files"],
        ["Automated tests", "67 passed"],
        ["Test failures", "0"],
        ["Pytest warning", "1 dependency deprecation warning"],
        ["Cluster output", "company_clusters_v4.csv present"],
        ["Cash-flow output", "cashflow_intelligence_v4.csv present"],
        ["NLP output", "pros_cons_generated.csv present"],
        ["Report generator", "scripts/report_generator_v4.py present"],
    ]

    story.append(
        make_table(evidence, [150, 345])
    )

    story.append(
        Paragraph("Final Sign-Off Criteria", heading_style)
    )

    signoff = [
        "All 20 acceptance gates must have evidence.",
        "No functional pytest failures are permitted.",
        "All expected company and sector reports must be present.",
        "API health and endpoint behavior must be verified.",
        "Dashboard availability and load performance must be verified.",
        "Analyst documentation must be present in docs/.",
        "The acceptance checklist itself must be archived with the release.",
    ]

    for item in signoff:
        story.append(
            Paragraph("• " + item, body_style)
        )

    story.append(
        Paragraph("Current Conclusion", heading_style)
    )

    story.append(
        Paragraph(
            "The available evidence confirms substantial Sprint 6 completion: "
            "the core analytical outputs exist, 92 company reports and 10 "
            "sector reports have been generated, and the automated test suite "
            "reports 67 passed tests with zero failures. Gates marked VERIFY "
            "must be checked before declaring final sign-off.",
            body_style,
        )
    )

    doc.build(story)

    print(f"Created: {path}")


if __name__ == "__main__":
    build_analyst_guide()
    build_acceptance_checklist()
    print("\nSprint 6 documentation generation complete.")