# Nifty 100 Analytics Platform

A Python-based financial analytics platform for analyzing **92 Nifty 100 companies** using financial statements, financial ratios, valuation metrics, cash-flow intelligence, machine-learning clustering, NLP-generated insights, interactive dashboards, and a REST API.

The platform combines **financial analytics + machine learning + NLP + reporting + API services** into a single Nifty 100 research platform.

---

## 📌 Project Overview

The Nifty 100 Analytics Platform analyzes company-level and sector-level financial information to provide:

* Financial ratio analysis
* Company screening
* Peer comparison
* Valuation analysis
* Historical trend analysis
* Sector analysis
* Capital allocation analysis
* Cash-flow intelligence
* Machine-learning company clustering
* NLP-generated company pros and cons
* Automated company tear sheets
* Automated sector reports
* Portfolio-level statistics
* REST API access to analytics

The current dataset contains **92 Nifty 100 companies**.

---

## 🚀 Key Features

### 1. Company Profile Dashboard

Provides company-level information including:

* Company name
* Company website
* NSE/BSE profiles
* Face value
* Book value
* ROE
* ROCE
* Company overview
* Financial KPIs
* NLP-generated pros and cons

---

### 2. Financial Screener

The platform supports financial screening using predefined investment-oriented presets.

Available presets include:

* Quality Compounder
* Value Pick
* Growth Accelerator
* Dividend Champion
* Debt-Free Bluechip
* Turnaround Watch

The screener returns ranked/filterable company results based on financial characteristics.

---

### 3. Peer Comparison

Companies can be compared with peers within the same broad sector.

The peer analysis includes metrics such as:

* ROE
* ROCE
* Net profit margin
* Operating profit margin
* Debt-to-equity
* Interest coverage
* Asset turnover
* Free cash flow
* EPS
* Dividend payout ratio

---

### 4. Trend Analysis

Historical financial and market data can be analyzed to identify trends in:

* Revenue
* Profit
* Margins
* ROE
* ROCE
* Financial ratios
* Stock prices
* Returns

The platform also calculates CAGR and related performance indicators.

---

### 5. Sector Analysis

Sector-level analysis provides:

* Company count by sector
* Index-weight distribution
* Sector comparisons
* Financial metrics
* Sector-level cash-flow insights
* Sector reports

The current dataset contains **10 broad sectors**.

---

### 6. Capital Allocation Analysis

The platform analyzes how companies allocate capital across areas such as:

* Capital expenditure
* Working capital
* Debt
* Cash flows
* Investment activity

Supporting analytics include capital allocation summaries and working-capital analysis.

---

## 💰 Cash-Flow Intelligence

The cash-flow intelligence module evaluates the quality and sustainability of company cash generation.

Key metrics include:

* Cash Flow from Operations (CFO)
* CFO/PAT
* Free Cash Flow
* FCF conversion
* CapEx intensity
* Cash-flow quality
* Leverage
* Interest coverage

Companies are classified into cash-flow risk/quality categories based on their financial characteristics.

Generated outputs include:

```text
output/
├── cashflow_intelligence_v4.csv
├── cashflow_risk_companies_v4.csv
├── cfo_quality_summary_v4.csv
├── capex_intensity_summary_v4.csv
└── sector_cashflow_summary_v4.csv
```

---

# 🤖 Machine Learning — Company Clustering

The platform uses **KMeans clustering** to group companies according to their financial characteristics.

### Current clustering

* **5 clusters**
* **92 companies**
* Cluster profiles validated
* Company assignments validated

The clusters are interpreted as financial archetypes:

| Cluster   | Archetype                                  |
| --------- | ------------------------------------------ |
| Cluster 0 | High-Leverage / Cash-Flow Stressed         |
| Cluster 1 | Low-Leverage / Cash-Generative Compounders |
| Cluster 2 | Capital-Efficient High-ROCE Companies      |
| Cluster 3 | Leverage-Heavy / Weak Cash Conversion      |
| Cluster 4 | Capital-Intensive Profit Reinvestment      |

Cluster analysis considers characteristics such as:

* Profitability
* ROE
* ROCE
* Debt-to-equity
* Interest coverage
* CFO/PAT
* FCF conversion
* CapEx intensity
* Valuation multiples

Generated clustering outputs include:

```text
output/
├── cluster_archetypes_v4.csv
├── cluster_archetype_profiles_v4.csv
├── cluster_profiles_v4.csv
└── company_clusters_v4.csv
```

---

# 🧠 NLP Intelligence

The NLP module generates company-level:

* Pros
* Cons
* Confidence scores
* Financial explanations

NLP outputs are integrated into the automated company tear sheets.

The report generation pipeline processes **902 NLP records** across the available company/metric information.

---

# 📊 Automated Reporting

The platform automatically generates financial research reports.

### Company Tear Sheets

**92 company tear sheets** are generated.

Each tear sheet integrates:

* Company information
* Financial metrics
* Profitability analysis
* Capital efficiency
* Leverage
* Cash-flow intelligence
* Valuation
* Cluster/archetype classification
* NLP-generated pros and cons

Location:

```text
output/reports/company_tearsheets/
```

### Sector Reports

**10 sector reports** are generated.

Location:

```text
output/reports/sector_reports/
```

---

# 🌐 REST API

The project includes a **FastAPI REST API** for programmatic access to the analytics platform.

### API Technology

* FastAPI
* Uvicorn
* SQLite
* Pandas

### API Base URL

When running locally:

```text
http://127.0.0.1:8000
```

### Interactive API Documentation

FastAPI automatically provides:

```text
http://127.0.0.1:8000/docs
```

and:

```text
http://127.0.0.1:8000/redoc
```

---

## 🔌 API Endpoints

The current API contains **16 application endpoints**.

### General

| Method | Endpoint           | Description                       |
| ------ | ------------------ | --------------------------------- |
| GET    | `/`                | API information                   |
| GET    | `/health`          | API health check                  |
| GET    | `/health/database` | Database health and company count |

### Companies

| Method | Endpoint                              | Description               |
| ------ | ------------------------------------- | ------------------------- |
| GET    | `/companies`                          | Paginated company list    |
| GET    | `/companies/{company_id}`             | Company details           |
| GET    | `/companies/{company_id}/prices`      | Historical company prices |
| GET    | `/companies/{company_id}/performance` | Company performance       |

### Analytics

| Method | Endpoint              | Description                    |
| ------ | --------------------- | ------------------------------ |
| GET    | `/sectors`            | Sector-level summary           |
| GET    | `/screener/{preset}`  | Run a screening preset         |
| GET    | `/market-cap`         | Market-cap distribution        |
| GET    | `/peers/{company_id}` | Peer comparison                |
| GET    | `/portfolio/stats`    | Nifty 100 portfolio statistics |

---

## 🧪 Testing

The project includes automated tests covering:

* API endpoints
* Database connectivity
* Company retrieval
* Pagination
* Sector analysis
* Screeners
* Market-cap analysis
* Peer comparison
* Portfolio statistics
* Stock prices
* Performance calculations
* ETL normalization
* Data validation
* CAGR calculations
* Financial ratios

### Current test status

```text
67 passed
0 failed
```

Run the complete test suite with:

```bash
pytest -q
```

The current test suite produces one dependency deprecation warning related to the `httpx`/Starlette TestClient combination, but **all 67 tests pass successfully**.

---

# 🛠️ Technology Stack

### Programming & Data

* Python
* Pandas
* SQLite
* OpenPyXL

### Visualization & Dashboard

* Streamlit
* Plotly

### Machine Learning

* Scikit-learn
* KMeans clustering

### NLP

* Python NLP processing
* Financial pros/cons generation

### API

* FastAPI
* Uvicorn

### Testing

* Pytest
* FastAPI TestClient

### Development

* Git
* GitHub
* Virtual environment

---

# 📁 Project Structure

```text
Nifty100_Project/
│
├── config/
├── data/
├── db/
├── docs/
├── logs/
├── notebooks/
├── output/
│   └── reports/
│       ├── company_tearsheets/
│       └── sector_reports/
│
├── reports/
│
├── scripts/
│   ├── cashflow_intelligence.py
│   ├── cluster_profiling_v4.py
│   ├── fix_cluster_archetypes_v4.py
│   ├── kmeans_clustering_v4.py
│   └── report_generator_v4.py
│
├── src/
│   ├── analytics/
│   │   ├── cagr.py
│   │   ├── capital_allocation.py
│   │   ├── cashflow_intelligence.py
│   │   ├── cashflow_kpis.py
│   │   ├── debt_leverage.py
│   │   ├── dupont_analysis.py
│   │   ├── peer.py
│   │   ├── ratios.py
│   │   ├── valuation.py
│   │   └── working_capital.py
│   │
│   ├── api/
│   │   └── main.py
│   │
│   ├── dashboard/
│   │   ├── app.py
│   │   ├── pages/
│   │   └── utils/
│   │
│   ├── etl/
│   │   ├── db_loader.py
│   │   ├── db_validator.py
│   │   ├── loader.py
│   │   ├── normaliser.py
│   │   └── validator.py
│   │
│   ├── nlp/
│   │   ├── parser.py
│   │   ├── pros_cons_generator.py
│   │   └── validate_nlp.py
│   │
│   ├── reports/
│   │   ├── portfolio_summary.py
│   │   └── tearsheet.py
│   │
│   └── screener/
│       ├── engine.py
│       ├── export_results.py
│       └── presets.py
│
├── tests/
│   ├── api/
│   │   └── test_api.py
│   ├── etl/
│   │   ├── test_loader.py
│   │   ├── test_normaliser.py
│   │   └── test_validator.py
│   └── kpi/
│       ├── test_cagr.py
│       ├── test_cashflow_kpis.py
│       └── test_ratios.py
│
├── .env
├── .gitignore
├── Makefile
├── nifty100.db
├── pytest.ini
├── requirements.txt
└── README.md
```

---

# ⚙️ Installation

Clone the repository and move into the project directory:

```bash
git clone <your-github-repository-url>
cd Nifty100_Project
```

Create a virtual environment:

```bash
python -m venv venv
```

Activate the environment on Windows PowerShell:

```powershell
.\venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

# ▶️ Running the Dashboard

Start the Streamlit dashboard:

```bash
streamlit run src/dashboard/app.py
```

The dashboard provides pages for:

1. Home
2. Company Profile
3. Screener
4. Peer Comparison
5. Trends
6. Sector Analysis
7. Capital Allocation
8. Reports

---

# ▶️ Running the REST API

Start the FastAPI server with:

```bash
uvicorn src.api.main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

Open the interactive API documentation:

```text
http://127.0.0.1:8000/docs
```

---

# 🔍 Example API Requests

### Health

```text
GET /health
```

Example response:

```json
{
  "status": "healthy"
}
```

### Database Health

```text
GET /health/database
```

Example response:

```json
{
  "status": "healthy",
  "database": "connected",
  "companies": 92
}
```

### Companies

```text
GET /companies?limit=5
```

### Company Details

```text
GET /companies/RELIANCE
```

### Sector Analysis

```text
GET /sectors
```

### Screener

```text
GET /screener/quality_compounder
```

### Peer Comparison

```text
GET /peers/RELIANCE
```

### Portfolio Statistics

```text
GET /portfolio/stats
```

### Historical Prices

```text
GET /companies/RELIANCE/prices
```

### Company Performance

```text
GET /companies/RELIANCE/performance
```

---

# 📈 Example Validated Results

The current project validation confirms:

```text
Companies analyzed:          92
Clusters:                     5
Company tear sheets:         92
Sector reports:              10
FastAPI application routes:  16
Automated tests:             67
Test failures:                0
```

---

# 📦 Generated Outputs

Important generated outputs include:

```text
output/
├── capex_intensity_summary_v4.csv
├── cashflow_intelligence_v4.csv
├── cashflow_risk_companies_v4.csv
├── cfo_quality_summary_v4.csv
├── cluster_archetype_profiles_v4.csv
├── cluster_archetypes_v4.csv
├── cluster_profiles_v4.csv
├── company_clusters_v4.csv
├── sector_cashflow_summary_v4.csv
│
└── reports/
    ├── company_tearsheets/
    │   └── 92 HTML reports
    │
    └── sector_reports/
        └── 10 HTML reports
```

---

# 🧩 Core Modules

### ETL

Handles:

* Data loading
* Normalization
* Database loading
* Data validation
* Company ID validation

### Analytics

Handles:

* Financial ratios
* CAGR
* Cash-flow KPIs
* Debt and leverage
* DuPont analysis
* Peer analysis
* Capital allocation
* Working capital
* Valuation

### Screener

Provides predefined financial screening strategies.

### NLP

Generates and validates company-level pros and cons.

### Clustering

Groups companies into five financial archetypes using KMeans.

### Reporting

Generates company tear sheets and sector reports.

### Dashboard

Provides an interactive Streamlit interface.

### API

Provides programmatic access to company, sector, screening, peer, market-cap, portfolio, price, and performance analytics.

---

# 🏆 Project Highlights

* Analyzed **92 Nifty 100 companies**
* Built a complete financial analytics pipeline
* Implemented financial ratio and valuation analysis
* Added cash-flow quality intelligence
* Implemented KMeans-based financial clustering
* Created **5 interpretable company archetypes**
* Integrated NLP-generated company insights
* Automated **92 company tear sheets**
* Automated **10 sector reports**
* Built a **FastAPI REST API**
* Implemented **16 application endpoints**
* Built automated testing with **67 passing tests**
* Maintained a clean Git/GitHub workflow

---

# 👩‍💻 Author

**Kanishka Varshney**

B.Tech — Artificial Intelligence & Machine Learning
Noida International University

---

## 📌 Project Status

**Sprint 6 — Completed ✅**

The current implementation has completed the analytics, clustering, cash-flow intelligence, NLP integration, automated reporting, REST API, and automated testing milestones.
