import sqlite3
from pathlib import Path

from fastapi import APIRouter, HTTPException

router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)

BASE_DIR = Path(__file__).resolve().parents[3]

DB_PATH = BASE_DIR / "data" / "database" / "nifty100.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


@router.get("")
def get_documents(
    limit: int = 20,
    offset: int = 0,
):
    limit = max(1, min(limit, 100))
    offset = max(0, offset)

    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                id,
                company_id,
                year,
                annual_report
            FROM documents
            ORDER BY company_id, year DESC
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        )

        rows = cursor.fetchall()

        cursor.execute(
            "SELECT COUNT(*) FROM documents"
        )

        total = cursor.fetchone()[0]

    finally:
        conn.close()

    documents = [
        {
            "id": row[0],
            "company_id": row[1],
            "year": row[2],
            "annual_report": row[3],
        }
        for row in rows
    ]

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "count": len(documents),
        "documents": documents,
    }


@router.get("/{company_id}")
def get_company_documents(
    company_id: str,
    limit: int = 20,
):
    company_id = company_id.upper().strip()
    limit = max(1, min(limit, 100))

    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                id,
                company_id,
                year,
                annual_report
            FROM documents
            WHERE company_id = ?
            ORDER BY year DESC
            LIMIT ?
            """,
            (company_id, limit),
        )

        rows = cursor.fetchall()

    finally:
        conn.close()

    if not rows:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "No documents found",
                "company_id": company_id,
            },
        )

    documents = [
        {
            "id": row[0],
            "company_id": row[1],
            "year": row[2],
            "annual_report": row[3],
        }
        for row in rows
    ]

    return {
        "company_id": company_id,
        "count": len(documents),
        "documents": documents,
    }
