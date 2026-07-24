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