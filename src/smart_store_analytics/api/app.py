"""FastAPI application factory and static web dashboard mounting."""

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from smart_store_analytics import __version__
from smart_store_analytics.api.routes.analytics import router as analytics_router
from smart_store_analytics.api.routes.health import router as health_router
from smart_store_analytics.api.routes.heatmap import router as heatmap_router
from smart_store_analytics.core.heatmap_generator import SpatialHeatmapGenerator
from smart_store_analytics.core.queue_monitor import QueueMonitor
from smart_store_analytics.core.spatial_analytics import SpatialAnalyticsEngine
from smart_store_analytics.core.tracking_engine import MultiObjectTracker
from smart_store_analytics.core.video_processor import VideoProcessor
from smart_store_analytics.utils.config import Settings, get_settings
from smart_store_analytics.utils.logger import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup lifecycle."""
    logger.info("Initializing Smart-Store-Analytics vision engine...")
    settings = get_settings()
    settings.ensure_directories()

    if not hasattr(app.state, "tracker") or app.state.tracker is None:
        app.state.tracker = MultiObjectTracker(
            iou_threshold=settings.tracking_iou_threshold,
            max_age_frames=settings.tracking_max_age_frames,
        )
    if not hasattr(app.state, "spatial_engine") or app.state.spatial_engine is None:
        app.state.spatial_engine = SpatialAnalyticsEngine()
    if not hasattr(app.state, "heatmap_gen") or app.state.heatmap_gen is None:
        app.state.heatmap_gen = SpatialHeatmapGenerator()
    if not hasattr(app.state, "queue_monitor") or app.state.queue_monitor is None:
        app.state.queue_monitor = QueueMonitor(
            max_length_threshold=settings.max_queue_length_threshold,
            max_wait_seconds=settings.max_queue_wait_seconds,
        )
    if not hasattr(app.state, "processor") or app.state.processor is None:
        app.state.processor = VideoProcessor(
            tracker=app.state.tracker,
            spatial_engine=app.state.spatial_engine,
            heatmap_gen=app.state.heatmap_gen,
            queue_monitor=app.state.queue_monitor,
        )
        # Pre-seed initial simulation
        app.state.processor.process_synthetic_simulation(num_frames=60)

    logger.info(f"Smart-Store-Analytics v{__version__} ready on {settings.host}:{settings.port}")
    yield
    logger.info("Shutting down Smart-Store-Analytics engine...")


def create_app(
    settings: Optional[Settings] = None,
    processor: Optional[VideoProcessor] = None,
    spatial_engine: Optional[SpatialAnalyticsEngine] = None,
    heatmap_gen: Optional[SpatialHeatmapGenerator] = None,
) -> FastAPI:
    """Creates configured FastAPI dashboard instance."""
    app_settings = settings or get_settings()

    app = FastAPI(
        title="Smart-Store-Analytics API",
        description="Computer Vision & Retail Spatial Intelligence Engine",
        version=__version__,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    app.state.settings = app_settings
    if spatial_engine:
        app.state.spatial_engine = spatial_engine
    if heatmap_gen:
        app.state.heatmap_gen = heatmap_gen
    if processor:
        app.state.processor = processor

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount API routers
    app.include_router(health_router)
    app.include_router(analytics_router)
    app.include_router(heatmap_router)

    # Static assets and template rendering
    web_dir = Path(__file__).parent.parent / "web"
    static_dir = web_dir / "static"
    templates_dir = web_dir / "templates"

    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    templates = Jinja2Templates(directory=str(templates_dir)) if templates_dir.exists() else None

    @app.get("/", response_class=HTMLResponse, include_in_schema=False)
    async def render_dashboard(request: Request):
        if templates:
            return templates.TemplateResponse(
                request=request,
                name="index.html",
                context={
                    "title": "Smart-Store-Analytics | Vision AI & Retail Intelligence",
                    "version": __version__,
                },
            )
        return HTMLResponse("<h1>Smart-Store-Analytics API Active</h1><p>Visit <a href='/docs'>/docs</a></p>")

    return app
