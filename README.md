# Nifty 100 Analytics Dashboard

## Project Overview

The Nifty 100 Analytics Dashboard is a Python-based financial analytics platform that analyzes 92 Nifty 100 companies using financial statements, ratios, valuation metrics, and interactive dashboards.

The project provides company screening, peer comparison, trend analysis, valuation analysis, and sector-level insights using Streamlit.

---

## Features

- Company Profile Dashboard
- Financial Screener
- Peer Comparison
- Trend Analysis
- Sector Analysis
- Capital Allocation Map
- Annual Report Viewer
- Valuation Module

---

## Technology Stack

- Python
- Pandas
- SQLite
- Streamlit
- Plotly
- OpenPyXL

---

## Project Structure

```text
src/
    analytics/
    dashboard/
        pages/
        utils/

data/
output/
reports/
```

---

## How to Run

Activate virtual environment

```bash
.\venv\Scripts\activate
```

Run dashboard

```bash
streamlit run src/dashboard/app.py
```

Run valuation

```bash
python src/analytics/valuation.py
```

---

## Outputs

- valuation_summary.xlsx
- valuation_flags.csv
- screener_output.xlsx
- peer_comparison.xlsx
- radar_charts/

---

## Dashboard Pages

1. Home
2. Company Profile
3. Screener
4. Peer Comparison
5. Trends
6. Sector Analysis
7. Capital Allocation
8. Reports

---

## Dashboard Screens

### Home

Displays KPI cards, sector distribution, and top companies.

### Company Profile

Shows company overview, KPIs, Revenue, Profit, ROE, ROCE, Pros & Cons.

### Screener

Filter companies using financial ratios.

### Peer Comparison

Compare companies with peers using radar charts.

### Trends

Visualize 10-year financial trends.

### Sector Analysis

Sector comparison with bubble charts.

### Capital Allocation

Treemap visualization of capital allocation.

### Reports

View available annual reports.

## Author

Kanishka Varshney

B.Tech AIML
Noida International University