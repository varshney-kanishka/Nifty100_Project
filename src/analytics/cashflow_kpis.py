"""
Sprint 5 - Day 31
Cash Flow Intelligence Module

Generates:
- output/cashflow_intelligence.xlsx
- output/distress_alerts.csv
"""

import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

DB_PATH = BASE_DIR / "data" / "database" / "nifty100.db"
OUTPUT_DIR = BASE_DIR / "output"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# EXISTING KPI HELPERS
# ============================================================

def free_cash_flow(operating_activity, investing_activity):
    """Calculate free cash flow as CFO + CFI."""

    if pd.isna(operating_activity) or pd.isna(investing_activity):
        return None

    return operating_activity + investing_activity


def cfo_quality_score(cfo, pat):
    """Return CFO/PAT quality label."""

    if pat == 0 or pd.isna(cfo) or pd.isna(pat):
        return None

    ratio = cfo / pat

    if ratio > 1:
        return "High Quality"
    elif ratio >= 0.5:
        return "Moderate"
    else:
        return "Accrual Risk"


def capex_intensity(investing_activity, sales):
    """Calculate CapEx intensity and classification."""

    if sales == 0 or pd.isna(investing_activity) or pd.isna(sales):
        return None, None

    value = abs(investing_activity) / sales * 100

    if value < 3:
        label = "Asset Light"
    elif value <= 8:
        label = "Moderate"
    else:
        label = "Capital Intensive"

    return value, label


def fcf_conversion_rate(fcf, operating_profit):
    """Calculate FCF conversion percentage."""

    if (
        operating_profit == 0
        or pd.isna(fcf)
        or pd.isna(operating_profit)
    ):
        return None

    return fcf / operating_profit * 100


def capital_allocation_pattern(cfo, cfi, cff):
    """Classify capital allocation from CFO/CFI/CFF signs."""

    if pd.isna(cfo) or pd.isna(cfi) or pd.isna(cff):
        return None

    pattern = (
        "+" if cfo >= 0 else "-",
        "+" if cfi >= 0 else "-",
        "+" if cff >= 0 else "-",
    )

    mapping = {
        ("+", "-", "-"): "Reinvestor",
        ("+", "+", "-"): "Liquidating Assets",
        ("-", "+", "+"): "Distress Signal",
        ("-", "-", "+"): "Growth Funded by Debt",
        ("+", "+", "+"): "Cash Accumulator",
        ("-", "-", "-"): "Pre-Revenue",
        ("+", "-", "+"): "Mixed",
        ("-", "+", "-"): "Unknown",
    }

    return mapping.get(pattern, "Unknown")


# ============================================================
# ADDITIONAL HELPERS
# ============================================================

def safe_numeric(series):
    """Convert a pandas series to numeric."""

    return pd.to_numeric(series, errors="coerce")


def normalize_year(series):
    """Normalize financial year strings."""

    return (
        series.astype("string")
        .str.replace(r"\.0$", "", regex=True)
        .str.strip()
    )


def calculate_fcf_cagr(first_value, last_value, years):
    """Calculate CAGR when beginning and ending FCF are positive."""

    if (
        pd.isna(first_value)
        or pd.isna(last_value)
        or years <= 0
        or first_value <= 0
        or last_value <= 0
    ):
        return None

    try:
        return ((last_value / first_value) ** (1 / years) - 1) * 100
    except (ValueError, ZeroDivisionError):
        return None


# ============================================================
# LOAD DATABASE
# ============================================================

def load_data():
    """Load required tables from SQLite."""

    conn = sqlite3.connect(DB_PATH)

    cashflow = pd.read_sql(
        "SELECT * FROM cashflow",
        conn,
    )

    profit = pd.read_sql(
        "SELECT * FROM profitandloss",
        conn,
    )

    companies = pd.read_sql(
        "SELECT * FROM companies",
        conn,
    )

    sectors = pd.read_sql(
        "SELECT * FROM sectors",
        conn,
    )

    conn.close()

    return cashflow, profit, companies, sectors


# ============================================================
# PREPARE DATA
# ============================================================

def prepare_data(cashflow, profit, companies, sectors):
    """Clean and prepare cash-flow and P&L data."""

    for df in (cashflow, profit, companies, sectors):
        if "company_id" in df.columns:
            df["company_id"] = (
                df["company_id"]
                .astype(str)
                .str.strip()
                .str.upper()
            )

    cashflow["year"] = normalize_year(cashflow["year"])
    profit["year"] = normalize_year(profit["year"])

    cashflow["operating_activity"] = safe_numeric(
        cashflow["operating_activity"]
    )

    cashflow["investing_activity"] = safe_numeric(
        cashflow["investing_activity"]
    )

    cashflow["financing_activity"] = safe_numeric(
        cashflow["financing_activity"]
    )

    cashflow["net_cash_flow"] = safe_numeric(
        cashflow["net_cash_flow"]
    )

    profit["sales"] = safe_numeric(profit["sales"])
    profit["operating_profit"] = safe_numeric(
        profit["operating_profit"]
    )
    profit["net_profit"] = safe_numeric(profit["net_profit"])

    return cashflow, profit, companies, sectors


# ============================================================
# FIVE-YEAR METRICS
# ============================================================

def calculate_company_metrics(company_id, cashflow, profit):
    """Calculate cash-flow intelligence metrics for one company."""

    cf = cashflow[
        cashflow["company_id"] == company_id
    ].copy()

    pl = profit[
        profit["company_id"] == company_id
    ].copy()

    if cf.empty:
        return None

    cf = cf.sort_values("year")
    pl = pl.sort_values("year")

    # --------------------------------------------------------
    # CFO QUALITY
    # --------------------------------------------------------

    merged = cf.merge(
        pl[
            [
                "company_id",
                "year",
                "net_profit",
                "sales",
                "operating_profit",
            ]
        ],
        on=["company_id", "year"],
        how="left",
    )

    merged["cfo_pat_ratio"] = np.where(
        merged["net_profit"].notna()
        & (merged["net_profit"] != 0),
        merged["operating_activity"]
        / merged["net_profit"],
        np.nan,
    )

    recent_5 = merged.tail(5)

    cfo_quality_score_value = recent_5[
        "cfo_pat_ratio"
    ].mean()

    if pd.isna(cfo_quality_score_value):
        cfo_quality_label = None
    elif cfo_quality_score_value > 1:
        cfo_quality_label = "High Quality"
    elif cfo_quality_score_value >= 0.5:
        cfo_quality_label = "Moderate"
    else:
        cfo_quality_label = "Accrual Risk"

    # --------------------------------------------------------
    # LATEST YEAR
    # --------------------------------------------------------

    latest = merged.iloc[-1]

    cfo = latest["operating_activity"]
    cfi = latest["investing_activity"]
    cff = latest["financing_activity"]

    sales = latest["sales"]
    operating_profit = latest["operating_profit"]

    # --------------------------------------------------------
    # CAPEX INTENSITY
    # --------------------------------------------------------

    capex_value, capex_label = capex_intensity(
        cfi,
        sales,
    )

    # --------------------------------------------------------
    # FCF
    # --------------------------------------------------------

    merged["fcf"] = (
        merged["operating_activity"]
        + merged["investing_activity"]
    )

    recent_fcf = merged.tail(6)

    fcf_cagr = None

    if len(recent_fcf) >= 2:
        first_fcf = recent_fcf.iloc[0]["fcf"]
        last_fcf = recent_fcf.iloc[-1]["fcf"]

        fcf_cagr = calculate_fcf_cagr(
            first_fcf,
            last_fcf,
            len(recent_fcf) - 1,
        )

    # --------------------------------------------------------
    # FCF CONVERSION
    # --------------------------------------------------------

    fcf_latest = latest["operating_activity"] + latest[
        "investing_activity"
    ]

    fcf_conversion = fcf_conversion_rate(
        fcf_latest,
        operating_profit,
    )

    # --------------------------------------------------------
    # DISTRESS FLAG
    # --------------------------------------------------------

    distress_flag = bool(
        pd.notna(cfo)
        and pd.notna(cff)
        and cfo < 0
        and cff > 0
    )

    # --------------------------------------------------------
    # CAPITAL ALLOCATION
    # --------------------------------------------------------

    allocation_label = capital_allocation_pattern(
        cfo,
        cfi,
        cff,
    )

    return {
        "cfo_quality_score": cfo_quality_score_value,
        "cfo_quality_label": cfo_quality_label,
        "capex_intensity_pct": capex_value,
        "capex_label": capex_label,
        "fcf_cagr_5yr": fcf_cagr,
        "fcf_conversion_pct": fcf_conversion,
        "distress_flag": distress_flag,
        "capital_allocation_label": allocation_label,
        "latest_cfo": cfo,
        "latest_cff": cff,
        "latest_net_profit": latest["net_profit"],
    }


# ============================================================
# DELEVERAGING
# ============================================================

def calculate_deleveraging(company_id, cashflow, balance=None):
    """Detect active debt repayment from financing cash flow."""

    if balance is None:
        return False

    cf = cashflow[
        cashflow["company_id"] == company_id
    ].sort_values("year")

    bs = balance[
        balance["company_id"] == company_id
    ].copy()

    if cf.empty or bs.empty:
        return False

    bs["year"] = normalize_year(bs["year"])
    bs["borrowings"] = safe_numeric(bs["borrowings"])

    merged = cf.merge(
        bs[["company_id", "year", "borrowings"]],
        on=["company_id", "year"],
        how="left",
    )

    if len(merged) < 2:
        return False

    latest = merged.iloc[-1]
    previous = merged.iloc[-2]

    return bool(
        pd.notna(latest["financing_activity"])
        and latest["financing_activity"] < 0
        and pd.notna(latest["borrowings"])
        and pd.notna(previous["borrowings"])
        and latest["borrowings"] < previous["borrowings"]
    )


# ============================================================
# MAIN PIPELINE
# ============================================================

def run_cashflow_intelligence():
    """Generate the Sprint 5 cash-flow intelligence outputs."""

    print("=" * 70)
    print("DAY 31 - CASH FLOW INTELLIGENCE")
    print("=" * 70)

    cashflow, profit, companies, sectors = load_data()

    # Need balance sheet for deleveraging.
    conn = sqlite3.connect(DB_PATH)

    balance = pd.read_sql(
        "SELECT * FROM balancesheet",
        conn,
    )

    conn.close()

    cashflow, profit, companies, sectors = prepare_data(
        cashflow,
        profit,
        companies,
        sectors,
    )

    balance["company_id"] = (
        balance["company_id"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    print("\nTables Loaded")
    print("Cash Flow :", len(cashflow))
    print("Profit    :", len(profit))
    print("Balance   :", len(balance))
    print("Companies :", len(companies))
    print("Sectors   :", len(sectors))

    results = []
    distress_rows = []

    # --------------------------------------------------------
    # PROCESS ALL COMPANIES
    # --------------------------------------------------------

    for company_id in companies["company_id"].unique():

        metrics = calculate_company_metrics(
            company_id,
            cashflow,
            profit,
        )

        if metrics is None:
            continue

        sector_row = sectors[
            sectors["company_id"] == company_id
        ]

        sector = (
            sector_row.iloc[0]["broad_sector"]
            if not sector_row.empty
            else None
        )

        metrics["company_id"] = company_id
        metrics["sector"] = sector

        metrics["deleveraging_flag"] = calculate_deleveraging(
            company_id,
            cashflow,
            balance,
        )

        results.append(metrics)

        if metrics["distress_flag"]:
            distress_rows.append(
                {
                    "company_id": company_id,
                    "sector": sector,
                    "CFO": metrics["latest_cfo"],
                    "CFF": metrics["latest_cff"],
                    "latest_net_profit": metrics[
                        "latest_net_profit"
                    ],
                }
            )

    result = pd.DataFrame(results)

    # --------------------------------------------------------
    # COLUMN ORDER
    # --------------------------------------------------------

    columns = [
        "company_id",
        "sector",
        "cfo_quality_score",
        "cfo_quality_label",
        "capex_intensity_pct",
        "capex_label",
        "fcf_cagr_5yr",
        "fcf_conversion_pct",
        "distress_flag",
        "deleveraging_flag",
        "capital_allocation_label",
    ]

    result = result[
        [c for c in columns if c in result.columns]
    ]

    # --------------------------------------------------------
    # SAVE EXCEL
    # --------------------------------------------------------

    excel_path = OUTPUT_DIR / "cashflow_intelligence.xlsx"

    result.to_excel(
        excel_path,
        index=False,
    )

    # --------------------------------------------------------
    # SAVE DISTRESS ALERTS
    # --------------------------------------------------------

    distress_path = OUTPUT_DIR / "distress_alerts.csv"

    pd.DataFrame(distress_rows).to_csv(
        distress_path,
        index=False,
    )

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("DAY 31 COMPLETE")
    print("=" * 70)

    print("Companies processed :", len(result))
    print("Distress alerts     :", len(distress_rows))

    print("\nCFO Quality:")
    print(
        result["cfo_quality_label"]
        .value_counts(dropna=False)
    )

    print("\nCapEx:")
    print(
        result["capex_label"]
        .value_counts(dropna=False)
    )

    print("\nDistress flags:")
    print(
        result["distress_flag"]
        .value_counts(dropna=False)
    )

    print("\nDeleveraging flags:")
    print(
        result["deleveraging_flag"]
        .value_counts(dropna=False)
    )

    print("\nCapital Allocation:")
    print(
        result["capital_allocation_label"]
        .value_counts(dropna=False)
    )

    print("\nCreated:")
    print(excel_path)
    print(distress_path)

    return result


if __name__ == "__main__":
    run_cashflow_intelligence()