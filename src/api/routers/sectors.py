import sqlite3
from pathlib import Path

from fastapi import APIRouter

router = APIRouter(
    prefix="/sectors",
    tags=["Sectors"],
)

BASE_DIR = Path(__file__).resolve().parents[3]
DB_PATH = BASE_DIR / "data" / "database" / "nifty100.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


@router.get("")
def get_sectors():
    """
    Return sector-level summary for the Nifty100 universe.
    """

    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                broad_sector,
                COUNT(*) AS company_count,
                SUM(index_weight_pct) AS total_index_weight_pct
            FROM sectors
            WHERE broad_sector IS NOT NULL
            GROUP BY broad_sector
            ORDER BY total_index_weight_pct DESC
            """
        )

        rows = cursor.fetchall()

    finally:
        conn.close()

    sectors = [
        {
            "broad_sector": row[0],
            "company_count": int(row[1]),
            "total_index_weight_pct": (
                float(row[2])
                if row[2] is not None
                else None
            ),
        }
        for row in rows
    ]

    return {
        "count": len(sectors),
        "sectors": sectors,
    }
