
from src.analytics.cagr import calculate_cagr


def test_normal_cagr():
    _value, flag = calculate_cagr(100, 200, 5)
    assert flag == "OK"


def test_zero_base():
    _value, flag = calculate_cagr(0, 100, 5)
    assert flag == "ZERO_BASE"


def test_turnaround():
    _value, flag = calculate_cagr(-100, 100, 5)
    assert flag == "TURNAROUND"


def test_decline():
    _value, flag = calculate_cagr(100, -100, 5)
    assert flag == "DECLINE_TO_LOSS"


def test_both_negative():
    _value, flag = calculate_cagr(-100, -50, 5)
    assert flag == "BOTH_NEGATIVE"


def test_insufficient():
    _value, flag = calculate_cagr(100, 120, 2)
    assert flag == "INSUFFICIENT"


def test_invalid_period():
    _value, flag = calculate_cagr(100, 200, 0)
    assert flag == "INVALID_PERIOD"


def test_value_exists():
    value, _flag = calculate_cagr(100, 200, 5)
    assert value > 0


def test_flag_ok():
    _value, flag = calculate_cagr(100, 200, 5)
    assert flag == "OK"


def test_none_value():
    value, _flag = calculate_cagr(0, 100, 5)
    assert value is None