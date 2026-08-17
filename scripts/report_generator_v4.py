import pandas as pd
from pathlib import Path
from html import escape


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]

OUTPUT_DIR = BASE_DIR / "output"

REPORT_DIR = OUTPUT_DIR / "reports"
COMPANY_REPORT_DIR = REPORT_DIR / "company_tearsheets"
SECTOR_REPORT_DIR = REPORT_DIR / "sector_reports"

COMPANY_REPORT_DIR.mkdir(parents=True, exist_ok=True)
SECTOR_REPORT_DIR.mkdir(parents=True, exist_ok=True)

CLUSTER_FILE = OUTPUT_DIR / "company_clusters_v4.csv"
CASHFLOW_FILE = OUTPUT_DIR / "cashflow_intelligence_v4.csv"
NLP_FILE = OUTPUT_DIR / "pros_cons_generated.csv"

YEAR = 2024
EXPECTED_COMPANIES = 92


# ============================================================
# LOAD DATA
# ============================================================

print("=" * 70)
print("NIFTY100 REPORT GENERATOR V4")
print("=" * 70)

print("\nLoading input files...")

if not CLUSTER_FILE.exists():
    raise FileNotFoundError(f"Missing: {CLUSTER_FILE}")

if not CASHFLOW_FILE.exists():
    raise FileNotFoundError(f"Missing: {CASHFLOW_FILE}")

if not NLP_FILE.exists():
    raise FileNotFoundError(f"Missing: {NLP_FILE}")


clusters = pd.read_csv(CLUSTER_FILE)
cashflow = pd.read_csv(CASHFLOW_FILE)
nlp = pd.read_csv(NLP_FILE)


# ============================================================
# BASIC VALIDATION
# ============================================================

print(f"Cluster rows:   {len(clusters)}")
print(f"Cash-flow rows: {len(cashflow)}")
print(f"NLP rows:       {len(nlp)}")

if clusters["company_id"].nunique() != EXPECTED_COMPANIES:
    raise ValueError("Cluster file does not contain 92 unique companies.")

if cashflow["company_id"].nunique() != EXPECTED_COMPANIES:
    raise ValueError("Cash-flow file does not contain 92 unique companies.")

if nlp["company_id"].nunique() != EXPECTED_COMPANIES:
    raise ValueError("NLP file does not contain 92 unique companies.")


# ============================================================
# NORMALIZE IDS
# ============================================================

for frame in [clusters, cashflow, nlp]:

    frame["company_id"] = (
        frame["company_id"]
        .astype(str)
        .str.strip()
    )


# ============================================================
# MERGE COMPANY DATA
# ============================================================

df = clusters.merge(
    cashflow,
    on="company_id",
    how="left",
    suffixes=("", "_cashflow"),
)


# Keep clustering values as the primary company metadata.
for column in ["company_name", "sector", "sub_sector"]:

    cashflow_column = f"{column}_cashflow"

    if cashflow_column in df.columns:

        df[column] = (
            df[column]
            .fillna(df[cashflow_column])
        )


# ============================================================
# NLP HELPERS
# ============================================================

def get_nlp_items(company_id, statement_type, limit=5):

    company_nlp = nlp[
        (nlp["company_id"] == company_id)
        & (nlp["type"].str.lower() == statement_type)
    ].copy()

    if company_nlp.empty:
        return []

    company_nlp["confidence_pct"] = pd.to_numeric(
        company_nlp["confidence_pct"],
        errors="coerce",
    )

    company_nlp = (
        company_nlp
        .sort_values(
            "confidence_pct",
            ascending=False,
        )
        .head(limit)
    )

    return company_nlp[
        ["text", "confidence_pct", "rule_id"]
    ].to_dict("records")


# ============================================================
# FORMATTING HELPERS
# ============================================================

def fmt(value, decimals=2):

    if pd.isna(value):
        return "N/A"

    try:
        return f"{float(value):,.{decimals}f}"
    except (ValueError, TypeError):
        return escape(str(value))


def fmt_bool(value):

    if pd.isna(value):
        return "N/A"

    return "Yes" if bool(value) else "No"


def safe_filename(name):

    name = str(name)

    invalid = '<>:"/\\|?*'

    for char in invalid:
        name = name.replace(char, "_")

    return name.strip().replace(" ", "_")


def metric_row(label, value):

    return f"""
    <tr>
        <td class="label">{escape(str(label))}</td>
        <td>{escape(str(value))}</td>
    </tr>
    """


# ============================================================
# HTML TEMPLATE
# ============================================================

CSS = """
<style>

body {
    font-family: Arial, Helvetica, sans-serif;
    margin: 40px;
    color: #222;
    line-height: 1.5;
}

h1 {
    font-size: 28px;
    margin-bottom: 5px;
}

h2 {
    margin-top: 30px;
    border-bottom: 2px solid #333;
    padding-bottom: 6px;
}

h3 {
    margin-top: 20px;
}

.subtitle {
    color: #666;
    margin-bottom: 25px;
}

.grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
    margin: 20px 0;
}

.card {
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 15px;
    background: #fafafa;
}

.card-title {
    font-size: 12px;
    color: #666;
    text-transform: uppercase;
}

.card-value {
    font-size: 20px;
    font-weight: bold;
    margin-top: 5px;
}

table {
    width: 100%;
    border-collapse: collapse;
    margin: 15px 0;
}

th {
    background: #333;
    color: white;
    text-align: left;
    padding: 9px;
}

td {
    border: 1px solid #ddd;
    padding: 8px;
}

.label {
    font-weight: bold;
    width: 45%;
}

.pro {
    border-left: 5px solid #2e7d32;
    padding: 10px;
    margin: 8px 0;
    background: #f3faf4;
}

.con {
    border-left: 5px solid #c62828;
    padding: 10px;
    margin: 8px 0;
    background: #fff5f5;
}

.small {
    color: #666;
    font-size: 12px;
}

.footer {
    margin-top: 40px;
    padding-top: 15px;
    border-top: 1px solid #ddd;
    color: #777;
    font-size: 12px;
}

</style>
"""


# ============================================================
# COMPANY TEAR SHEET
# ============================================================

def build_company_report(row):

    company_id = row["company_id"]
    company_name = row["company_name"]

    pros = get_nlp_items(
        company_id,
        "pro",
        limit=5,
    )

    cons = get_nlp_items(
        company_id,
        "con",
        limit=5,
    )

    pros_html = ""

    for item in pros:

        pros_html += f"""
        <div class="pro">
            <strong>Pro</strong><br>
            {escape(str(item["text"]))}
            <div class="small">
                Confidence: {fmt(item["confidence_pct"], 0)}%
                | Rule: {escape(str(item["rule_id"]))}
            </div>
        </div>
        """

    cons_html = ""

    for item in cons:

        cons_html += f"""
        <div class="con">
            <strong>Con</strong><br>
            {escape(str(item["text"]))}
            <div class="small">
                Confidence: {fmt(item["confidence_pct"], 0)}%
                | Rule: {escape(str(item["rule_id"]))}
            </div>
        </div>
        """

    if not pros_html:
        pros_html = "<p>No Pros available.</p>"

    if not cons_html:
        cons_html = "<p>No Cons available.</p>"


    html = f"""
    <!DOCTYPE html>
    <html>

    <head>
        <meta charset="UTF-8">
        <title>{escape(str(company_name))} - Nifty100 Tear Sheet</title>
        {CSS}
    </head>

    <body>

        <h1>{escape(str(company_name))}</h1>

        <div class="subtitle">
            Company ID: {escape(str(company_id))}
            |
            Nifty100 Company Tear Sheet
            |
            Analysis Year: {YEAR}
        </div>


        <h2>Company Overview</h2>

        <table>
            {metric_row("Sector", row.get("sector", "N/A"))}
            {metric_row("Sub-sector", row.get("sub_sector", "N/A"))}
            {metric_row("Cluster", row.get("cluster", "N/A"))}
            {metric_row("Archetype", row.get("archetype", "N/A"))}
            {metric_row("Archetype Description", row.get("archetype_description", "N/A"))}
        </table>


        <h2>Key Financial Metrics</h2>

        <div class="grid">

            <div class="card">
                <div class="card-title">Net Profit Margin</div>
                <div class="card-value">
                    {fmt(row.get("net_profit_margin_pct"))}%
                </div>
            </div>

            <div class="card">
                <div class="card-title">Operating Margin</div>
                <div class="card-value">
                    {fmt(row.get("operating_profit_margin_pct"))}%
                </div>
            </div>

            <div class="card">
                <div class="card-title">ROE</div>
                <div class="card-value">
                    {fmt(row.get("return_on_equity_pct"))}%
                </div>
            </div>

            <div class="card">
                <div class="card-title">ROCE</div>
                <div class="card-value">
                    {fmt(row.get("return_on_capital_employed_pct"))}%
                </div>
            </div>

            <div class="card">
                <div class="card-title">Debt / Equity</div>
                <div class="card-value">
                    {fmt(row.get("debt_to_equity"))}
                </div>
            </div>

            <div class="card">
                <div class="card-title">Interest Coverage</div>
                <div class="card-value">
                    {fmt(row.get("interest_coverage"))}
                </div>
            </div>

        </div>


        <h2>Cash Flow Intelligence</h2>

        <table>

            {metric_row(
                "CFO / PAT",
                fmt(row.get("cfo_pat_ratio"))
            )}

            {metric_row(
                "FCF",
                fmt(row.get("fcf"))
            )}

            {metric_row(
                "FCF Conversion",
                fmt(row.get("fcf_conversion_pct")) + "%"
            )}

            {metric_row(
                "CapEx Intensity",
                fmt(row.get("capex_intensity_pct")) + "%"
            )}

            {metric_row(
                "CFO Quality",
                row.get("cfo_quality", "N/A")
            )}

            {metric_row(
                "Cash-Profit Alignment",
                row.get("cash_profit_alignment", "N/A")
            )}

            {metric_row(
                "FCF Status",
                row.get("fcf_status", "N/A")
            )}

            {metric_row(
                "CapEx Classification",
                row.get("capex_intensity_class", "N/A")
            )}

            {metric_row(
                "Cash-Flow Risk",
                fmt_bool(row.get("cash_flow_risk"))
            )}

            {metric_row(
                "Cash-Flow Score",
                fmt(row.get("cash_flow_score"))
            )}

        </table>


        <h2>Valuation</h2>

        <table>

            {metric_row("P/E Ratio", fmt(row.get("pe_ratio")))}
            {metric_row("P/B Ratio", fmt(row.get("pb_ratio")))}
            {metric_row("EV / EBITDA", fmt(row.get("ev_ebitda")))}
            {metric_row(
                "Dividend Yield",
                fmt(row.get("dividend_yield_pct")) + "%"
            )}

        </table>


        <h2>Investment Pros</h2>

        {pros_html}


        <h2>Investment Cons / Risks</h2>

        {cons_html}


        <div class="footer">

            Generated from the Nifty100 analytical pipeline.
            Analysis year: {YEAR}.
            NLP statements are ranked by confidence score.

        </div>

    </body>

    </html>
    """

    return html


# ============================================================
# GENERATE COMPANY REPORTS
# ============================================================

print("\n" + "=" * 70)
print("GENERATING COMPANY TEAR SHEETS")
print("=" * 70)

company_count = 0

for _, row in df.iterrows():

    html = build_company_report(row)

    filename = (
        safe_filename(row["company_id"])
        + "_tear_sheet.html"
    )

    output_path = COMPANY_REPORT_DIR / filename

    output_path.write_text(
        html,
        encoding="utf-8",
    )

    company_count += 1


print(f"\nCompany tear sheets generated: {company_count}")


# ============================================================
# SECTOR REPORTS
# ============================================================

print("\n" + "=" * 70)
print("GENERATING SECTOR REPORTS")
print("=" * 70)


sector_metrics = [
    "net_profit_margin_pct",
    "operating_profit_margin_pct",
    "return_on_equity_pct",
    "return_on_capital_employed_pct",
    "debt_to_equity",
    "interest_coverage",
    "cfo_pat_ratio",
    "fcf_conversion_pct",
    "capex_intensity_pct",
    "pe_ratio",
    "pb_ratio",
    "ev_ebitda",
    "dividend_yield_pct",
    "cash_flow_score",
]


def build_sector_report(sector, sector_df):

    profile = (
        sector_df[sector_metrics]
        .median(numeric_only=True)
        .round(2)
    )

    company_count = len(sector_df)

    risk_count = int(
        sector_df["cash_flow_risk"]
        .fillna(False)
        .astype(bool)
        .sum()
    )

    positive_fcf = int(
        (
            sector_df["fcf_status"]
            == "Positive"
        ).sum()
    )

    negative_fcf = company_count - positive_fcf


    cfo_distribution = (
        sector_df["cfo_quality"]
        .value_counts()
    )


    metrics_html = ""

    for metric in sector_metrics:

        label = metric.replace("_", " ").title()

        value = profile.get(metric, float("nan"))

        suffix = ""

        if metric.endswith("_pct"):
            suffix = "%"

        metrics_html += metric_row(
            label,
            fmt(value) + suffix,
        )


    cfo_html = ""

    for label in [
        "Strong",
        "Healthy",
        "Weak",
        "Poor",
        "Negative",
    ]:

        count = int(
            cfo_distribution.get(
                label,
                0,
            )
        )

        cfo_html += metric_row(
            label,
            count,
        )


    company_rows = ""

    top_companies = (
        sector_df
        .sort_values(
            "cash_flow_score",
            ascending=False,
        )
        .head(10)
    )


    for _, company in top_companies.iterrows():

        company_rows += f"""
        <tr>
            <td>{escape(str(company["company_id"]))}</td>
            <td>{escape(str(company["company_name"]))}</td>
            <td>{escape(str(company["archetype"]))}</td>
            <td>{fmt(company["cash_flow_score"])}</td>
        </tr>
        """


    return f"""
    <!DOCTYPE html>
    <html>

    <head>
        <meta charset="UTF-8">
        <title>{escape(str(sector))} - Nifty100 Sector Report</title>
        {CSS}
    </head>

    <body>

        <h1>{escape(str(sector))}</h1>

        <div class="subtitle">
            Nifty100 Sector Report | Analysis Year: {YEAR}
        </div>


        <h2>Sector Overview</h2>

        <div class="grid">

            <div class="card">
                <div class="card-title">Companies</div>
                <div class="card-value">
                    {company_count}
                </div>
            </div>

            <div class="card">
                <div class="card-title">Positive FCF</div>
                <div class="card-value">
                    {positive_fcf}
                </div>
            </div>

            <div class="card">
                <div class="card-title">Negative FCF</div>
                <div class="card-value">
                    {negative_fcf}
                </div>
            </div>

            <div class="card">
                <div class="card-title">Cash-Flow Risk</div>
                <div class="card-value">
                    {risk_count}
                </div>
            </div>

        </div>


        <h2>Sector Median Profile</h2>

        <table>
            {metrics_html}
        </table>


        <h2>CFO Quality Distribution</h2>

        <table>
            {cfo_html}
        </table>


        <h2>Top Companies by Cash-Flow Score</h2>

        <table>

            <tr>
                <th>Company ID</th>
                <th>Company</th>
                <th>Archetype</th>
                <th>Cash-Flow Score</th>
            </tr>

            {company_rows}

        </table>


        <div class="footer">

            Generated from the Nifty100 analytical pipeline.
            Analysis year: {YEAR}.

        </div>

    </body>

    </html>
    """


sector_count = 0

for sector in sorted(df["sector"].dropna().unique()):

    sector_df = df[
        df["sector"] == sector
    ].copy()

    html = build_sector_report(
        sector,
        sector_df,
    )

    filename = (
        safe_filename(sector)
        + "_sector_report.html"
    )

    output_path = (
        SECTOR_REPORT_DIR
        / filename
    )

    output_path.write_text(
        html,
        encoding="utf-8",
    )

    sector_count += 1


# ============================================================
# FINAL VALIDATION
# ============================================================

company_files = list(
    COMPANY_REPORT_DIR.glob("*.html")
)

sector_files = list(
    SECTOR_REPORT_DIR.glob("*.html")
)


print("\n" + "=" * 70)
print("REPORT GENERATION COMPLETE")
print("=" * 70)

print(f"\nCompany reports: {len(company_files)}")
print(f"Sector reports:  {len(sector_files)}")

if len(company_files) != EXPECTED_COMPANIES:
    raise ValueError(
        f"Expected {EXPECTED_COMPANIES} company reports "
        f"but found {len(company_files)}"
    )

if len(sector_files) != df["sector"].nunique():
    raise ValueError(
        "Sector report count does not match sector count."
    )

print("\nOutput directories:")

print(
    f"Company reports:\n"
    f"  {COMPANY_REPORT_DIR}"
)

print(
    f"Sector reports:\n"
    f"  {SECTOR_REPORT_DIR}"
)

print("\nValidation:")
print("✓ 92 company tear sheets")
print(f"✓ {len(sector_files)} sector reports")
print("✓ NLP Pros/Cons integrated")
print("✓ Cash-flow intelligence integrated")
print("✓ Cluster/archetype information integrated")
print("✓ Report generation completed")

print("\n" + "=" * 70)
