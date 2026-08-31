"""Health and vision telemetry routes."""

from fastapi import APIRouter, Request
from smart_store_analytics import __version__
from smart_store_analytics.api.schemas import HealthResponse
from smart_store_analytics.core.spatial_analytics import SpatialAnalyticsEngine

router = APIRouter(prefix="/api/v1", tags=["Health & Vision Telemetry"])


@router.get("/health", response_model=HealthResponse)
async def get_health(request: Request) -> HealthResponse:
    """Returns application status and vision model configuration."""
    settings = request.app.state.settings
    spatial_engine: SpatialAnalyticsEngine = request.app.state.spatial_engine

    return HealthResponse(
        status="healthy",
        version=__version__,
        environment=settings.app_env,
        detector_model=settings.detector_model,
        tracking_algorithm="ByteTrack / IoU Centroid Proximity",
        zones_configured=len(spatial_engine.zones),
    )
