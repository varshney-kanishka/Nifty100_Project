def net_profit_margin(net_profit, sales):
    if sales == 0:
        return None
    return (net_profit / sales) * 100

def operating_profit_margin(op, sales):
    if sales == 0:
        return None

    return (op / sales) * 100

def roe(net_profit, equity, reserves):

    capital = equity + reserves

    if capital <= 0:
        return None

    return (net_profit / capital) * 100

def roce(ebit, equity, reserves, borrowings):

    capital = equity + reserves + borrowings

    if capital <= 0:
        return None

    return (ebit / capital) * 100

def roa(net_profit,total_assets):

    if total_assets==0:
        return None

    return (net_profit/total_assets)*100

def opm_cross_check(calculated_opm, dataset_opm):

    if dataset_opm is None:
        return False

    return abs(calculated_opm-dataset_opm) > 1

def debt_to_equity(borrowings, equity, reserves):
    capital = equity + reserves

    if borrowings == 0:
        return 0

    if capital <= 0:
        return None

    return borrowings / capital

def high_leverage_flag(de_ratio, sector):
    if sector == "Financials":
        return False

    return de_ratio > 5

def interest_coverage(operating_profit, other_income, interest):

    if interest == 0:
        return None

    return (operating_profit + other_income) / interest

def interest_coverage(operating_profit, other_income, interest):

    if interest == 0:
        return None

    return (operating_profit + other_income) / interest

def icr_label(interest):

    if interest == 0:
        return "Debt Free"

    return ""

def icr_warning(icr):

    if icr is None:
        return False

    return icr < 1.5

def net_debt(borrowings, investments):

    return borrowings - investments

def asset_turnover(sales, total_assets):

    if total_assets == 0:
        return None

    return sales / total_assets