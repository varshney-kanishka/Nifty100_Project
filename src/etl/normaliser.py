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
    """
    if year is None:
        return None

    year = str(year).strip()

    if year.startswith("FY"):
        year = year.replace("FY", "")

    if "-" in year:
        year = year.split("-")[-1]

    if len(year) == 2:
        year = "20" + year

    try:
        return int(year)
    except ValueError:
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