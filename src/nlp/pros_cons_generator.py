import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd


print("=" * 70)
print("DAY 30 - AUTO PROS & CONS GENERATOR")
print("=" * 70)

# ---------------------------------------------------------
# PATHS
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]

DB = BASE_DIR / "data" / "database" / "nifty100.db"
OUTPUT = BASE_DIR / "output"

OUTPUT.mkdir(exist_ok=True)

# ---------------------------------------------------------
# DATABASE
# ---------------------------------------------------------

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


# ---------------------------------------------------------
# HELPER - CLEAN YEAR
# ---------------------------------------------------------

def extract_year(value):
    """
    Converts values such as:
    Dec 2012
    Mar 2024
    2024
    TTM

    into a numeric year.
    """

    match = pd.Series([str(value)]).str.extract(r"(\d{4})")[0].iloc[0]

    if pd.isna(match):
        return np.nan

    return int(match)


# ---------------------------------------------------------
# PREPARE FINANCIAL TABLES
# ---------------------------------------------------------

profit["year_num"] = profit["year"].apply(extract_year)
balance["year_num"] = balance["year"].apply(extract_year)
cashflow["year_num"] = cashflow["year"].apply(extract_year)


# ---------------------------------------------------------
# LATEST PROFIT
# ---------------------------------------------------------

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


# ---------------------------------------------------------
# LATEST BALANCE
# ---------------------------------------------------------

latest_balance = (
    balance
    .dropna(subset=["year_num"])
    .sort_values(["company_id", "year_num"])
    .groupby("company_id")
    .tail(1)
    .copy()
)

print("Balance   :", len(latest_balance))


# ---------------------------------------------------------
# LATEST CASH FLOW
# ---------------------------------------------------------

latest_cashflow = (
    cashflow
    .dropna(subset=["year_num"])
    .sort_values(["company_id", "year_num"])
    .groupby("company_id")
    .tail(1)
    .copy()
)

print("Cash Flow :", len(latest_cashflow))


# ---------------------------------------------------------
# MERGE ALL LATEST DATA
# ---------------------------------------------------------

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


# ---------------------------------------------------------
# COMPANY NAME
# ---------------------------------------------------------

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

latest.drop(columns=["id"], inplace=True, errors="ignore")


# ---------------------------------------------------------
# NUMERIC CLEANING
# ---------------------------------------------------------

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


# ---------------------------------------------------------
# DERIVED METRICS
# ---------------------------------------------------------

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
    latest["operating_profit"] /
    latest["interest"].abs(),
    np.nan
)

latest["free_cash_flow"] = (
    latest["operating_activity"].fillna(0)
    + latest["investing_activity"].fillna(0)
)

latest["fcf_positive"] = latest["free_cash_flow"] > 0

latest["debt_to_assets"] = np.where(
    latest["total_assets"] != 0,
    latest["borrowings"] /
    latest["total_assets"],
    np.nan
)


# ---------------------------------------------------------
# DISPLAY
# ---------------------------------------------------------

print("\nMerged Latest Dataset :", len(latest))

print("\nLatest Dataset Columns")
print(latest.columns.tolist())


# =========================================================
# HISTORICAL DATA FOR TREND RULES
# =========================================================

# ---------------------------------------------------------
# PROFIT HISTORY
# ---------------------------------------------------------

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


# ---------------------------------------------------------
# ROE HISTORY
# ---------------------------------------------------------

roe_history = companies[
    ["id", "roe_percentage"]
].copy()

roe_history.rename(
    columns={"id": "company_id"},
    inplace=True
)


# ---------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------

def cagr(first, last, years):

    if pd.isna(first) or pd.isna(last):
        return np.nan

    if first <= 0 or last <= 0 or years <= 0:
        return np.nan

    return (
        ((last / first) ** (1 / years) - 1)
        * 100
    )


def has_consecutive_condition(
    df,
    column,
    condition,
    count
):

    values = df[column].dropna().tolist()

    if len(values) < count:
        return False

    streak = 0

    for value in values:

        if condition(value):
            streak += 1

            if streak >= count:
                return True

        else:
            streak = 0

    return False


# =========================================================
# GENERATE PROS & CONS
# =========================================================

records = []

all_companies = companies["id"].astype(str).str.strip().unique()


for company in all_companies:

    row_match = latest[
        latest["company_id"].astype(str).str.strip()
        == company
    ]

    if row_match.empty:
        continue

    row = row_match.iloc[0]

    company_name = row.get(
        "company_name",
        company
    )


    # -----------------------------------------------------
    # PRO RULE 1
    # ROE > 20%
    # -----------------------------------------------------

    roe = row.get("roe_percentage", np.nan)

    if pd.notna(roe) and roe > 20:

        records.append({
            "company_id": company,
            "type": "pro",
            "rule_id": "P1",
            "text":
                "Consistently high return on equity above 20% demonstrates exceptional capital efficiency.",
            "confidence_pct": 90
        })


    # -----------------------------------------------------
    # PRO RULE 2
    # FCF POSITIVE
    # -----------------------------------------------------

    if row.get("free_cash_flow", 0) > 0:

        records.append({
            "company_id": company,
            "type": "pro",
            "rule_id": "P2",
            "text":
                "Positive free cash flow indicates healthy business fundamentals.",
            "confidence_pct": 80
        })


    # -----------------------------------------------------
    # PRO RULE 3
    # DEBT FREE
    # -----------------------------------------------------

    de = row.get("debt_to_equity", np.nan)

    if pd.notna(de) and de == 0:

        records.append({
            "company_id": company,
            "type": "pro",
            "rule_id": "P3",
            "text":
                "Debt-free balance sheet provides financial flexibility and eliminates interest burden.",
            "confidence_pct": 95
        })


    # -----------------------------------------------------
    # PRO RULE 4
    # OPM > 25%
    # -----------------------------------------------------

    opm = row.get(
        "opm_percentage",
        np.nan
    )

    if pd.notna(opm) and opm > 25:

        records.append({
            "company_id": company,
            "type": "pro",
            "rule_id": "P4",
            "text":
                "Operating profit margin above 25% indicates strong pricing power and cost discipline.",
            "confidence_pct": 85
        })


    # -----------------------------------------------------
    # PRO RULE 5
    # HIGH INTEREST COVERAGE
    # -----------------------------------------------------

    icr = row.get(
        "interest_coverage",
        np.nan
    )

    if pd.notna(icr) and icr > 10:

        records.append({
            "company_id": company,
            "type": "pro",
            "rule_id": "P5",
            "text":
                "Very high interest coverage ratio reflects negligible financial stress from debt servicing.",
            "confidence_pct": 88
        })


    # -----------------------------------------------------
    # PRO RULE 6
    # POSITIVE EPS
    # -----------------------------------------------------

    eps = row.get("eps", np.nan)

    if pd.notna(eps) and eps > 0:

        records.append({
            "company_id": company,
            "type": "pro",
            "rule_id": "P6",
            "text":
                "Positive earnings per share indicate profitable operations.",
            "confidence_pct": 75
        })


    # -----------------------------------------------------
    # PRO RULE 7
    # REVENUE CAGR > 15%
    # -----------------------------------------------------

    hist = (
        profit_history[
            profit_history["company_id"] == company
        ]
        .sort_values("year_num")
    )

    if len(hist) >= 5:

        first_sales = hist.iloc[-5]["sales"]
        last_sales = hist.iloc[-1]["sales"]

        revenue_cagr = cagr(
            first_sales,
            last_sales,
            4
        )

        if pd.notna(revenue_cagr) and revenue_cagr > 15:

            records.append({
                "company_id": company,
                "type": "pro",
                "rule_id": "P7",
                "text":
                    "Revenue growing at above 15% CAGR over 5 years reflects strong business momentum.",
                "confidence_pct": 90
            })


    # -----------------------------------------------------
    # PRO RULE 8
    # PAT CAGR > 20%
    # -----------------------------------------------------

        first_profit = hist.iloc[-5]["net_profit"]
        last_profit = hist.iloc[-1]["net_profit"]

        pat_cagr = cagr(
            first_profit,
            last_profit,
            4
        )

        if pd.notna(pat_cagr) and pat_cagr > 20:

            records.append({
                "company_id": company,
                "type": "pro",
                "rule_id": "P8",
                "text":
                    "Net profit compounding at above 20% over 5 years creates significant shareholder value.",
                "confidence_pct": 90
            })


    # -----------------------------------------------------
    # PRO RULE 9
    # EPS POSITIVE + PROFIT GROWTH
    # -----------------------------------------------------

    if (
        pd.notna(eps)
        and eps > 0
        and pd.notna(row.get("net_profit"))
        and row.get("net_profit") > 0
    ):

        records.append({
            "company_id": company,
            "type": "pro",
            "rule_id": "P9",
            "text":
                "Positive earnings and net profit indicate a profitable operating base.",
            "confidence_pct": 78
        })


    # -----------------------------------------------------
    # PRO RULE 10
    # ASSET GROWTH
    # -----------------------------------------------------

    if (
        pd.notna(row.get("total_assets"))
        and row.get("total_assets") > 0
    ):

        records.append({
            "company_id": company,
            "type": "pro",
            "rule_id": "P10",
            "text":
                "A positive asset base provides capacity to support future business growth.",
            "confidence_pct": 70
        })


    # -----------------------------------------------------
    # PRO RULE 11
    # DIVIDEND PAYOUT
    # -----------------------------------------------------

    payout = row.get(
        "dividend_payout",
        np.nan
    )

    if pd.notna(payout) and 0 < payout <= 100:

        records.append({
            "company_id": company,
            "type": "pro",
            "rule_id": "P11",
            "text":
                "A sustainable dividend payout reflects shareholder distribution supported by earnings.",
            "confidence_pct": 70
        })


    # -----------------------------------------------------
    # PRO RULE 12
    # POSITIVE OPERATING CASH FLOW
    # -----------------------------------------------------

    cfo = row.get(
        "operating_activity",
        np.nan
    )

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
    # CON 1
    # HIGH D/E
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
    # CON 2
    # NEGATIVE FCF
    # -----------------------------------------------------

    if row.get("free_cash_flow", 0) < 0:

        records.append({
            "company_id": company,
            "type": "con",
            "rule_id": "C2",
            "text":
                "Negative free cash flow raises concern about cash generation quality.",
            "confidence_pct": 85
        })


    # -----------------------------------------------------
    # CON 3
    # LOW ICR
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
    # CON 4
    # NEGATIVE PROFIT
    # -----------------------------------------------------

    net_profit = row.get(
        "net_profit",
        np.nan
    )

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
    # CON 5
    # LOW ROE
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
    # CON 6
    # LOW OPM
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
    # CON 7
    # NEGATIVE EPS
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
    # CON 8
    # HIGH BORROWINGS
    # -----------------------------------------------------

    if (
        pd.notna(row.get("borrowings"))
        and pd.notna(row.get("total_assets"))
        and row["total_assets"] > 0
        and row["borrowings"] / row["total_assets"] > 0.5
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
    # CON 9
    # NEGATIVE CFO
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
    # CON 10
    # HIGH DIVIDEND PAYOUT
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
    # CON 11
    # LOW ROCE
    # -----------------------------------------------------

    roce = row.get(
        "roce_percentage",
        np.nan
    )

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
    # CON 12
    # NEGATIVE NET CASH FLOW
    # -----------------------------------------------------

    net_cf = row.get(
        "net_cash_flow",
        np.nan
    )

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
# =========================================================

covered_pro = set(
    pros_cons.loc[
        pros_cons["type"] == "pro",
        "company_id"
    ]
)

covered_con = set(
    pros_cons.loc[
        pros_cons["type"] == "con",
        "company_id"
    ]
)


for company in all_companies:

    if company not in covered_pro:

        pros_cons = pd.concat(
            [
                pros_cons,
                pd.DataFrame([{
                    "company_id": company,
                    "type": "pro",
                    "rule_id": "P_FALLBACK",
                    "text":
                        "The company has measurable financial data available for fundamental analysis.",
                    "confidence_pct": 65
                }])
            ],
            ignore_index=True
        )


    if company not in covered_con:

        pros_cons = pd.concat(
            [
                pros_cons,
                pd.DataFrame([{
                    "company_id": company,
                    "type": "con",
                    "rule_id": "C_FALLBACK",
                    "text":
                        "The company should continue to be monitored across profitability, leverage and cash-flow indicators.",
                    "confidence_pct": 65
                }])
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
# SAVE
# =========================================================

output_file = OUTPUT / "pros_cons_generated.csv"

pros_cons.to_csv(
    output_file,
    index=False
)


# =========================================================
# VALIDATION
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


print("\n" + "=" * 70)
print("DAY 30 VALIDATION")
print("=" * 70)

print("Total Companies :", len(all_companies))
print("Total Records   :", len(pros_cons))
print("Total Pros      :", (pros_cons["type"] == "pro").sum())
print("Total Cons      :", (pros_cons["type"] == "con").sum())

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

print("Missing Pro :", missing_pro)
print("Missing Con :", missing_con)

print("\nOutput:")
print(output_file)

print("\n" + "=" * 70)
print("DAY 30 COMPLETED")
print("=" * 70)