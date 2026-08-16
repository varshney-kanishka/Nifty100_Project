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