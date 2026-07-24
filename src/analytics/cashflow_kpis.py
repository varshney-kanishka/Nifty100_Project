"""
cashflow_kpis.py

Sprint 2 - Day 11

Cash Flow KPI calculations.
"""

import pandas as pd


# ---------------------------------------------------
# Free Cash Flow
# ---------------------------------------------------

def free_cash_flow(operating_activity, investing_activity):

    if pd.isna(operating_activity) or pd.isna(investing_activity):
        return None

    return operating_activity + investing_activity


# ---------------------------------------------------
# CFO Quality Score
# ---------------------------------------------------

def cfo_quality_score(cfo, pat):

    if pat == 0 or pd.isna(cfo) or pd.isna(pat):
        return None

    ratio = cfo / pat

    if ratio > 1:
        return "High Quality"

    elif ratio >= 0.5:
        return "Moderate"

    else:
        return "Accrual Risk"


# ---------------------------------------------------
# CapEx Intensity
# ---------------------------------------------------

def capex_intensity(investing_activity, sales):

    if sales == 0 or pd.isna(investing_activity):
        return None

    value = abs(investing_activity) / sales * 100

    if value < 3:
        label = "Asset Light"

    elif value <= 8:
        label = "Moderate"

    else:
        label = "Capital Intensive"

    return value, label


# ---------------------------------------------------
# FCF Conversion Rate
# ---------------------------------------------------

def fcf_conversion_rate(fcf, operating_profit):

    if operating_profit == 0 or pd.isna(fcf):
        return None

    return fcf / operating_profit * 100


# ---------------------------------------------------
# Capital Allocation Pattern
# ---------------------------------------------------

def capital_allocation_pattern(cfo, cfi, cff):

    if pd.isna(cfo) or pd.isna(cfi) or pd.isna(cff):
        return None

    s1 = "+" if cfo >= 0 else "-"
    s2 = "+" if cfi >= 0 else "-"
    s3 = "+" if cff >= 0 else "-"

    pattern = (s1, s2, s3)

    mapping = {

        ("+", "-", "-"): "Reinvestor",

        ("+", "+", "-"): "Liquidating Assets",

        ("-", "+", "+"): "Distress Signal",

        ("-", "-", "+"): "Growth Funded by Debt",

        ("+", "+", "+"): "Cash Accumulator",

        ("-", "-", "-"): "Pre-Revenue",

        ("+", "-", "+"): "Mixed",

    }

    return mapping.get(pattern, "Unknown")