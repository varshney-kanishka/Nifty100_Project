import pytest

from src.analytics.cagr import calculate_cagr


def test_normal_cagr():
    value, flag = calculate_cagr(100, 200, 5)
    assert flag == "OK"


def test_zero_base():
    value, flag = calculate_cagr(0, 100, 5)
    assert flag == "ZERO_BASE"


def test_turnaround():
    value, flag = calculate_cagr(-100, 100, 5)
    assert flag == "TURNAROUND"


def test_decline():
    value, flag = calculate_cagr(100, -100, 5)
    assert flag == "DECLINE_TO_LOSS"


def test_both_negative():
    value, flag = calculate_cagr(-100, -50, 5)
    assert flag == "BOTH_NEGATIVE"


def test_insufficient():
    value, flag = calculate_cagr(100, 120, 2)
    assert flag == "INSUFFICIENT"


def test_invalid_period():
    value, flag = calculate_cagr(100, 200, 0)
    assert flag == "INVALID_PERIOD"


def test_value_exists():
    value, flag = calculate_cagr(100, 200, 5)
    assert value > 0


def test_flag_ok():
    value, flag = calculate_cagr(100, 200, 5)
    assert flag == "OK"


def test_none_value():
    value, flag = calculate_cagr(0, 100, 5)
    assert value is None