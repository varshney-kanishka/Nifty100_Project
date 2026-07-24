-- ===========================================
-- Query 1 : Total Companies
-- ===========================================

SELECT COUNT(*) AS total_companies
FROM companies;


-- ===========================================
-- Query 2 : Total Profit & Loss Records
-- ===========================================

SELECT COUNT(*) AS total_profit_records
FROM profitandloss;


-- ===========================================
-- Query 3 : Total Balance Sheet Records
-- ===========================================

SELECT COUNT(*) AS total_balancesheet_records
FROM balancesheet;


-- ===========================================
-- Query 4 : Total Cash Flow Records
-- ===========================================

SELECT COUNT(*) AS total_cashflow_records
FROM cashflow;


-- ===========================================
-- Query 5 : Top 10 Companies by Market Cap
-- ===========================================

SELECT
company_id,
MAX(market_cap_crore) AS market_cap
FROM market_cap
GROUP BY company_id
ORDER BY market_cap DESC
LIMIT 10;


-- ===========================================
-- Query 6 : Years Available Per Company
-- ===========================================

SELECT
company_id,
COUNT(*) AS years
FROM profitandloss
GROUP BY company_id
ORDER BY years DESC;


-- ===========================================
-- Query 7 : Companies Per Sector
-- ===========================================

SELECT
broad_sector,
COUNT(*) AS companies
FROM sectors
GROUP BY broad_sector
ORDER BY companies DESC;


-- ===========================================
-- Query 8 : Average Closing Price
-- ===========================================

SELECT
company_id,
AVG(close_price) AS avg_close
FROM stock_prices
GROUP BY company_id
ORDER BY avg_close DESC
LIMIT 10;


-- ===========================================
-- Query 9 : Highest Average ROE
-- ===========================================

SELECT
company_id,
AVG(return_on_equity_pct) AS avg_roe
FROM financial_ratios
GROUP BY company_id
ORDER BY avg_roe DESC
LIMIT 10;


-- ===========================================
-- Query 10 : Highest Net Profit
-- ===========================================

SELECT
company_id,
SUM(net_profit) AS total_profit
FROM profitandloss
GROUP BY company_id
ORDER BY total_profit DESC
LIMIT 10;