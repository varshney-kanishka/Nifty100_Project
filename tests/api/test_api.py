from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


# ============================================================
# ROOT / HEALTH
# ============================================================

def test_root():
    response = client.get("/")

    assert response.status_code == 200

    data = response.json()

    assert data["message"] == "Nifty100 Analytics API"
    assert data["status"] == "running"
    assert data["version"] == "1.0.0"


def test_health():
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "healthy"


def test_database_health():
    response = client.get("/health/database")

    assert response.status_code == 200

    data = response.json()

    assert data["database"] == "connected"
    assert data["companies"] > 0


# ============================================================
# COMPANIES
# ============================================================

def test_get_companies():
    response = client.get("/companies")

    assert response.status_code == 200

    data = response.json()

    assert "total" in data
    assert "companies" in data
    assert data["total"] > 0
    assert len(data["companies"]) > 0


def test_get_companies_pagination():
    response = client.get("/companies?limit=5&offset=0")

    assert response.status_code == 200

    data = response.json()

    assert data["limit"] == 5
    assert data["offset"] == 0
    assert data["count"] <= 5


def test_get_company():
    response = client.get("/companies/RELIANCE")

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == "RELIANCE"
    assert "company_name" in data


def test_get_company_not_found():
    response = client.get("/companies/INVALID_COMPANY")

    assert response.status_code == 404


# ============================================================
# SECTORS
# ============================================================

def test_get_sectors():
    response = client.get("/sectors")

    assert response.status_code == 200

    data = response.json()

    assert "count" in data
    assert "sectors" in data
    assert data["count"] > 0


# ============================================================
# SCREENER
# ============================================================

def test_quality_compounder_screener():
    response = client.get(
        "/screener/quality_compounder"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["preset"] == "quality_compounder"
    assert "results" in data
    assert data["count"] <= 20


def test_value_pick_screener():
    response = client.get(
        "/screener/value_pick"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["preset"] == "value_pick"


def test_invalid_screener():
    response = client.get(
        "/screener/invalid_preset"
    )

    assert response.status_code == 404


# ============================================================
# MARKET CAP
# ============================================================

def test_market_cap():
    response = client.get("/market-cap")

    assert response.status_code == 200

    data = response.json()

    assert "count" in data
    assert "market_cap" in data
    assert data["count"] > 0


# ============================================================
# PEERS
# ============================================================

def test_get_peers():
    response = client.get(
        "/peers/RELIANCE"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["company_id"] == "RELIANCE"
    assert "broad_sector" in data
    assert "peers" in data


def test_get_peers_not_found():
    response = client.get(
        "/peers/INVALID_COMPANY"
    )

    assert response.status_code == 404


# ============================================================
# PORTFOLIO STATISTICS
# ============================================================

def test_portfolio_stats():
    response = client.get(
        "/portfolio/stats"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["portfolio"] == "Nifty100"
    assert data["total_companies"] > 0
    assert data["sector_count"] > 0
    assert "sector_breakdown" in data
    assert "market_cap_breakdown" in data


# ============================================================
# STOCK PRICES
# ============================================================

def test_company_prices():
    response = client.get(
        "/companies/RELIANCE/prices"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["company_id"] == "RELIANCE"
    assert "prices" in data
    assert "total" in data


def test_company_prices_not_found():
    response = client.get(
        "/companies/INVALID_COMPANY/prices"
    )

    assert response.status_code == 404


# ============================================================
# COMPANY PERFORMANCE
# ============================================================

def test_company_performance():
    response = client.get(
        "/companies/RELIANCE/performance"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["company_id"] == "RELIANCE"

    if "count" in data and data["count"] > 0:
        assert "total_return_pct" in data
        assert "annualized_return_pct" in data


def test_company_performance_not_found():
    response = client.get(
        "/companies/INVALID_COMPANY/performance"
    )

    assert response.status_code == 404
# ============================================================
# ADDITIONAL API COVERAGE
# ============================================================

def test_get_companies_limit_capped():
    response = client.get("/companies?limit=500")

    assert response.status_code == 200

    data = response.json()

    assert data["limit"] == 100
    assert data["count"] <= 100


def test_get_companies_negative_offset():
    response = client.get("/companies?limit=5&offset=-10")

    assert response.status_code == 200

    data = response.json()

    assert data["offset"] == 0
    assert data["count"] <= 5


def test_get_company_case_insensitive():
    response = client.get("/companies/reliance")

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == "RELIANCE"


def test_growth_accelerator_screener():
    response = client.get("/screener/growth_accelerator")

    assert response.status_code == 200

    data = response.json()

    assert data["preset"] == "growth_accelerator"
    assert "results" in data
    assert data["count"] <= 20


def test_dividend_champion_screener():
    response = client.get("/screener/dividend_champion")

    assert response.status_code == 200

    data = response.json()

    assert data["preset"] == "dividend_champion"
    assert "results" in data


def test_peers_case_insensitive():
    response = client.get("/peers/reliance")

    assert response.status_code == 200

    data = response.json()

    assert data["company_id"] == "RELIANCE"
    assert "peers" in data


def test_company_prices_case_insensitive():
    response = client.get("/companies/reliance/prices")

    assert response.status_code == 200

    data = response.json()

    assert data["company_id"] == "RELIANCE"
    assert "prices" in data


def test_company_performance_case_insensitive():
    response = client.get("/companies/reliance/performance")

    assert response.status_code == 200

    data = response.json()

    assert data["company_id"] == "RELIANCE"
    assert "start_date" in data
    assert "end_date" in data
# ============================================================
# VALUATION ROUTES
# ============================================================

def test_valuation_summary():
    response = client.get("/valuation")

    assert response.status_code == 200

    data = response.json()

    assert data["count"] == 92
    assert "companies" in data
    assert len(data["companies"]) > 0


def test_valuation_flags():
    response = client.get("/valuation/flags")

    assert response.status_code == 200

    data = response.json()

    assert "count" in data
    assert "flags" in data


# ============================================================
# DOCUMENT ROUTES
# ============================================================

def test_documents():
    response = client.get("/documents")

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1456
    assert "documents" in data
    assert len(data["documents"]) > 0


def test_documents_pagination():
    response = client.get("/documents?limit=5&offset=0")

    assert response.status_code == 200

    data = response.json()

    assert data["limit"] == 5
    assert data["offset"] == 0
    assert data["count"] <= 5


def test_company_documents():
    response = client.get("/documents/RELIANCE")

    assert response.status_code == 200

    data = response.json()

    assert data["company_id"] == "RELIANCE"
    assert "documents" in data
    assert data["count"] > 0


def test_company_documents_case_insensitive():
    response = client.get("/documents/reliance")

    assert response.status_code == 200

    data = response.json()

    assert data["company_id"] == "RELIANCE"


def test_company_documents_not_found():
    response = client.get(
        "/documents/INVALID_COMPANY"
    )

    assert response.status_code == 404
