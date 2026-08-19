import sqlite3
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, HTTPException

from src.screener.presets import (
    debt_free_bluechip,
    dividend_champion,
    growth_accelerator,
    quality_compounder,
    turnaround_watch,
    value_pick,
)

router = APIRouter(
    prefix="/screener",
    tags=["Screener"],
)

BASE_DIR = Path(__file__).resolve().parents[3]
DB_PATH = BASE_DIR / "data" / "database" / "nifty100.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


SCREENER_PRESETS = {
    "quality_compounder": quality_compounder,
    "value_pick": value_pick,
    "growth_accelerator": growth_accelerator,
    "dividend_champion": dividend_champion,
    "debt_free_bluechip": debt_free_bluechip,
    "turnaround_watch": turnaround_watch,
}


@router.get("/{preset}")
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

    limit = max(limit, 1)
    limit = min(limit, 100)

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

    if ratios.empty:
        return {
            "preset": preset,
            "count": 0,
            "results": [],
        }

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

    result = result.head(limit)

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
