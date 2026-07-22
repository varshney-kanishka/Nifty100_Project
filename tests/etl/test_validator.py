import sys
from pathlib import Path

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT_DIR / "src"))

from etl.validator import validate_companies, validate_financial_table


def test_validate_companies_missing_id():
    df = pd.DataFrame({"company_name": ["A Company"]})

    results = validate_companies(df, "companies.csv")

    assert len(results) == 1
    assert results[0]["rule"] == "DQ-01"
    assert "missing required column" in results[0]["message"].lower()


def test_validate_companies_duplicate_id():
    df = pd.DataFrame(
        {
            "id": ["ABC", "ABC"],
            "company_name": ["A Company", "A Different Company"],
        }
    )

    results = validate_companies(df, "companies.csv")

    assert len(results) == 1
    assert results[0]["rule"] == "DQ-01"
    assert "duplicate" in results[0]["message"].lower()


def test_validate_financial_table_missing_columns():
    df = pd.DataFrame({"company_id": ["ABC"]})

    results = validate_financial_table(df, "balancesheet.csv")

    assert len(results) == 1
    assert results[0]["rule"] == "DQ-02"
    assert "year" in results[0]["message"].lower()


def test_validate_financial_table_duplicate_company_year():
    df = pd.DataFrame(
        {
            "company_id": ["ABC", "ABC"],
            "year": [2022, 2022],
        }
    )

    results = validate_financial_table(df, "balancesheet.csv")

    assert len(results) == 1
    assert results[0]["rule"] == "DQ-02"
    assert "duplicate" in results[0]["message"].lower()


def test_validate_financial_table_no_issues():
    df = pd.DataFrame(
        {
            "company_id": ["ABC", "DEF"],
            "year": [2022, 2023],
        }
    )

    results = validate_financial_table(df, "balancesheet.csv")

    assert results == []
