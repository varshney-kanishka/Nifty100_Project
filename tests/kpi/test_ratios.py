import pytest

from src.analytics.ratios import (
    net_profit_margin,
    operating_profit_margin,
    roe,
    roce,
    roa,
    opm_cross_check,
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