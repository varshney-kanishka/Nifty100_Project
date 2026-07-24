import pandas as pd
def quality_compounder(df):

    result = df.copy()

    result = result[
        (result["return_on_equity_pct"] > 15)
        &
        (result["debt_to_equity"] < 1)
        &
        (result["free_cash_flow_cr"] > 0)
    ]

    return result
def value_pick(df):

    result = df.copy()

    if "pe_ratio" in result.columns:
        result = result[result["pe_ratio"] < 20]

    if "pb_ratio" in result.columns:
        result = result[result["pb_ratio"] < 3]

    result = result[result["debt_to_equity"] < 2]

    return result
def growth_accelerator(df):

    result = df.copy()

    if "pat_cagr_5yr" in result.columns:
        result = result[result["pat_cagr_5yr"] > 20]

    result = result[result["debt_to_equity"] < 2]

    return result
def dividend_champion(df):

    result = df.copy()

    if "dividend_yield" in result.columns:
        result = result[result["dividend_yield"] > 2]

    if "dividend_payout_ratio_pct" in result.columns:
        result = result[result["dividend_payout_ratio_pct"] < 80]

    result = result[result["free_cash_flow_cr"] > 0]

    return result
def debt_free_bluechip(df):

    result = df.copy()

    result = result[result["debt_to_equity"] == 0]

    result = result[result["return_on_equity_pct"] > 12]

    if "sales" in result.columns:
        result = result[result["sales"] > 5000]

    return result
def turnaround_watch(df):

    result = df.copy()

    result = result[result["free_cash_flow_cr"] > 0]

    if "revenue_cagr_3yr" in result.columns:
        result = result[result["revenue_cagr_3yr"] > 10]

    return result