import sqlite3
from pathlib import Path

from fastapi import APIRouter, HTTPException

router = APIRouter(
    prefix="/companies",
    tags=["Companies"],
)

BASE_DIR = Path(__file__).resolve().parents[3]
DB_PATH = BASE_DIR / "data" / "database" / "nifty100.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


@router.get("")
def get_companies(
    limit: int = 20,
    offset: int = 0,
):
    """
    Return a paginated list of Nifty100 companies.
    """

    limit = max(limit, 1)
    limit = min(limit, 100)
    offset = max(offset, 0)

    conn = get_connection()

    try:
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

        cursor.execute(
            "SELECT COUNT(*) FROM companies"
        )

        total = cursor.fetchone()[0]

    finally:
        conn.close()

    companies = [
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
        for row in rows
    ]

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "count": len(companies),
        "companies": companies,
    }


@router.get("/{company_id}")
def get_company(company_id: str):
    """
    Return detailed information for a single Nifty100 company.
    """

    company_id = company_id.upper().strip()

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
            (company_id,),
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
