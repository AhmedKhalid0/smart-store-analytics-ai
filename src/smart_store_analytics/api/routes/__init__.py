"""Route router exports for FastAPI application."""

from smart_store_analytics.api.routes.health import router as health_router
from smart_store_analytics.api.routes.analytics import router as analytics_router
from smart_store_analytics.api.routes.heatmap import router as heatmap_router

__all__ = ["health_router", "analytics_router", "heatmap_router"]
