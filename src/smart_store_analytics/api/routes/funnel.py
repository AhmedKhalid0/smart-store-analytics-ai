"""API routes for Shopper Flow, Zone Transitions, and Retail Conversion Funnels."""

from typing import List
from fastapi import APIRouter, Request, status

from smart_store_analytics.core.funnel import (
    ShopperFunnelEngine,
    ShopperFunnelReport,
    ZoneTransition,
)
from smart_store_analytics.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/funnel", tags=["Conversion Funnel & Flow"])


def get_funnel_engine(request: Request) -> ShopperFunnelEngine:
    """Lazily retrieves or initializes the ShopperFunnelEngine."""
    if not hasattr(request.app.state, "funnel_engine") or request.app.state.funnel_engine is None:
        spatial_engine = getattr(request.app.state, "spatial_engine", None)
        if spatial_engine is None and hasattr(request.app.state, "processor"):
            spatial_engine = request.app.state.processor.spatial_engine
        request.app.state.funnel_engine = ShopperFunnelEngine(spatial_engine=spatial_engine)
    return request.app.state.funnel_engine


@router.get("/report", response_model=ShopperFunnelReport, status_code=status.HTTP_200_OK)
async def get_funnel_report(request: Request) -> ShopperFunnelReport:
    """Returns multi-stage conversion funnel, drop-off percentages, and leakage metrics."""
    engine = get_funnel_engine(request)
    return engine.generate_funnel_report()


@router.get("/transitions", response_model=List[ZoneTransition], status_code=status.HTTP_200_OK)
async def get_zone_transitions(request: Request) -> List[ZoneTransition]:
    """Returns top customer migration flows and probability shares between store zones."""
    engine = get_funnel_engine(request)
    report = engine.generate_funnel_report()
    return report.top_transitions
