
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

print("=" * 70)
print("DAY 30 - AUTO PROS & CONS GENERATOR")
print("=" * 70)

# =========================================================
# PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parents[2]

DB = BASE_DIR / "data" / "database" / "nifty100.db"
OUTPUT = BASE_DIR / "output"

OUTPUT.mkdir(exist_ok=True)

# =========================================================
# DATABASE
# =========================================================

conn = sqlite3.connect(DB)

companies = pd.read_sql(
    "SELECT * FROM companies",
    conn
)

profit = pd.read_sql(
    "SELECT * FROM profitandloss",
    conn
)

balance = pd.read_sql(
    "SELECT * FROM balancesheet",
    conn
)

cashflow = pd.read_sql(
    "SELECT * FROM cashflow",
    conn
)

analysis = pd.read_sql(
    "SELECT * FROM analysis",
    conn
)

conn.close()

print("\nTables Loaded")
print("Companies :", len(companies))
print("Profit    :", len(profit))
print("Balance   :", len(balance))
print("Cash Flow :", len(cashflow))
print("Analysis  :", len(analysis))


# =========================================================
# HELPER - CLEAN YEAR
# =========================================================

def extract_year(value):
    """
    Converts values such as:
        Dec 2012
        Mar 2024
        2024
        TTM

    into a numeric year.
    """

    match = pd.Series([str(value)]).str.extract(
        r"(\d{4})"
    )[0].iloc[0]

    if pd.isna(match):
        return np.nan

    return int(match)


# =========================================================
# PREPARE FINANCIAL TABLES
# =========================================================

profit["year_num"] = profit["year"].apply(extract_year)
balance["year_num"] = balance["year"].apply(extract_year)
cashflow["year_num"] = cashflow["year"].apply(extract_year)


# =========================================================
# LATEST PROFIT
# =========================================================

latest_profit = (
    profit
    .dropna(subset=["year_num"])
    .sort_values(["company_id", "year_num"])
    .groupby("company_id")
    .tail(1)
    .copy()
)

print("\nLatest Records")
print("Profit    :", len(latest_profit))


# =========================================================
# LATEST BALANCE
# =========================================================

latest_balance = (
    balance
    .dropna(subset=["year_num"])
    .sort_values(["company_id", "year_num"])
    .groupby("company_id")
    .tail(1)
    .copy()
)

print("Balance   :", len(latest_balance))


# =========================================================
# LATEST CASH FLOW
# =========================================================

latest_cashflow = (
    cashflow
    .dropna(subset=["year_num"])
    .sort_values(["company_id", "year_num"])
    .groupby("company_id")
    .tail(1)
    .copy()
)

print("Cash Flow :", len(latest_cashflow))


# =========================================================
# MERGE ALL LATEST DATA
# =========================================================

latest = latest_profit.merge(
    latest_balance[
        [
            "company_id",
            "equity_capital",
            "reserves",
            "borrowings",
            "other_liabilities",
            "total_liabilities",
            "total_assets",
        ]
    ],
    on="company_id",
    how="left"
)

latest = latest.merge(
    latest_cashflow[
        [
            "company_id",
            "operating_activity",
            "investing_activity",
            "financing_activity",
            "net_cash_flow",
        ]
    ],
    on="company_id",
    how="left"
)


# =========================================================
# COMPANY INFORMATION
# =========================================================

latest = latest.merge(
    companies[
        [
            "id",
            "company_name",
            "roce_percentage",
            "roe_percentage",
        ]
    ],
    left_on="company_id",
    right_on="id",
    how="left"
)

latest.drop(
    columns=["id"],
    inplace=True,
    errors="ignore"
)


# =========================================================
# NUMERIC CLEANING
# =========================================================

numeric_columns = [
    "sales",
    "operating_profit",
    "opm_percentage",
    "net_profit",
    "eps",
    "dividend_payout",
    "interest",
    "equity_capital",
    "reserves",
    "borrowings",
    "other_liabilities",
    "total_liabilities",
    "total_assets",
    "operating_activity",
    "investing_activity",
    "financing_activity",
    "net_cash_flow",
    "roce_percentage",
    "roe_percentage",
]

for col in numeric_columns:

    if col in latest.columns:

        latest[col] = pd.to_numeric(
            latest[col],
            errors="coerce"
        )


# =========================================================
# DERIVED METRICS
# =========================================================

latest["equity"] = (
    latest["equity_capital"].fillna(0)
    + latest["reserves"].fillna(0)
)

latest["debt_to_equity"] = np.where(
    latest["equity"] != 0,
    latest["borrowings"] / latest["equity"],
    np.nan
)

latest["interest_coverage"] = np.where(
    latest["interest"].abs() > 0,
    latest["operating_profit"]
    / latest["interest"].abs(),
    np.nan
)

latest["free_cash_flow"] = (
    latest["operating_activity"].fillna(0)
    + latest["investing_activity"].fillna(0)
)

latest["fcf_positive"] = (
    latest["free_cash_flow"] > 0
)

latest["debt_to_assets"] = np.where(
    latest["total_assets"] != 0,
    latest["borrowings"]
    / latest["total_assets"],
    np.nan
)


# =========================================================
# DISPLAY
# =========================================================

print("\nMerged Latest Dataset :", len(latest))

print("\nLatest Dataset Columns")
print(latest.columns.tolist())


# =========================================================
# HISTORICAL DATA FOR TREND RULES
# =========================================================

profit_history = profit.copy()

profit_history["sales"] = pd.to_numeric(
    profit_history["sales"],
    errors="coerce"
)

profit_history["net_profit"] = pd.to_numeric(
    profit_history["net_profit"],
    errors="coerce"
)

profit_history["eps"] = pd.to_numeric(
    profit_history["eps"],
    errors="coerce"
)

profit_history["opm_percentage"] = pd.to_numeric(
    profit_history["opm_percentage"],
    errors="coerce"
)


# =========================================================
# HELPER - CAGR
# =========================================================

def cagr(first, last, years):

    if pd.isna(first) or pd.isna(last):
        return np.nan

    if first <= 0 or last <= 0 or years <= 0:
        return np.nan

    return (
        ((last / first) ** (1 / years) - 1)
        * 100
    )


# =========================================================
# COMPANY LIST
# =========================================================

all_companies = (
    companies["id"]
    .astype(str)
    .str.strip()
    .unique()
)

print("\nCompanies to process :", len(all_companies))


# =========================================================
# GENERATE PROS & CONS
# =========================================================

records = []


for company in all_companies:

    # -----------------------------------------------------
    # FIND LATEST COMPANY DATA
    # -----------------------------------------------------

    row_match = latest[
        latest["company_id"]
        .astype(str)
        .str.strip()
        == company
    ]

    if row_match.empty:
        print(
            f"WARNING: No latest financial data for {company}"
        )
        continue

    row = row_match.iloc[0]

    company_name = row.get(
        "company_name",
        company
    )


    # =====================================================
    # CURRENT METRICS
    # =====================================================

    roe = row.get(
        "roe_percentage",
        np.nan
    )

    roce = row.get(
        "roce_percentage",
        np.nan
    )

    opm = row.get(
        "opm_percentage",
        np.nan
    )

    eps = row.get(
        "eps",
        np.nan
    )

    net_profit = row.get(
        "net_profit",
        np.nan
    )

    payout = row.get(
        "dividend_payout",
        np.nan
    )

    de = row.get(
        "debt_to_equity",
        np.nan
    )

    icr = row.get(
        "interest_coverage",
        np.nan
    )

    cfo = row.get(
        "operating_activity",
        np.nan
    )

    net_cf = row.get(
        "net_cash_flow",
        np.nan
    )

    free_cash_flow = row.get(
        "free_cash_flow",
        np.nan
    )

    total_assets = row.get(
        "total_assets",
        np.nan
    )

    borrowings = row.get(
        "borrowings",
        np.nan
    )


    # =====================================================
    # PRO RULE 1 - ROE > 20%
    # =====================================================

    if pd.notna(roe) and roe > 20:

        records.append({
            "company_id": company,
            "type": "pro",
            "rule_id": "P1",
            "text":
                "Consistently high return on equity above 20% demonstrates exceptional capital efficiency.",
            "confidence_pct": 90
        })


    # =====================================================
    # PRO RULE 2 - POSITIVE FCF
    # =====================================================

    if pd.notna(free_cash_flow) and free_cash_flow > 0:

        records.append({
            "company_id": company,
            "type": "pro",
            "rule_id": "P2",
            "text":
                "Positive free cash flow indicates healthy business fundamentals.",
            "confidence_pct": 80
        })


    # =====================================================
    # PRO RULE 3 - DEBT FREE
    # =====================================================

    if pd.notna(de) and de == 0:

        records.append({
            "company_id": company,
            "type": "pro",
            "rule_id": "P3",
            "text":
                "Debt-free balance sheet provides financial flexibility and eliminates interest burden.",
            "confidence_pct": 95
        })


    # =====================================================
    # PRO RULE 4 - OPM > 25%
    # =====================================================

    if pd.notna(opm) and opm > 25:

        records.append({
            "company_id": company,
            "type": "pro",
            "rule_id": "P4",
            "text":
                "Operating profit margin above 25% indicates strong pricing power and cost discipline.",
            "confidence_pct": 85
        })


    # =====================================================
    # PRO RULE 5 - HIGH INTEREST COVERAGE
    # =====================================================

    if pd.notna(icr) and icr > 10:

        records.append({
            "company_id": company,
            "type": "pro",
            "rule_id": "P5",
            "text":
                "Very high interest coverage ratio reflects negligible financial stress from debt servicing.",
            "confidence_pct": 88
        })


    # =====================================================
    # PRO RULE 6 - POSITIVE EPS
    # =====================================================

    if pd.notna(eps) and eps > 0:

        records.append({
            "company_id": company,
            "type": "pro",
            "rule_id": "P6",
            "text":
                "Positive earnings per share indicate profitable operations.",
            "confidence_pct": 75
        })


    # =====================================================
    # HISTORICAL DATA
    # =====================================================

    hist = (
        profit_history[
            profit_history["company_id"]
            .astype(str)
            .str.strip()
            == company
        ]
        .dropna(subset=["year_num"])
        .sort_values("year_num")
    )


    # =====================================================
    # PRO RULE 7 - REVENUE CAGR > 15%
    # =====================================================

    if len(hist) >= 5:

        first_sales = hist.iloc[-5]["sales"]
        last_sales = hist.iloc[-1]["sales"]

        revenue_cagr = cagr(
            first_sales,
            last_sales,
            4
        )

        if (
            pd.notna(revenue_cagr)
            and revenue_cagr > 15
        ):

            records.append({
                "company_id": company,
                "type": "pro",
                "rule_id": "P7",
                "text":
                    "Revenue growing at above 15% CAGR over 5 years reflects strong business momentum.",
                "confidence_pct": 90
            })


    # =====================================================
    # PRO RULE 8 - PAT CAGR > 20%
    # =====================================================

        first_profit = hist.iloc[-5]["net_profit"]
        last_profit = hist.iloc[-1]["net_profit"]

        pat_cagr = cagr(
            first_profit,
            last_profit,
            4
        )

        if (
            pd.notna(pat_cagr)
            and pat_cagr > 20
        ):

            records.append({
                "company_id": company,
                "type": "pro",
                "rule_id": "P8",
                "text":
                    "Net profit compounding at above 20% over 5 years creates significant shareholder value.",
                "confidence_pct": 90
            })


    # =====================================================
    # PRO RULE 9 - EPS + NET PROFIT POSITIVE
    # =====================================================

    if (
        pd.notna(eps)
        and eps > 0
        and pd.notna(net_profit)
        and net_profit > 0
    ):

        records.append({
            "company_id": company,
            "type": "pro",
            "rule_id": "P9",
            "text":
                "Positive earnings and net profit indicate a profitable operating base.",
            "confidence_pct": 78
        })


    # =====================================================
    # PRO RULE 10 - POSITIVE ASSET BASE
    # =====================================================

    if (
        pd.notna(total_assets)
        and total_assets > 0
    ):

        records.append({
            "company_id": company,
            "type": "pro",
            "rule_id": "P10",
            "text":
                "A positive asset base provides capacity to support future business growth.",
            "confidence_pct": 70
        })


    # =====================================================
    # PRO RULE 11 - DIVIDEND PAYOUT
    # =====================================================

    if (
        pd.notna(payout)
        and 0 < payout <= 100
    ):

        records.append({
            "company_id": company,
            "type": "pro",
            "rule_id": "P11",
            "text":
                "A sustainable dividend payout reflects shareholder distribution supported by earnings.",
            "confidence_pct": 70
        })


    # =====================================================
    # PRO RULE 12 - POSITIVE CFO
    # =====================================================

    if pd.notna(cfo) and cfo > 0:

        records.append({
            "company_id": company,
            "type": "pro",
            "rule_id": "P12",
            "text":
                "Positive operating cash flow demonstrates the ability of the business to generate cash from operations.",
            "confidence_pct": 85
        })


    # =====================================================
    # CONS
    # =====================================================

    # -----------------------------------------------------
    # CON 1 - HIGH D/E
    # -----------------------------------------------------

    if pd.notna(de) and de > 2:

        records.append({
            "company_id": company,
            "type": "con",
            "rule_id": "C1",
            "text":
                f"Debt-to-equity ratio of {de:.2f} is elevated and warrants monitoring.",
            "confidence_pct": 90
        })


    # -----------------------------------------------------
    # CON 2 - NEGATIVE FCF
    # -----------------------------------------------------

    if (
        pd.notna(free_cash_flow)
        and free_cash_flow < 0
    ):

        records.append({
            "company_id": company,
            "type": "con",
            "rule_id": "C2",
            "text":
                "Negative free cash flow raises concern about cash generation quality.",
            "confidence_pct": 85
        })


    # -----------------------------------------------------
    # CON 3 - LOW ICR
    # -----------------------------------------------------

    if pd.notna(icr) and icr < 1.5:

        records.append({
            "company_id": company,
            "type": "con",
            "rule_id": "C3",
            "text":
                "Interest coverage ratio below 1.5x indicates risk in meeting debt obligations.",
            "confidence_pct": 90
        })


    # -----------------------------------------------------
    # CON 4 - NEGATIVE PROFIT
    # -----------------------------------------------------

    if pd.notna(net_profit) and net_profit < 0:

        records.append({
            "company_id": company,
            "type": "con",
            "rule_id": "C4",
            "text":
                "Company reported a net loss in the most recent financial year.",
            "confidence_pct": 95
        })


    # -----------------------------------------------------
    # CON 5 - LOW ROE
    # -----------------------------------------------------

    if pd.notna(roe) and roe < 10:

        records.append({
            "company_id": company,
            "type": "con",
            "rule_id": "C5",
            "text":
                "Return on equity below 10% suggests weak capital efficiency.",
            "confidence_pct": 80
        })


    # -----------------------------------------------------
    # CON 6 - LOW OPM
    # -----------------------------------------------------

    if pd.notna(opm) and opm < 10:

        records.append({
            "company_id": company,
            "type": "con",
            "rule_id": "C6",
            "text":
                "Low operating margin indicates weak profitability.",
            "confidence_pct": 78
        })


    # -----------------------------------------------------
    # CON 7 - NEGATIVE EPS
    # -----------------------------------------------------

    if pd.notna(eps) and eps < 0:

        records.append({
            "company_id": company,
            "type": "con",
            "rule_id": "C7",
            "text":
                "Negative earnings per share indicate losses.",
            "confidence_pct": 95
        })


    # -----------------------------------------------------
    # CON 8 - HIGH BORROWINGS
    # -----------------------------------------------------

    if (
        pd.notna(borrowings)
        and pd.notna(total_assets)
        and total_assets > 0
        and borrowings / total_assets > 0.5
    ):

        records.append({
            "company_id": company,
            "type": "con",
            "rule_id": "C8",
            "text":
                "Borrowings represent a high proportion of total assets and increase financial leverage risk.",
            "confidence_pct": 82
        })


    # -----------------------------------------------------
    # CON 9 - NEGATIVE CFO
    # -----------------------------------------------------

    if pd.notna(cfo) and cfo < 0:

        records.append({
            "company_id": company,
            "type": "con",
            "rule_id": "C9",
            "text":
                "Negative operating cash flow indicates pressure on cash generation from core operations.",
            "confidence_pct": 88
        })


    # -----------------------------------------------------
    # CON 10 - HIGH DIVIDEND PAYOUT
    # -----------------------------------------------------

    if pd.notna(payout) and payout > 100:

        records.append({
            "company_id": company,
            "type": "con",
            "rule_id": "C10",
            "text":
                "Dividend payout ratio above 100% may indicate distributions exceeding reported earnings.",
            "confidence_pct": 90
        })


    # -----------------------------------------------------
    # CON 11 - LOW ROCE
    # -----------------------------------------------------

    if pd.notna(roce) and roce < 10:

        records.append({
            "company_id": company,
            "type": "con",
            "rule_id": "C11",
            "text":
                "Return on capital employed below 10% suggests the business is generating limited returns on invested capital.",
            "confidence_pct": 85
        })


    # -----------------------------------------------------
    # CON 12 - NEGATIVE NET CASH FLOW
    # -----------------------------------------------------

    if pd.notna(net_cf) and net_cf < 0:

        records.append({
            "company_id": company,
            "type": "con",
            "rule_id": "C12",
            "text":
                "Negative net cash flow indicates that total cash outflows exceeded inflows during the latest period.",
            "confidence_pct": 75
        })


# =========================================================
# CREATE DATAFRAME
# =========================================================

pros_cons = pd.DataFrame(records)


# =========================================================
# CONFIDENCE FILTER
# =========================================================

if not pros_cons.empty:

    pros_cons = pros_cons[
        pros_cons["confidence_pct"] > 60
    ].copy()


# =========================================================
# GUARANTEE 1 PRO + 1 CON FOR EVERY COMPANY
#
# IMPORTANT:
# Fallback logic must run INSIDE the company loop.
# =========================================================

for company in all_companies:

    # -----------------------------------------------------
    # Current company records
    # -----------------------------------------------------

    company_records = pros_cons[
        pros_cons["company_id"] == company
    ]

    has_pro = (
        (company_records["type"] == "pro").any()
    )

    has_con = (
        (company_records["type"] == "con").any()
    )


    # -----------------------------------------------------
    # GUARANTEE PRO
    # -----------------------------------------------------

    if not has_pro:

        row_match = latest[
            latest["company_id"]
            .astype(str)
            .str.strip()
            == company
        ]

        if not row_match.empty:

            row = row_match.iloc[0]

            roe = row.get(
                "roe_percentage",
                np.nan
            )

            opm = row.get(
                "opm_percentage",
                np.nan
            )

            eps = row.get(
                "eps",
                np.nan
            )

            cfo = row.get(
                "operating_activity",
                np.nan
            )

            total_assets = row.get(
                "total_assets",
                np.nan
            )

            # Neutral but factual positive fallback
            if (
                pd.notna(eps)
                and eps > 0
            ):

                fallback_pro = {
                    "company_id": company,
                    "type": "pro",
                    "rule_id": "P_FALLBACK_EPS",
                    "text":
                        "Positive earnings per share provide evidence of profitable operations.",
                    "confidence_pct": 70
                }

            elif (
                pd.notna(cfo)
                and cfo > 0
            ):

                fallback_pro = {
                    "company_id": company,
                    "type": "pro",
                    "rule_id": "P_FALLBACK_CFO",
                    "text":
                        "Positive operating cash flow indicates the business is generating cash from core operations.",
                    "confidence_pct": 70
                }

            elif (
                pd.notna(opm)
                and opm > 0
            ):

                fallback_pro = {
                    "company_id": company,
                    "type": "pro",
                    "rule_id": "P_FALLBACK_OPM",
                    "text":
                        f"Positive operating profit margin of {opm:.2f}% indicates the business generates operating profit.",
                    "confidence_pct": 68
                }

            elif (
                pd.notna(total_assets)
                and total_assets > 0
            ):

                fallback_pro = {
                    "company_id": company,
                    "type": "pro",
                    "rule_id": "P_FALLBACK_ASSETS",
                    "text":
                        "The company maintains a positive asset base supporting its operating activities.",
                    "confidence_pct": 65
                }

            else:

                fallback_pro = {
                    "company_id": company,
                    "type": "pro",
                    "rule_id": "P_MONITORING",
                    "text":
                        "The company has identifiable operating and financial indicators that should be monitored for future improvement.",
                    "confidence_pct": 65
                }

            pros_cons = pd.concat(
                [
                    pros_cons,
                    pd.DataFrame([fallback_pro])
                ],
                ignore_index=True
            )


    # -----------------------------------------------------
    # GUARANTEE CON
    # -----------------------------------------------------

    if not has_con:

        row_match = latest[
            latest["company_id"]
            .astype(str)
            .str.strip()
            == company
        ]

        if not row_match.empty:

            row = row_match.iloc[0]

            roe = row.get(
                "roe_percentage",
                np.nan
            )

            roce = row.get(
                "roce_percentage",
                np.nan
            )

            opm = row.get(
                "opm_percentage",
                np.nan
            )

            de = row.get(
                "debt_to_equity",
                np.nan
            )

            debt_assets = row.get(
                "debt_to_assets",
                np.nan
            )

            icr = row.get(
                "interest_coverage",
                np.nan
            )

            payout = row.get(
                "dividend_payout",
                np.nan
            )

            net_cf = row.get(
                "net_cash_flow",
                np.nan
            )

            fallback_con = None

            # -------------------------------------------------
            # FALLBACK 1 - MODERATE ROCE
            # -------------------------------------------------

            if (
                pd.notna(roce)
                and roce < 15
            ):

                fallback_con = {
                    "company_id": company,
                    "type": "con",
                    "rule_id": "C_FALLBACK_ROCE",
                    "text":
                        f"Return on capital employed of {roce:.2f}% is below 15%, indicating moderate capital efficiency.",
                    "confidence_pct": 72
                }


            # -------------------------------------------------
            # FALLBACK 2 - MODERATE ROE
            # -------------------------------------------------

            elif (
                pd.notna(roe)
                and roe < 15
            ):

                fallback_con = {
                    "company_id": company,
                    "type": "con",
                    "rule_id": "C_FALLBACK_ROE",
                    "text":
                        f"Return on equity of {roe:.2f}% is below 15%, indicating moderate shareholder return efficiency.",
                    "confidence_pct": 72
                }


            # -------------------------------------------------
            # FALLBACK 3 - MODERATE OPM
            # -------------------------------------------------

            elif (
                pd.notna(opm)
                and opm < 15
            ):

                fallback_con = {
                    "company_id": company,
                    "type": "con",
                    "rule_id": "C_FALLBACK_OPM",
                    "text":
                        f"Operating profit margin of {opm:.2f}% is below 15%, indicating moderate operating profitability.",
                    "confidence_pct": 72
                }


            # -------------------------------------------------
            # FALLBACK 4 - MODERATE DEBT
            # -------------------------------------------------

            elif (
                pd.notna(de)
                and de > 1
            ):

                fallback_con = {
                    "company_id": company,
                    "type": "con",
                    "rule_id": "C_FALLBACK_DE",
                    "text":
                        f"Debt-to-equity ratio of {de:.2f} indicates moderate financial leverage.",
                    "confidence_pct": 72
                }


            # -------------------------------------------------
            # FALLBACK 5 - DEBT TO ASSETS
            # -------------------------------------------------

            elif (
                pd.notna(debt_assets)
                and debt_assets > 0.30
            ):

                debt_assets_pct = (
                    debt_assets * 100
                )

                fallback_con = {
                    "company_id": company,
                    "type": "con",
                    "rule_id": "C_FALLBACK_DTA",
                    "text":
                        f"Borrowings account for approximately {debt_assets_pct:.1f}% of total assets, indicating elevated leverage exposure.",
                    "confidence_pct": 72
                }


            # -------------------------------------------------
            # FALLBACK 6 - INTEREST COVERAGE
            # -------------------------------------------------

            elif (
                pd.notna(icr)
                and icr < 3
            ):

                fallback_con = {
                    "company_id": company,
                    "type": "con",
                    "rule_id": "C_FALLBACK_ICR",
                    "text":
                        f"Interest coverage of {icr:.2f}x is below 3x and should be monitored for debt-servicing risk.",
                    "confidence_pct": 75
                }


            # -------------------------------------------------
            # FALLBACK 7 - HIGH PAYOUT
            # -------------------------------------------------

            elif (
                pd.notna(payout)
                and payout > 80
            ):

                fallback_con = {
                    "company_id": company,
                    "type": "con",
                    "rule_id": "C_FALLBACK_PAYOUT",
                    "text":
                        f"Dividend payout of {payout:.1f}% leaves a relatively smaller portion of earnings available for reinvestment.",
                    "confidence_pct": 70
                }


            # -------------------------------------------------
            # FALLBACK 8 - NEGATIVE NET CASH FLOW
            # -------------------------------------------------

            elif (
                pd.notna(net_cf)
                and net_cf < 0
            ):

                fallback_con = {
                    "company_id": company,
                    "type": "con",
                    "rule_id": "C_FALLBACK_NETCF",
                    "text":
                        "Negative net cash flow indicates that total cash outflows exceeded inflows during the latest period.",
                    "confidence_pct": 75
                }


            # -------------------------------------------------
            # FINAL NEUTRAL FALLBACK
            # -------------------------------------------------

            else:

                fallback_con = {
                    "company_id": company,
                    "type": "con",
                    "rule_id": "C_MONITORING",
                    "text":
                        "No major negative financial threshold was triggered; profitability, leverage and cash-flow indicators should continue to be monitored.",
                    "confidence_pct": 65
                }


            pros_cons = pd.concat(
                [
                    pros_cons,
                    pd.DataFrame([fallback_con])
                ],
                ignore_index=True
            )


# =========================================================
# FINAL COLUMN ORDER
# =========================================================

pros_cons = pros_cons[
    [
        "company_id",
        "type",
        "rule_id",
        "text",
        "confidence_pct"
    ]
]


# =========================================================
# REMOVE DUPLICATES
# =========================================================

pros_cons = pros_cons.drop_duplicates(
    subset=[
        "company_id",
        "type",
        "rule_id"
    ]
).reset_index(drop=True)


# =========================================================
# FINAL VALIDATION
# =========================================================

pro_count = (
    pros_cons[
        pros_cons["type"] == "pro"
    ]
    .groupby("company_id")
    .size()
)

con_count = (
    pros_cons[
        pros_cons["type"] == "con"
    ]
    .groupby("company_id")
    .size()
)

missing_pro = [
    company
    for company in all_companies
    if pro_count.get(company, 0) == 0
]

missing_con = [
    company
    for company in all_companies
    if con_count.get(company, 0) == 0
]


# =========================================================
# SAVE
# =========================================================

output_file = OUTPUT / "pros_cons_generated.csv"

pros_cons.to_csv(
    output_file,
    index=False
)


# =========================================================
# VALIDATION REPORT
# =========================================================

print("\n" + "=" * 70)
print("DAY 30 VALIDATION")
print("=" * 70)

print(
    "Total Companies :",
    len(all_companies)
)

print(
    "Total Records   :",
    len(pros_cons)
)

print(
    "Total Pros      :",
    (pros_cons["type"] == "pro").sum()
)

print(
    "Total Cons      :",
    (pros_cons["type"] == "con").sum()
)

print(
    "Companies with Pro :",
    pros_cons.loc[
        pros_cons["type"] == "pro",
        "company_id"
    ].nunique()
)

print(
    "Companies with Con :",
    pros_cons.loc[
        pros_cons["type"] == "con",
        "company_id"
    ].nunique()
)

print(
    "Missing Pro :",
    missing_pro
)

print(
    "Missing Con :",
    missing_con
)


# =========================================================
# FALLBACK SUMMARY
# =========================================================

fallback_rows = pros_cons[
    pros_cons["rule_id"].str.startswith(
        "C_FALLBACK",
        na=False
    )
]

monitoring_rows = pros_cons[
    pros_cons["rule_id"] == "C_MONITORING"
]

print("\n" + "=" * 70)
print("FALLBACK SUMMARY")
print("=" * 70)

print(
    "Fallback Cons :",
    len(fallback_rows)
)

print(
    "Neutral Monitoring Cons :",
    len(monitoring_rows)
)


# =========================================================
# RULE USAGE
# =========================================================

print("\n" + "=" * 70)
print("RULE USAGE")
print("=" * 70)

rule_usage = (
    pros_cons
    .groupby(["type", "rule_id"])
    .size()
    .sort_values(ascending=False)
)

print(rule_usage)


# =========================================================
# COMPANY SUMMARY
# =========================================================

print("\n" + "=" * 70)
print("PROS/CONS BY COMPANY")
print("=" * 70)

company_summary = pd.crosstab(
    pros_cons["company_id"],
    pros_cons["type"]
)

if "pro" not in company_summary.columns:
    company_summary["pro"] = 0

if "con" not in company_summary.columns:
    company_summary["con"] = 0

company_summary = company_summary[
    ["con", "pro"]
].sort_index()

print(company_summary)


# =========================================================
# CONFIDENCE SUMMARY
# =========================================================

print("\n" + "=" * 70)
print("AVERAGE CONFIDENCE")
print("=" * 70)

confidence_summary = (
    pros_cons
    .groupby("type")["confidence_pct"]
    .agg(
        ["count", "mean", "min", "max"]
    )
)

print(confidence_summary)


# =========================================================
# OUTPUT
# =========================================================

print("\nOutput:")
print(output_file)

print("\n" + "=" * 70)
print("DAY 30 COMPLETED")
print("=" * 70)

