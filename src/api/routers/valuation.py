from pathlib import Path

import pandas as pd
from fastapi import APIRouter, HTTPException

router = APIRouter(
    prefix="/valuation",
    tags=["Valuation"],
)

BASE_DIR = Path(__file__).resolve().parents[3]

SUMMARY_FILE = BASE_DIR / "output" / "valuation_summary.xlsx"
FLAGS_FILE = BASE_DIR / "output" / "valuation_flags.csv"


def clean_dataframe(df):
    """
    Convert pandas NaN/NaT values to JSON-safe None.
    """
    return df.astype(object).where(pd.notna(df), None)


def load_valuation():
    if not SUMMARY_FILE.exists():
        raise HTTPException(
            status_code=500,
            detail="valuation_summary.xlsx not found",
        )

    return pd.read_excel(SUMMARY_FILE)


@router.get("")
def valuation_summary():
    df = load_valuation()
    df = clean_dataframe(df)

    return {
        "count": len(df),
        "companies": df.to_dict(orient="records"),
    }


@router.get("/flags")
def valuation_flags():
    if not FLAGS_FILE.exists():
        raise HTTPException(
            status_code=500,
            detail="valuation_flags.csv not found",
        )

    df = pd.read_csv(FLAGS_FILE)
    df = clean_dataframe(df)

    return {
        "count": len(df),
        "flags": df.to_dict(orient="records"),
    }
