from src.api.routers.health import router as health_router
from src.api.routers.valuation import router as valuation_router
from src.api.routers.documents import router as documents_router
from src.api.routers.companies import router as companies_router
from src.api.routers.sectors import router as sectors_router
from src.api.routers.screener import router as screener_router


def register_routers(app):
    app.include_router(health_router)
    app.include_router(valuation_router)
    app.include_router(documents_router)
    app.include_router(companies_router)
    app.include_router(sectors_router)
    app.include_router(screener_router)
