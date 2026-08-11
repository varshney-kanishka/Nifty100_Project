"""
normaliser.py

Contains helper functions to standardize data before loading
into the processed CSV files and database.
"""

import re


# ============================================================
# COMPANY ID NORMALIZATION
# ============================================================

COMPANY_ID_MAP = {
    # Source-data correction
    "AGTL": "ATGL",
}


def normalize_company_id(company_id):
    """
    Standardize company IDs.

    Examples:
        AGTL -> ATGL
        ATGL -> ATGL
        wipro -> WIPRO
    """

    if company_id is None:
        return None

    company_id = str(company_id).strip().upper()

    if not company_id:
        return None

    return COMPANY_ID_MAP.get(company_id, company_id)


# ============================================================
# YEAR NORMALIZATION
# ============================================================

def normalize_year(year):
    """
    Convert different year formats to a 4-digit year.

    Examples:
        FY23       -> 2023
        2022-23    -> 2023
        2023       -> 2023
        Dec 2012   -> 2012
        Mar 2014   -> 2014
    """

    if year is None:
        return None

    # --------------------------------------------------------
    # Convert numeric values safely
    # --------------------------------------------------------

    try:
        year_value = float(year)

        if year_value.is_integer():
            year = str(int(year_value))
        else:
            year = str(year)

    except (TypeError, ValueError):
        year = str(year)

    year = year.strip()

    if not year:
        return None

    # --------------------------------------------------------
    # Remove FY prefix
    # --------------------------------------------------------

    if year.upper().startswith("FY"):
        year = year[2:].strip()

    # --------------------------------------------------------
    # Handle ranges such as 2022-23
    # --------------------------------------------------------

    if "-" in year:
        parts = [
            part.strip()
            for part in year.split("-")
            if part.strip()
        ]

        if parts:
            year = parts[-1]

    # --------------------------------------------------------
    # Exact 4-digit year
    # --------------------------------------------------------

    match = re.fullmatch(r"(20\d{2}|19\d{2})", year)

    if match:
        return int(match.group(1))

    # --------------------------------------------------------
    # Find year inside text
    # Example: Mar 2014
    # --------------------------------------------------------

    match = re.search(r"(20\d{2}|19\d{2})", year)

    if match:
        return int(match.group(1))

    # --------------------------------------------------------
    # Handle 2-digit year
    # Example: 23 -> 2023
    # --------------------------------------------------------

    if len(year) == 2 and year.isdigit():
        return int("20" + year)

    return None


# ============================================================
# TICKER NORMALIZATION
# ============================================================

def normalize_ticker(ticker):
    """
    Standardize stock ticker symbols.

    Examples:
        tcs.ns       -> TCS
        reliance.ns  -> RELIANCE
        reliance.bo  -> RELIANCE
        INFY         -> INFY
    """

    if ticker is None:
        return None

    ticker = str(ticker).strip().upper()

    if not ticker:
        return None

    ticker = ticker.replace(".NS", "")
    ticker = ticker.replace(".BO", "")

    return ticker


# ============================================================
# QUICK TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("NORMALISER TEST")
    print("=" * 60)

    print("\nCompany ID:")
    print("AGTL   ->", normalize_company_id("AGTL"))
    print("ATGL   ->", normalize_company_id("ATGL"))
    print(" wipro ->", normalize_company_id(" wipro "))

    print("\nYear:")
    print("FY23      ->", normalize_year("FY23"))
    print("2022-23   ->", normalize_year("2022-23"))
    print("2023      ->", normalize_year("2023"))
    print("Dec 2012  ->", normalize_year("Dec 2012"))
    print("Mar 2014  ->", normalize_year("Mar 2014"))

    print("\nTicker:")
    print("tcs.ns       ->", normalize_ticker("tcs.ns"))
    print("reliance.bo  ->", normalize_ticker("reliance.bo"))
    print("INFY         ->", normalize_ticker("INFY"))

    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)