from src.etl.normaliser import normalize_year, normalize_ticker


def test_normalize_year():
    assert normalize_year("FY23") == 2023
    assert normalize_year("2022-23") == 2023
    assert normalize_year("2024") == 2024


def test_normalize_ticker():
    assert normalize_ticker("tcs.ns") == "TCS"
    assert normalize_ticker("reliance.bo") == "RELIANCE"
    assert normalize_ticker("INFY") == "INFY"