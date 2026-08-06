"""
normaliser.py
Contains helper functions to standardize data before loading into the database.
"""


def normalize_year(year):
    """
    Convert different year formats to a 4-digit year.
    Examples:
        FY23 -> 2023
        2022-23 -> 2023
        2023 -> 2023
        Dec 2012 -> 2012
        Mar 2014 -> 2014
    """
    if year is None:
        return None

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

    if year.upper().startswith("FY"):
        year = year[2:].strip()

    if "-" in year:
        parts = [part.strip() for part in year.split("-") if part.strip()]
        if parts:
            year = parts[-1]

    import re

    match = re.fullmatch(r"(20\d{2}|19\d{2})", year)
    if match:
        return int(match.group(1))

    match = re.search(r"(20\d{2}|19\d{2})", year)
    if match:
        return int(match.group(1))

    if len(year) == 2 and year.isdigit():
        return int("20" + year)

    return None


def normalize_ticker(ticker):
    """
    Standardize stock ticker symbols.
    Examples:
        tcs.ns -> TCS
        reliance.ns -> RELIANCE
        INFY -> INFY
    """
    if ticker is None:
        return None

    ticker = str(ticker).strip().upper()

    ticker = ticker.replace(".NS", "")
    ticker = ticker.replace(".BO", "")

    return ticker


if __name__ == "__main__":
    print(normalize_year("FY23"))
    print(normalize_year("2022-23"))
    print(normalize_ticker("tcs.ns"))
    print(normalize_ticker("reliance.bo"))
