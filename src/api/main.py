from pathlib import Path
import sqlite3



import pandas as pd
from fastapi import FastAPI, HTTPException

from src.screener.presets import (
    quality_compounder,
    value_pick,
    growth_accelerator,
    dividend_champion,
    debt_free_bluechip,
    turnaround_watch,
)

# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

DB_PATH = BASE_DIR / "data" / "database" / "nifty100.db"


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(
    title="Nifty100 Analytics API",
    description=(
        "REST API for Nifty100 financial analytics, "
        "screening, peer comparison and portfolio intelligence."
    ),
    version="1.0.0",
)


# ============================================================
# DATABASE HELPER
# ============================================================

def get_connection():
    return sqlite3.connect(DB_PATH)


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    return {
        "message": "Nifty100 Analytics API",
        "status": "running",
        "version": "1.0.0",
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


# ============================================================
# DATABASE HEALTH
# ============================================================

@app.get("/health/database")
def database_health():

    try:
        conn = get_connection()

        cursor = conn.cursor()

        cursor.execute(
            "SELECT COUNT(*) FROM companies"
        )

        company_count = cursor.fetchone()[0]

        conn.close()

        return {
            "status": "healthy",
            "database": "connected",
            "companies": company_count,
        }

    except Exception as e:

        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
        }
# ============================================================
# COMPANIES
# ============================================================

@app.get("/companies")
def get_companies(
    limit: int = 20,
    offset: int = 0,
):
    """
    Return a paginated list of Nifty100 companies.
    """

    # Basic validation
    if limit < 1:
        limit = 1

    if limit > 100:
        limit = 100

    if offset < 0:
        offset = 0

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            id,
            company_name,
            website,
            nse_profile,
            bse_profile,
            face_value,
            book_value,
            roce_percentage,
            roe_percentage
        FROM companies
        ORDER BY company_name
        LIMIT ? OFFSET ?
        """,
        (limit, offset),
    )

    rows = cursor.fetchall()

    # Get total count
    cursor.execute(
        "SELECT COUNT(*) FROM companies"
    )

    total = cursor.fetchone()[0]

    conn.close()



    companies = []

    for row in rows:

        companies.append(
            {
                "id": row[0],
                "company_name": row[1],
                "website": row[2],
                "nse_profile": row[3],
                "bse_profile": row[4],
                "face_value": row[5],
                "book_value": row[6],
                "roce_percentage": row[7],
                "roe_percentage": row[8],
            }
        )

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "count": len(companies),
        "companies": companies,
    }

    # ============================================================
# COMPANY DETAIL
# ============================================================

@app.get("/companies/{company_id}")
def get_company(company_id: str):
    """
    Return detailed information for a single Nifty100 company.
    """

    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                id,
                company_logo,
                company_name,
                chart_link,
                about_company,
                website,
                nse_profile,
                bse_profile,
                face_value,
                book_value,
                roce_percentage,
                roe_percentage
            FROM companies
            WHERE id = ?
            """,
            (company_id.upper().strip(),),
        )

        row = cursor.fetchone()

    finally:
        conn.close()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "Company not found",
                "company_id": company_id,
            },
        )

    return {
        "id": row[0],
        "company_logo": row[1],
        "company_name": row[2],
        "chart_link": row[3],
        "about_company": row[4],
        "website": row[5],
        "nse_profile": row[6],
        "bse_profile": row[7],
        "face_value": row[8],
        "book_value": row[9],
        "roce_percentage": row[10],
        "roe_percentage": row[11],
    }

    # ============================================================
# SECTORS
# ============================================================

@app.get("/sectors")
def get_sectors():
    """
    Return sector-level summary for the Nifty100 universe.
    """

    conn = get_connection()

    try:
        query = """
            SELECT
                broad_sector,
                COUNT(*) AS company_count,
                SUM(index_weight_pct) AS total_index_weight_pct
            FROM sectors
            WHERE broad_sector IS NOT NULL
            GROUP BY broad_sector
            ORDER BY total_index_weight_pct DESC
        """

        sectors_df = pd.read_sql(query, conn)

    finally:
        conn.close()

    sectors_df = sectors_df.where(
        pd.notna(sectors_df),
        None,
    )

    sectors = []

    for _, row in sectors_df.iterrows():

        sectors.append(
            {
                "broad_sector": row["broad_sector"],
                "company_count": int(row["company_count"]),
                "total_index_weight_pct": (
                    float(row["total_index_weight_pct"])
                    if row["total_index_weight_pct"] is not None
                    else None
                ),
            }
        )

    return {
        "count": len(sectors),
        "sectors": sectors,
    }

 # ============================================================
# SCREENER
# ============================================================

SCREENER_PRESETS = {
    "quality_compounder": quality_compounder,
    "value_pick": value_pick,
    "growth_accelerator": growth_accelerator,
    "dividend_champion": dividend_champion,
    "debt_free_bluechip": debt_free_bluechip,
    "turnaround_watch": turnaround_watch,
}


@app.get("/screener/{preset}")
def run_screener(
    preset: str,
    limit: int = 20,
):
    """
    Run a predefined Nifty100 screening strategy.
    """

    if preset not in SCREENER_PRESETS:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "Unknown screener preset",
                "available_presets": list(
                    SCREENER_PRESETS.keys()
                ),
            },
        )

    if limit < 1:
        limit = 1

    if limit > 100:
        limit = 100

    conn = get_connection()

    try:

        ratios = pd.read_sql(
            "SELECT * FROM financial_ratios",
            conn,
        )

        companies = pd.read_sql(
            """
            SELECT
                id,
                company_name
            FROM companies
            """,
            conn,
        )

        sectors = pd.read_sql(
            """
            SELECT
                company_id,
                broad_sector
            FROM sectors
            """,
            conn,
        )

    finally:

        conn.close()




    # --------------------------------------------------------
    # Validate required data
    # --------------------------------------------------------

    if ratios.empty:

        return {
            "preset": preset,
            "count": 0,
            "results": [],
        }

    # --------------------------------------------------------
    # Normalize IDs
    # --------------------------------------------------------

    ratios["company_id"] = (
        ratios["company_id"]
        .astype(str)
        .str.strip()
    )

    companies["id"] = (
        companies["id"]
        .astype(str)
        .str.strip()
    )

    sectors["company_id"] = (
        sectors["company_id"]
        .astype(str)
        .str.strip()
    )

    # --------------------------------------------------------
    # Latest financial record per company
    # --------------------------------------------------------

    if "year" in ratios.columns:

        ratios["_year_num"] = pd.to_numeric(
            ratios["year"],
            errors="coerce",
        )

        ratios = (
            ratios
            .sort_values(
                ["company_id", "_year_num"]
            )
            .groupby(
                "company_id",
                as_index=False,
            )
            .tail(1)
        )

    # --------------------------------------------------------
    # Merge company information
    # --------------------------------------------------------

    df = ratios.merge(
        companies,
        left_on="company_id",
        right_on="id",
        how="left",
    )

    df = df.merge(
        sectors,
        on="company_id",
        how="left",
    )

    # --------------------------------------------------------
    # Run selected preset
    # --------------------------------------------------------

    screening_function = SCREENER_PRESETS[preset]

    try:

        result = screening_function(df)

    except KeyError as e:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Required screener column is missing: {e}"
            ),
        )

    # --------------------------------------------------------
    # Limit output
    # --------------------------------------------------------

    result = result.head(limit)

    # --------------------------------------------------------
    # Convert to JSON-safe records
    # --------------------------------------------------------

    output_columns = [
        "company_id",
        "company_name",
        "broad_sector",
        "year",
        "return_on_equity_pct",
        "debt_to_equity",
        "free_cash_flow_cr",
    ]

    available_columns = [
        column
        for column in output_columns
        if column in result.columns
    ]

    result = result[available_columns].copy()

    result = result.where(
        pd.notna(result),
        None,
    )

    records = result.to_dict(
        orient="records"
    )

    return {
        "preset": preset,
        "count": len(records),
        "results": records,
    }
# ============================================================
# MARKET CAP ANALYTICS
# ============================================================

@app.get("/market-cap")
def get_market_cap():

    conn = get_connection()

    try:

        query = """
            SELECT
                market_cap_category,
                COUNT(*) AS company_count,
                SUM(index_weight_pct) AS total_index_weight_pct
            FROM sectors
            WHERE market_cap_category IS NOT NULL
            GROUP BY market_cap_category
            ORDER BY total_index_weight_pct DESC
        """

        market_cap_df = pd.read_sql(
            query,
            conn,
        )

    finally:
        conn.close()

    market_cap_df = market_cap_df.where(
        pd.notna(market_cap_df),
        None,
    )

    categories = []

    for _, row in market_cap_df.iterrows():

        categories.append(
            {
                "market_cap_category": row["market_cap_category"],
                "company_count": int(row["company_count"]),
                "total_index_weight_pct": (
                    float(row["total_index_weight_pct"])
                    if row["total_index_weight_pct"] is not None
                    else None
                ),
            }
        )

    return {
        "count": len(categories),
        "market_cap": categories,
    }
# ============================================================
# PEER COMPARISON
# ============================================================

@app.get("/peers/{company_id}")
def get_peers(
    company_id: str,
    limit: int = 5,
):
    """
    Return peer companies from the same broad sector.
    """

    company_id = company_id.upper().strip()

    if limit < 1:
        limit = 1

    if limit > 20:
        limit = 20

    conn = get_connection()

    try:

        # ----------------------------------------------------
        # Find target company's sector
        # ----------------------------------------------------

        target_query = """
            SELECT
                c.id,
                c.company_name,
                s.broad_sector
            FROM companies c
            LEFT JOIN sectors s
                ON c.id = s.company_id
            WHERE c.id = ?
        """

        target_df = pd.read_sql(
            target_query,
            conn,
            params=(company_id,),
        )

        if target_df.empty:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "Company not found",
                    "company_id": company_id,
                },
            )

        target_sector = target_df.iloc[0]["broad_sector"]

        # ----------------------------------------------------
        # Get all companies in same sector
        # ----------------------------------------------------

        peers_query = """
            SELECT
                c.id AS company_id,
                c.company_name,
                s.broad_sector,
                fr.year,
                fr.return_on_equity_pct,
                fr.return_on_capital_employed_pct,
                fr.net_profit_margin_pct,
                fr.operating_profit_margin_pct,
                fr.debt_to_equity,
                fr.interest_coverage,
                fr.asset_turnover,
                fr.free_cash_flow_cr,
                fr.earnings_per_share,
                fr.dividend_payout_ratio_pct
            FROM companies c
            INNER JOIN sectors s
                ON c.id = s.company_id
            INNER JOIN financial_ratios fr
                ON c.id = fr.company_id
            WHERE s.broad_sector = ?
              AND c.id != ?
        """

        peers_df = pd.read_sql(
            peers_query,
            conn,
            params=(target_sector, company_id),
        )

    finally:

        conn.close()

    # --------------------------------------------------------
    # Keep latest financial year per company
    # --------------------------------------------------------

    if not peers_df.empty:

        peers_df["_year_num"] = pd.to_numeric(
            peers_df["year"],
            errors="coerce",
        )

        peers_df = (
            peers_df
            .sort_values(
                ["company_id", "_year_num"]
            )
            .groupby(
                "company_id",
                as_index=False,
            )
            .tail(1)
        )

        peers_df = peers_df.sort_values(
            "company_name"
        ).head(limit)

    # --------------------------------------------------------
    # Convert NaN to None
    # --------------------------------------------------------

    peers_df = peers_df.where(
        pd.notna(peers_df),
        None,
    )

    peers = []

    for _, row in peers_df.iterrows():

        peers.append(
            {
                "company_id": row["company_id"],
                "company_name": row["company_name"],
                "broad_sector": row["broad_sector"],
                "year": row["year"],
                "return_on_equity_pct": row[
                    "return_on_equity_pct"
                ],
                "return_on_capital_employed_pct": row[
                    "return_on_capital_employed_pct"
                ],
                "net_profit_margin_pct": row[
                    "net_profit_margin_pct"
                ],
                "operating_profit_margin_pct": row[
                    "operating_profit_margin_pct"
                ],
                "debt_to_equity": row[
                    "debt_to_equity"
                ],
                "interest_coverage": row[
                    "interest_coverage"
                ],
                "asset_turnover": row[
                    "asset_turnover"
                ],
                "free_cash_flow_cr": row[
                    "free_cash_flow_cr"
                ],
                "earnings_per_share": row[
                    "earnings_per_share"
                ],
                "dividend_payout_ratio_pct": row[
                    "dividend_payout_ratio_pct"
                ],
            }
        )

    return {
        "company_id": company_id,
        "company_name": target_df.iloc[0]["company_name"],
        "broad_sector": target_sector,
        "count": len(peers),
        "peers": peers,
    }
# ============================================================
# PORTFOLIO STATISTICS
# ============================================================

@app.get("/portfolio/stats")
def get_portfolio_stats():
    """
    Return portfolio-level statistics for the Nifty100 universe.
    """

    conn = get_connection()

    try:

        # ----------------------------------------------------
        # Latest financial ratios per company
        # ----------------------------------------------------

        ratios_query = """
            SELECT *
            FROM financial_ratios
        """

        ratios = pd.read_sql(
            ratios_query,
            conn,
        )

        if not ratios.empty:

            ratios["_year_num"] = pd.to_numeric(
                ratios["year"],
                errors="coerce",
            )

            ratios = (
                ratios
                .sort_values(
                    ["company_id", "_year_num"]
                )
                .groupby(
                    "company_id",
                    as_index=False,
                )
                .tail(1)
            )

        # ----------------------------------------------------
        # Latest market-cap record per company
        # ----------------------------------------------------

        market_cap_query = """
            SELECT *
            FROM market_cap
        """

        market_cap = pd.read_sql(
            market_cap_query,
            conn,
        )

        if not market_cap.empty:

            market_cap["_year_num"] = pd.to_numeric(
                market_cap["year"],
                errors="coerce",
            )

            market_cap = (
                market_cap
                .sort_values(
                    ["company_id", "_year_num"]
                )
                .groupby(
                    "company_id",
                    as_index=False,
                )
                .tail(1)
            )

        # ----------------------------------------------------
        # Companies
        # ----------------------------------------------------

        companies = pd.read_sql(
            """
            SELECT
                id,
                company_name
            FROM companies
            """,
            conn,
        )

        # ----------------------------------------------------
        # Sectors
        # ----------------------------------------------------

        sectors = pd.read_sql(
            """
            SELECT
                company_id,
                broad_sector,
                market_cap_category
            FROM sectors
            """,
            conn,
        )

    finally:

        conn.close()

    # --------------------------------------------------------
    # Basic portfolio size
    # --------------------------------------------------------

    total_companies = len(companies)

    # --------------------------------------------------------
    # Financial statistics
    # --------------------------------------------------------

    def average(column):

        if column not in ratios.columns:
            return None

        value = pd.to_numeric(
            ratios[column],
            errors="coerce",
        ).mean()

        return (
            float(value)
            if pd.notna(value)
            else None
        )

    def total(column):

        if column not in ratios.columns:
            return None

        value = pd.to_numeric(
            ratios[column],
            errors="coerce",
        ).sum()

        return (
            float(value)
            if pd.notna(value)
            else None
        )

    # --------------------------------------------------------
    # Market-cap statistics
    # --------------------------------------------------------

    total_market_cap = None
    average_pe = None
    average_pb = None
    average_dividend_yield = None

    if not market_cap.empty:

        total_market_cap_value = pd.to_numeric(
            market_cap["market_cap_crore"],
            errors="coerce",
        ).sum()

        total_market_cap = (
            float(total_market_cap_value)
            if pd.notna(total_market_cap_value)
            else None
        )

        average_pe = (
            float(
                pd.to_numeric(
                    market_cap["pe_ratio"],
                    errors="coerce",
                ).mean()
            )
            if "pe_ratio" in market_cap.columns
            else None
        )

        average_pb = (
            float(
                pd.to_numeric(
                    market_cap["pb_ratio"],
                    errors="coerce",
                ).mean()
            )
            if "pb_ratio" in market_cap.columns
            else None
        )

        average_dividend_yield = (
            float(
                pd.to_numeric(
                    market_cap["dividend_yield_pct"],
                    errors="coerce",
                ).mean()
            )
            if "dividend_yield_pct" in market_cap.columns
            else None
        )

    # --------------------------------------------------------
    # Sector statistics
    # --------------------------------------------------------

    sector_count = int(
        sectors["broad_sector"]
        .dropna()
        .nunique()
    )

    # --------------------------------------------------------
    # Market-cap category breakdown
    # --------------------------------------------------------

    market_cap_breakdown = []

    if "market_cap_category" in sectors.columns:

        category_df = (
            sectors[
                sectors["market_cap_category"].notna()
            ]
            .groupby("market_cap_category")
            .size()
            .reset_index(name="company_count")
        )

        for _, row in category_df.iterrows():

            market_cap_breakdown.append(
                {
                    "market_cap_category": row[
                        "market_cap_category"
                    ],
                    "company_count": int(
                        row["company_count"]
                    ),
                }
            )

    # --------------------------------------------------------
    # Sector breakdown
    # --------------------------------------------------------

    sector_breakdown = []

    sector_df = (
        sectors[
            sectors["broad_sector"].notna()
        ]
        .groupby("broad_sector")
        .size()
        .reset_index(name="company_count")
        .sort_values(
            "company_count",
            ascending=False,
        )
    )

    for _, row in sector_df.iterrows():

        sector_breakdown.append(
            {
                "broad_sector": row[
                    "broad_sector"
                ],
                "company_count": int(
                    row["company_count"]
                ),
            }
        )

    # --------------------------------------------------------
    # Final response
    # --------------------------------------------------------

    return {
        "portfolio": "Nifty100",
        "total_companies": total_companies,
        "total_market_cap_crore": total_market_cap,
        "average_pe_ratio": average_pe,
        "average_pb_ratio": average_pb,
        "average_dividend_yield_pct": average_dividend_yield,
        "average_roe_pct": average(
            "return_on_equity_pct"
        ),
        "average_roce_pct": average(
            "return_on_capital_employed_pct"
        ),
        "average_debt_to_equity": average(
            "debt_to_equity"
        ),
        "total_free_cash_flow_cr": total(
            "free_cash_flow_cr"
        ),
        "sector_count": sector_count,
        "market_cap_breakdown": market_cap_breakdown,
        "sector_breakdown": sector_breakdown,
    }
# ============================================================
# HISTORICAL STOCK PRICES
# ============================================================

@app.get("/companies/{company_id}/prices")
def get_company_prices(
    company_id: str,
    limit: int = 60,
    offset: int = 0,
):
    """
    Return historical stock prices for a company.
    """

    company_id = company_id.upper().strip()

    if limit < 1:
        limit = 1

    if limit > 1000:
        limit = 1000

    if offset < 0:
        offset = 0

    conn = get_connection()

    try:

        # ----------------------------------------------------
        # Verify company
        # ----------------------------------------------------

        company = pd.read_sql(
            """
            SELECT
                id,
                company_name
            FROM companies
            WHERE id = ?
            """,
            conn,
            params=(company_id,),
        )

        if company.empty:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "Company not found",
                    "company_id": company_id,
                },
            )

        # ----------------------------------------------------
        # Get total price records
        # ----------------------------------------------------

        total_query = """
            SELECT COUNT(*)
            FROM stock_prices
            WHERE company_id = ?
        """

        cursor = conn.cursor()

        cursor.execute(
            total_query,
            (company_id,),
        )

        total = cursor.fetchone()[0]

        # ----------------------------------------------------
        # Get historical prices
        # ----------------------------------------------------

        prices_query = """
            SELECT
                date,
                open_price,
                high_price,
                low_price,
                close_price,
                volume,
                adjusted_close
            FROM stock_prices
            WHERE company_id = ?
            ORDER BY date DESC
            LIMIT ? OFFSET ?
        """

        prices_df = pd.read_sql(
            prices_query,
            conn,
            params=(
                company_id,
                limit,
                offset,
            ),
        )

    finally:

        conn.close()

    # --------------------------------------------------------
    # Convert NaN to None
    # --------------------------------------------------------

    prices_df = prices_df.where(
        pd.notna(prices_df),
        None,
    )

    prices = []

    for _, row in prices_df.iterrows():

        prices.append(
            {
                "date": row["date"],
                "open_price": row["open_price"],
                "high_price": row["high_price"],
                "low_price": row["low_price"],
                "close_price": row["close_price"],
                "volume": row["volume"],
                "adjusted_close": row[
                    "adjusted_close"
                ],
            }
        )

    return {
        "company_id": company_id,
        "company_name": company.iloc[0]["company_name"],
        "total": total,
        "limit": limit,
        "offset": offset,
        "count": len(prices),
        "prices": prices,
    }
# ============================================================
# COMPANY PERFORMANCE
# ============================================================

@app.get("/companies/{company_id}/performance")
def get_company_performance(company_id: str):

    company_id = company_id.upper().strip()

    conn = get_connection()

    try:
        company = pd.read_sql(
            """
            SELECT id, company_name
            FROM companies
            WHERE id = ?
            """,
            conn,
            params=(company_id,),
        )

        prices = pd.read_sql(
            """
            SELECT
                date,
                close_price
            FROM stock_prices
            WHERE company_id = ?
            ORDER BY date ASC
            """,
            conn,
            params=(company_id,),
        )

    finally:
        conn.close()

    # --------------------------------------------------------
    # Company validation
    # --------------------------------------------------------

    if company.empty:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "Company not found",
                "company_id": company_id,
            },
        )

    # --------------------------------------------------------
    # Price validation
    # --------------------------------------------------------

    if prices.empty:
        return {
            "company_id": company_id,
            "company_name": company.iloc[0]["company_name"],
            "message": "No historical price data available",
            "count": 0,
        }

    # --------------------------------------------------------
    # Calculate performance
    # --------------------------------------------------------

    start_price = float(prices.iloc[0]["close_price"])
    end_price = float(prices.iloc[-1]["close_price"])

    total_return_pct = (
        (end_price - start_price)
        / start_price
    ) * 100

    start_date = prices.iloc[0]["date"]
    end_date = prices.iloc[-1]["date"]

    # --------------------------------------------------------
    # Annualized return
    # --------------------------------------------------------

    start = pd.to_datetime(start_date)
    end = pd.to_datetime(end_date)

    years = (end - start).days / 365.25

    if years > 0:
        annualized_return_pct = (
            ((end_price / start_price) ** (1 / years))
            - 1
        ) * 100
    else:
        annualized_return_pct = 0

    return {
        "company_id": company_id,
        "company_name": company.iloc[0]["company_name"],
        "start_date": start_date,
        "end_date": end_date,
        "start_price": start_price,
        "end_price": end_price,
        "total_return_pct": total_return_pct,
        "annualized_return_pct": annualized_return_pct,
        "price_records": len(prices),
    }
