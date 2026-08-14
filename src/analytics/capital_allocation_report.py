"""
Sprint 5 - Day 32
Capital Allocation Report

Tasks:
1. Verify capital allocation coverage for all 92 master companies
2. Normalize company IDs and financial years
3. Remove duplicate company-year records
4. Generate latest-year capital allocation distribution
5. Update cashflow_intelligence.xlsx
6. Generate year-over-year pattern changes

Outputs:
    output/capital_allocation.csv
    output/capital_allocation_distribution.csv
    output/capital_allocation_coverage_failures.csv
    output/pattern_changes.csv
    output/cashflow_intelligence.xlsx
"""

from pathlib import Path
import sqlite3

import numpy as np
import pandas as pd

from .cashflow_kpis import capital_allocation_pattern


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

DB = BASE_DIR / "data" / "database" / "nifty100.db"
OUTPUT = BASE_DIR / "output"

OUTPUT.mkdir(parents=True, exist_ok=True)


# ============================================================
# CONSTANTS
# ============================================================

PATTERN_ORDER = [
    "Reinvestor",
    "Liquidating Assets",
    "Distress Signal",
    "Growth Funded by Debt",
    "Cash Accumulator",
    "Pre-Revenue",
    "Mixed",
    "Unknown",
]


# ============================================================
# COMPANY ID ALIASES
#
# AGTL in cashflow is the known typo/mismatch for ATGL
# in the master companies table.
# ============================================================

COMPANY_ID_ALIASES = {
    "AGTL": "ATGL",
}


# ============================================================
# HELPERS
# ============================================================

def normalize_company_id(value):
    """
    Normalize company IDs and correct known source-data aliases.
    """

    if pd.isna(value):
        return None

    value = str(value).strip().upper()

    if value == "":
        return None

    return COMPANY_ID_ALIASES.get(value, value)


def normalize_year(value):
    """
    Convert different year formats into a single integer year.

    Examples:
        'Mar 2024' -> 2024
        'Mar-24'   -> 2024
        'FY2024'   -> 2024
        '2024'     -> 2024
        'Dec 2012' -> 2012

    Returns NaN if no usable year is found.
    """

    if pd.isna(value):
        return np.nan

    text = str(value).strip()

    if text == "":
        return np.nan

    # First look for a four-digit year.
    match = pd.Series([text]).str.extract(r"((?:19|20)\d{2})")[0].iloc[0]

    if pd.notna(match):
        return int(match)

    # If only a two-digit year exists, handle it.
    match_two_digit = pd.Series([text]).str.extract(
        r"(?:^|[-/\s])(\d{2})(?:$|[-/\s])"
    )[0].iloc[0]

    if pd.notna(match_two_digit):
        year = int(match_two_digit)

        if year <= 30:
            return 2000 + year

        return 1900 + year

    return np.nan


def remove_duplicate_company_year(df):
    """
    Remove exact duplicates and then keep one record per
    company + normalized year.

    This fixes cases such as:
        TCS: Mar 2024 and Mar-24
    being treated as separate years.
    """

    before = len(df)

    # Remove exact duplicate rows.
    df = df.drop_duplicates().copy()

    # Normalize IDs and years first.
    df["company_id"] = df["company_id"].apply(normalize_company_id)
    df["year_num"] = df["year"].apply(normalize_year)

    # Remove rows where company or year cannot be identified.
    df = df[
        df["company_id"].notna()
        & df["year_num"].notna()
    ].copy()

    # Sort so the final record is deterministic.
    df = df.sort_values(
        ["company_id", "year_num"]
    )

    # Keep exactly one record per company-year.
    df = (
        df.drop_duplicates(
            subset=["company_id", "year_num"],
            keep="last",
        )
        .reset_index(drop=True)
    )

    after = len(df)

    print(
        f"\nDuplicate cleanup: {before} -> {after} rows "
        f"(removed {before - after})"
    )

    return df


def create_sign(value):
    """
    Convert cash-flow value into + / -.
    """

    if pd.isna(value):
        return None

    if value >= 0:
        return "+"

    return "-"


def validate_numeric_columns(df):
    """
    Convert cash-flow activity columns to numeric values.
    Invalid values become NaN.
    """

    numeric_columns = [
        "operating_activity",
        "investing_activity",
        "financing_activity",
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    return df


# ============================================================
# START
# ============================================================

print("=" * 70)
print("DAY 32 - CAPITAL ALLOCATION REPORT")
print("=" * 70)


print("\nDatabase:")
print(DB)


if not DB.exists():
    raise FileNotFoundError(
        f"Database not found:\n{DB}"
    )


# ============================================================
# DATABASE CONNECTION
# ============================================================

conn = sqlite3.connect(DB)


try:

    # ========================================================
    # LOAD MASTER COMPANIES
    # ========================================================

    companies = pd.read_sql(
        "SELECT id FROM companies",
        conn,
    )

    companies["id"] = companies["id"].apply(
        normalize_company_id
    )

    companies = companies[
        companies["id"].notna()
    ].drop_duplicates(
        subset=["id"]
    )

    master_companies = set(
        companies["id"]
    )

    print(
        "\nMaster Companies :",
        len(master_companies),
    )


    # ========================================================
    # LOAD CASH FLOW
    # ========================================================

    cashflow = pd.read_sql(
        """
        SELECT
            company_id,
            year,
            operating_activity,
            investing_activity,
            financing_activity
        FROM cashflow
        """,
        conn,
    )

    print(
        "Raw Cash Flow Rows :",
        len(cashflow),
    )


    # ========================================================
    # NORMALIZE CASH FLOW
    # ========================================================

    cashflow["company_id"] = cashflow[
        "company_id"
    ].apply(normalize_company_id)

    cashflow["year_num"] = cashflow[
        "year"
    ].apply(normalize_year)

    cashflow = validate_numeric_columns(
        cashflow
    )


    # ========================================================
    # REMOVE INVALID RECORDS
    # ========================================================

    invalid_company_rows = cashflow[
        cashflow["company_id"].isna()
    ]

    invalid_year_rows = cashflow[
        cashflow["year_num"].isna()
    ]

    if len(invalid_company_rows) > 0:
        print(
            "\nWarning:",
            len(invalid_company_rows),
            "cash-flow rows have invalid company IDs.",
        )

    if len(invalid_year_rows) > 0:
        print(
            "Warning:",
            len(invalid_year_rows),
            "cash-flow rows have invalid years.",
        )

    cashflow = cashflow[
        cashflow["company_id"].notna()
        & cashflow["year_num"].notna()
    ].copy()


    # ========================================================
    # DUPLICATE CLEANUP
    # ========================================================

    cashflow = remove_duplicate_company_year(
        cashflow
    )


    # ========================================================
    # FILTER TO MASTER 92-COMPANY UNIVERSE
    # ========================================================

    cashflow_master = cashflow[
        cashflow["company_id"].isin(
            master_companies
        )
    ].copy()

    cashflow_extra = cashflow[
        ~cashflow["company_id"].isin(
            master_companies
        )
    ].copy()


    # ========================================================
    # COMPANY COVERAGE
    # ========================================================

    cashflow_companies = set(
        cashflow_master["company_id"]
    )

    missing_companies = sorted(
        master_companies
        - cashflow_companies
    )

    extra_companies = sorted(
        set(cashflow["company_id"])
        - master_companies
    )


    print("\n" + "=" * 70)
    print("COMPANY COVERAGE CHECK")
    print("=" * 70)

    print(
        "\nCompanies in master table :",
        len(master_companies),
    )

    print(
        "Companies in cash flow     :",
        len(cashflow_companies),
    )

    print(
        "Missing companies          :",
        len(missing_companies),
    )

    print(
        "Extra companies            :",
        len(extra_companies),
    )


    if missing_companies:
        print(
            "\nMISSING FROM CASH FLOW:"
        )

        for company in missing_companies:
            print(" -", company)

    else:
        print(
            "\nAll 92 master companies are present "
            "in cash flow after normalization."
        )


    if extra_companies:
        print(
            "\nEXTRA CASH FLOW COMPANIES "
            "(excluded from Day 32 universe):"
        )

        for company in extra_companies:
            print(" -", company)


    # ========================================================
    # COMPANY-YEAR COVERAGE
    #
    # We validate that every master company that has cash-flow
    # data is represented correctly after normalization.
    #
    # We do NOT invent historical years for companies that
    # did not have data during earlier periods.
    # ========================================================

    print("\n" + "=" * 70)
    print("COMPANY-YEAR COVERAGE CHECK")
    print("=" * 70)


    years_by_company = (
        cashflow_master
        .groupby("company_id")["year_num"]
        .apply(
            lambda x: sorted(
                set(x.astype(int))
            )
        )
        .to_dict()
    )


    coverage_records = []

    for company_id in sorted(master_companies):

        company_years = years_by_company.get(
            company_id,
            [],
        )

        if len(company_years) == 0:

            coverage_records.append(
                {
                    "company_id": company_id,
                    "status": "MISSING_COMPANY",
                    "year": np.nan,
                }
            )

            continue

        # Check for gaps only inside the company's
        # observed historical range.
        min_year = min(company_years)
        max_year = max(company_years)

        expected_years = set(
            range(
                min_year,
                max_year + 1,
            )
        )

        actual_years = set(
            company_years
        )

        missing_years = sorted(
            expected_years
            - actual_years
        )

        for year in missing_years:

            coverage_records.append(
                {
                    "company_id": company_id,
                    "status": "MISSING_YEAR",
                    "year": year,
                }
            )


    coverage_failures = pd.DataFrame(
        coverage_records
    )


    coverage_path = (
        OUTPUT
        / "capital_allocation_coverage_failures.csv"
    )


    if coverage_failures.empty:

        # Create an empty file with consistent columns.
        coverage_failures = pd.DataFrame(
            columns=[
                "company_id",
                "status",
                "year",
            ]
        )

        print(
            "\nCoverage check: PASSED"
        )

        print(
            "No missing company-year gaps "
            "inside observed ranges."
        )

    else:

        print(
            "\nCoverage check: FAILED"
        )

        print(
            "Missing company-year records:",
            len(coverage_failures),
        )

        print(
            coverage_failures.to_string(
                index=False
            )
        )


    coverage_failures.to_csv(
        coverage_path,
        index=False,
    )


    print(
        "\nCoverage details saved:",
        coverage_path,
    )


    # ========================================================
    # CAPITAL ALLOCATION PATTERN
    # ========================================================

    cashflow_master[
        "pattern_label"
    ] = cashflow_master.apply(
        lambda row:
            capital_allocation_pattern(
                row["operating_activity"],
                row["investing_activity"],
                row["financing_activity"],
            ),
        axis=1,
    )


    # ========================================================
    # SIGNS
    # ========================================================

    cashflow_master[
        "cfo_sign"
    ] = cashflow_master[
        "operating_activity"
    ].apply(create_sign)

    cashflow_master[
        "cfi_sign"
    ] = cashflow_master[
        "investing_activity"
    ].apply(create_sign)

    cashflow_master[
        "cff_sign"
    ] = cashflow_master[
        "financing_activity"
    ].apply(create_sign)


    # ========================================================
    # CAPITAL ALLOCATION OUTPUT
    # ========================================================

    capital_allocation = cashflow_master[
        [
            "company_id",
            "year_num",
            "cfo_sign",
            "cfi_sign",
            "cff_sign",
            "pattern_label",
        ]
    ].copy()


    capital_allocation = capital_allocation.rename(
        columns={
            "year_num": "year",
        }
    )


    capital_allocation = (
        capital_allocation
        .sort_values(
            [
                "company_id",
                "year",
            ]
        )
        .reset_index(drop=True)
    )


    capital_allocation_path = (
        OUTPUT
        / "capital_allocation.csv"
    )


    capital_allocation.to_csv(
        capital_allocation_path,
        index=False,
    )


    print(
        "\nSaved:",
        capital_allocation_path,
    )


    # ========================================================
    # LATEST YEAR
    # ========================================================

    latest_year = int(
        cashflow_master["year_num"].max()
    )


    latest = cashflow_master[
        cashflow_master["year_num"]
        == latest_year
    ].copy()


    print("\n" + "=" * 70)
    print("LATEST YEAR CAPITAL ALLOCATION DISTRIBUTION")
    print("=" * 70)

    print(
        "\nLatest year:",
        latest_year,
    )

    print(
        "Companies in latest year:",
        latest["company_id"].nunique(),
    )


    # ========================================================
    # CHECK LATEST YEAR COVERAGE
    # ========================================================

    latest_companies = set(
        latest["company_id"]
    )

    latest_missing = sorted(
        master_companies
        - latest_companies
    )


    if latest_missing:

        print(
            "\nWARNING - companies missing "
            "from latest year:"
        )

        for company in latest_missing:
            print(" -", company)

    else:

        print(
            "\nLatest year contains all 92 "
            "master companies."
        )


    # ========================================================
    # DISTRIBUTION
    # ========================================================

    distribution_counts = (
        latest["pattern_label"]
        .value_counts()
    )


    distribution = pd.DataFrame(
        {
            "latest_year": latest_year,
            "capital_allocation_pattern":
                PATTERN_ORDER,
            "company_count": [
                int(
                    distribution_counts.get(
                        pattern,
                        0,
                    )
                )
                for pattern in PATTERN_ORDER
            ],
        }
    )


    distribution_path = (
        OUTPUT
        / "capital_allocation_distribution.csv"
    )


    distribution.to_csv(
        distribution_path,
        index=False,
    )


    print(
        "\n",
        distribution.to_string(
            index=False
        )
    )


    print(
        "\nDistribution saved:",
        distribution_path,
    )


    # ========================================================
    # UPDATE CASH FLOW INTELLIGENCE
    # ========================================================

    print("\n" + "=" * 70)
    print("UPDATING CASH FLOW INTELLIGENCE")
    print("=" * 70)


    excel_path = (
        OUTPUT
        / "cashflow_intelligence.xlsx"
    )


    if excel_path.exists():

        cashflow_intelligence = pd.read_excel(
            excel_path
        )

        cashflow_intelligence[
            "company_id"
        ] = cashflow_intelligence[
            "company_id"
        ].apply(normalize_company_id)


        # Keep only master companies.
        cashflow_intelligence = (
            cashflow_intelligence[
                cashflow_intelligence[
                    "company_id"
                ].isin(master_companies)
            ]
            .copy()
        )


        # Latest capital allocation pattern.
        latest_pattern = latest[
            [
                "company_id",
                "pattern_label",
            ]
        ].copy()


        latest_pattern = (
            latest_pattern
            .drop_duplicates(
                subset=["company_id"]
            )
            .rename(
                columns={
                    "pattern_label":
                        "capital_allocation_label"
                }
            )
        )


        # Remove old column if it already exists
        # so the merge doesn't create duplicates.
        if (
            "capital_allocation_label"
            in cashflow_intelligence.columns
        ):

            cashflow_intelligence = (
                cashflow_intelligence.drop(
                    columns=[
                        "capital_allocation_label"
                    ]
                )
            )


        cashflow_intelligence = (
            cashflow_intelligence.merge(
                latest_pattern,
                on="company_id",
                how="left",
            )
        )


        # Make sure the output contains exactly
        # the 92 master companies.
        master_order = (
            companies["id"]
            .drop_duplicates()
            .tolist()
        )


        cashflow_intelligence = (
            cashflow_intelligence[
                cashflow_intelligence[
                    "company_id"
                ].isin(master_companies)
            ]
            .copy()
        )


        # If duplicate rows somehow remain,
        # keep one row per company.
        cashflow_intelligence = (
            cashflow_intelligence
            .drop_duplicates(
                subset=["company_id"]
            )
            .copy()
        )


        # Reorder according to master company order.
        cashflow_intelligence[
            "_company_order"
        ] = cashflow_intelligence[
            "company_id"
        ].map(
            {
                company_id: index
                for index, company_id
                in enumerate(master_order)
            }
        )


        cashflow_intelligence = (
            cashflow_intelligence
            .sort_values("_company_order")
            .drop(
                columns=["_company_order"]
            )
            .reset_index(drop=True)
        )


        cashflow_intelligence.to_excel(
            excel_path,
            index=False,
        )


        print(
            "\nUpdated:",
            excel_path,
        )

        print(
            "Rows:",
            len(cashflow_intelligence),
        )

        print(
            "Unique companies:",
            cashflow_intelligence[
                "company_id"
            ].nunique(),
        )

    else:

        print(
            "\nWARNING:"
        )

        print(
            "cashflow_intelligence.xlsx "
            "was not found."
        )

        print(
            "Expected:",
            excel_path,
        )


    # ========================================================
    # YEAR-OVER-YEAR PATTERN CHANGES
    # ========================================================

    print("\n" + "=" * 70)
    print("YEAR-OVER-YEAR PATTERN CHANGES")
    print("=" * 70)


    pattern_data = cashflow_master[
        [
            "company_id",
            "year_num",
            "pattern_label",
        ]
    ].copy()


    pattern_data = (
        pattern_data
        .sort_values(
            [
                "company_id",
                "year_num",
            ]
        )
        .reset_index(drop=True)
    )


    # Previous available year and pattern.
    pattern_data[
        "previous_year"
    ] = pattern_data.groupby(
        "company_id"
    )["year_num"].shift(1)

    pattern_data[
        "previous_pattern"
    ] = pattern_data.groupby(
        "company_id"
    )["pattern_label"].shift(1)


    # Only call it a YEAR-OVER-YEAR change when
    # the previous record is exactly one year earlier.
    pattern_changes = pattern_data[
        (
            pattern_data["year_num"]
            - pattern_data["previous_year"]
            == 1
        )
        &
        (
            pattern_data["pattern_label"]
            != pattern_data["previous_pattern"]
        )
    ].copy()


    pattern_changes = pattern_changes[
        [
            "company_id",
            "previous_year",
            "year_num",
            "previous_pattern",
            "pattern_label",
        ]
    ].rename(
        columns={
            "year_num": "current_year",
            "pattern_label": "current_pattern",
        }
    )


    pattern_changes = (
        pattern_changes
        .sort_values(
            [
                "company_id",
                "current_year",
            ]
        )
        .reset_index(drop=True)
    )


    pattern_changes_path = (
        OUTPUT
        / "pattern_changes.csv"
    )


    pattern_changes.to_csv(
        pattern_changes_path,
        index=False,
    )


    print(
        "\nPattern changes found:",
        len(pattern_changes),
    )


    if len(pattern_changes) > 0:

        print(
            "\nSample changes:"
        )

        print(
            pattern_changes.head(10)
            .to_string(index=False)
        )

    else:

        print(
            "\nNo year-over-year pattern changes found."
        )


    print(
        "\nSaved:",
        pattern_changes_path,
    )


    # ========================================================
    # FINAL VALIDATION SUMMARY
    # ========================================================

    print("\n" + "=" * 70)
    print("DAY 32 FINAL VALIDATION")
    print("=" * 70)


    print(
        "\nMaster companies:",
        len(master_companies),
    )

    print(
        "Capital Allocation rows:",
        len(capital_allocation),
    )

    print(
        "Unique companies:",
        capital_allocation[
            "company_id"
        ].nunique(),
    )

    print(
        "Years:",
        capital_allocation[
            "year"
        ].nunique(),
    )

    print(
        "Latest year:",
        latest_year,
    )

    print(
        "Latest-year companies:",
        latest[
            "company_id"
        ].nunique(),
    )

    print(
        "Pattern changes:",
        len(pattern_changes),
    )

    print(
        "\nExpected latest-year distribution total:",
        len(latest),
    )

    print(
        "Distribution total:",
        distribution[
            "company_count"
        ].sum(),
    )


    # ========================================================
    # FINAL CHECKS
    # ========================================================

    if len(master_companies) != 92:

        print(
            "\nWARNING: Master company count is not 92."
        )


    if len(latest_companies) != 92:

        print(
            "\nWARNING: Latest year does not contain "
            "all 92 companies."
        )

    else:

        print(
            "\nPASS: Latest year contains all 92 companies."
        )


    if (
        distribution[
            "company_count"
        ].sum()
        == len(latest)
    ):

        print(
            "PASS: Distribution counts reconcile."
        )

    else:

        print(
            "FAIL: Distribution counts do not reconcile."
        )


    print("\nFiles created/updated:")

    print(
        "1.",
        capital_allocation_path,
    )

    print(
        "2.",
        distribution_path,
    )

    print(
        "3.",
        coverage_path,
    )

    print(
        "4.",
        pattern_changes_path,
    )

    print(
        "5.",
        excel_path,
    )


finally:

    conn.close()


print("\n" + "=" * 70)
print("DAY 32 CAPITAL ALLOCATION REPORT COMPLETED")
print("=" * 70)
