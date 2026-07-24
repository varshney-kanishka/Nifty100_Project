import pytest

from src.analytics.ratios import (
    net_profit_margin,
    operating_profit_margin,
    roe,
    roce,
    roa,
    opm_cross_check,
    debt_to_equity,
    high_leverage_flag,
    interest_coverage,
    icr_label,
    icr_warning,
    net_debt,
    asset_turnover,
)

def test_net_profit_margin():
    assert net_profit_margin(100, 500) == 20


def test_net_profit_margin_zero_sales():
    assert net_profit_margin(100, 0) is None


def test_operating_profit_margin():
    assert operating_profit_margin(150, 1000) == 15


def test_roe():
    assert roe(120, 100, 300) == 30


def test_roe_negative_equity():
    assert roe(100, -200, 100) is None


def test_roce():
    assert roce(150, 100, 300, 100) == 30


def test_roa():
    assert roa(120, 1000) == 12


def test_opm_cross_check():
    assert opm_cross_check(25, 28) is True
    
def test_debt_to_equity():
    assert debt_to_equity(500,100,400) == 1


def test_debt_free():
    assert debt_to_equity(0,100,400) == 0


def test_interest_coverage():
    assert interest_coverage(500,100,50) == 12


def test_interest_zero():
    assert interest_coverage(500,100,0) is None


def test_icr_label():
    assert icr_label(0) == "Debt Free"


def test_high_leverage():
    assert high_leverage_flag(6,"Technology") is True


def test_net_debt():
    assert net_debt(500,100) == 400


def test_asset_turnover():
    assert asset_turnover(1000,500) == 2    