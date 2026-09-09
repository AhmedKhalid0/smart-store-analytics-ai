"""Retail spatial analytics, footfall, and queue KPI endpoints."""

from fastapi import APIRouter, Request, status

from smart_store_analytics.api.schemas import (
    AnalyticsResponse,
    QueueAlertSchema,
    TrajectoryPointSchema,
    ZoneMetricSchema,
)
from smart_store_analytics.core.video_processor import VideoProcessor

router = APIRouter(prefix="/api/v1/analytics", tags=["Retail Analytics"])


@router.get("/stats", response_model=AnalyticsResponse, status_code=status.HTTP_200_OK)
async def get_analytics_stats(request: Request) -> AnalyticsResponse:
    """Returns real-time footfall, zone dwell-times, and queue bottleneck alerts."""
    processor: VideoProcessor = request.app.state.processor

    # Ensure some frames are simulated if empty
    if processor.spatial_engine.total_footfall == 0:
        processor.process_synthetic_simulation(num_frames=60)

    zone_stats = processor.spatial_engine.get_zone_analytics()
    zones_schema = [ZoneMetricSchema(**z) for z in zone_stats.values()]

    alerts_schema = [
        QueueAlertSchema(
            alert_id=a.alert_id,
            zone_id=a.zone_id,
            timestamp=a.timestamp,
            current_queue_length=a.current_queue_length,
            avg_wait_seconds=a.avg_wait_seconds,
            severity=a.severity,
            recommendation=a.recommendation,
        )
        for a in processor.queue_monitor.alert_history
    ]

    active_tracks = [t for t in processor.tracker.tracks.values() if t.state.value == "confirmed"]
    trajectories_schema = [
        TrajectoryPointSchema(
            track_id=t.track_id,
            points=t.trajectory[-15:],
            current_pos=t.centroid,
        )
        for t in active_tracks
    ]

    current_frame = 120
    if hasattr(request.app.state, "stream_manager") and request.app.state.stream_manager is not None:
        current_frame = request.app.state.stream_manager.current_frame or 120

    return AnalyticsResponse(
        total_footfall=processor.spatial_engine.total_footfall,
        active_shoppers=len(active_tracks),
        total_frames_processed=current_frame,
        zones=zones_schema,
        queue_alerts=alerts_schema,
        trajectories=trajectories_schema,
    )


@router.post("/simulate", response_model=AnalyticsResponse)
async def trigger_simulation(request: Request) -> AnalyticsResponse:
    """Runs a fresh retail video stream simulation."""
    processor: VideoProcessor = request.app.state.processor
    if hasattr(request.app.state, "stream_manager") and request.app.state.stream_manager is not None:
        for _ in range(5):
            request.app.state.stream_manager.step()
    processor.process_synthetic_simulation(num_frames=80)
    return await get_analytics_stats(request)
