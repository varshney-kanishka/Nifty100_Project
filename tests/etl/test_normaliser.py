from src.etl.normaliser import normalize_ticker, normalize_year


def test_normalize_year():
    assert normalize_year("FY23") == 2023
    assert normalize_year("2022-23") == 2023
    assert normalize_year("2024") == 2024
    assert normalize_year("Dec 2012") == 2012
    assert normalize_year("Mar 2014") == 2014
    assert normalize_year(2012.0) == 2012
    assert normalize_year("2012.0") == 2012


def test_normalize_ticker():
    assert normalize_ticker("tcs.ns") == "TCS"
    assert normalize_ticker("reliance.bo") == "RELIANCE"
    assert normalize_ticker("INFY") == "INFY"
