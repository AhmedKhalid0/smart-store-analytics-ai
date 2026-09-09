"""Video stream processing orchestrator integrating detector, tracker, and analytics."""

import time
from typing import Callable, Dict, List, Optional
from pydantic import BaseModel, Field

from smart_store_analytics.core.detector import Detection, SyntheticVideoSequenceGenerator
from smart_store_analytics.core.heatmap_generator import SpatialHeatmapGenerator
from smart_store_analytics.core.queue_monitor import QueueAnomalyAlert, QueueMonitor
from smart_store_analytics.core.spatial_analytics import SpatialAnalyticsEngine
from smart_store_analytics.core.tracking_engine import MultiObjectTracker, TrackedPerson
from smart_store_analytics.utils.logger import get_logger

logger = get_logger(__name__)


class VideoAnalyticsSummary(BaseModel):
    """Complete intelligence summary extracted from video sequence."""

    total_frames_processed: int
    duration_seconds: float
    total_footfall: int
    active_shoppers: int
    zone_metrics: Dict[str, dict]
    queue_alerts: List[QueueAnomalyAlert]
    active_trajectories: List[dict] = Field(default_factory=list)


class VideoProcessor:
    """End-to-end vision pipeline processing video frames and extracting retail KPIs."""

    def __init__(
        self,
        tracker: Optional[MultiObjectTracker] = None,
        spatial_engine: Optional[SpatialAnalyticsEngine] = None,
        heatmap_gen: Optional[SpatialHeatmapGenerator] = None,
        queue_monitor: Optional[QueueMonitor] = None,
        fps: float = 30.0,
    ) -> None:
        self.fps = fps
        self.tracker = tracker or MultiObjectTracker()
        self.spatial_engine = spatial_engine or SpatialAnalyticsEngine(fps=fps)
        self.heatmap_gen = heatmap_gen or SpatialHeatmapGenerator()
        self.queue_monitor = queue_monitor or QueueMonitor()

    def process_synthetic_simulation(
        self,
        num_frames: int = 100,
        on_frame_callback: Optional[Callable[[int, List[TrackedPerson]], None]] = None,
    ) -> VideoAnalyticsSummary:
        """Runs retail analytics simulation across multi-customer synthetic trajectories."""
        start_t = time.time()
        gen = SyntheticVideoSequenceGenerator(total_frames=num_frames)

        for frame_idx in range(num_frames):
            # 1. Detection
            detections = gen.get_detections_for_frame(frame_idx)

            # 2. Tracking
            active_tracks = self.tracker.update(detections, frame_idx)

            # 3. Spatial Zones & Dwell
            self.spatial_engine.update(active_tracks, frame_idx)

            # 4. Heatmap Accumulation
            for track in active_tracks:
                cx, cy = track.centroid
                self.heatmap_gen.add_point(cx, cy)

            # 5. Queue Anomaly Check (every 10 frames)
            if frame_idx % 10 == 0:
                self.queue_monitor.check_queue_health(self.spatial_engine)

            if on_frame_callback:
                on_frame_callback(frame_idx, active_tracks)

        elapsed = time.time() - start_t
        zone_metrics = self.spatial_engine.get_zone_analytics()
        active_tracks = [t for t in self.tracker.tracks.values() if t.state.value == "confirmed"]

        trajectories = [
            {"track_id": t.track_id, "points": t.trajectory[-15:], "current_pos": t.centroid}
            for t in active_tracks
        ]

        logger.info(
            f"Processed {num_frames} frames in {elapsed:.2f}s "
            f"(Total Footfall: {self.spatial_engine.total_footfall})"
        )

        return VideoAnalyticsSummary(
            total_frames_processed=num_frames,
            duration_seconds=round(num_frames / self.fps, 2),
            total_footfall=self.spatial_engine.total_footfall,
            active_shoppers=len(active_tracks),
            zone_metrics=zone_metrics,
            queue_alerts=self.queue_monitor.alert_history,
            active_trajectories=trajectories,
        )

    def get_analytics_summary(self) -> VideoAnalyticsSummary:
        """Returns the current snapshot analytics summary without running a new simulation."""
        zone_metrics = self.spatial_engine.get_zone_analytics()
        active_tracks = [t for t in self.tracker.tracks.values() if t.state.value == "confirmed"]
        trajectories = [
            {"track_id": t.track_id, "points": t.trajectory[-15:], "current_pos": t.centroid}
            for t in active_tracks
        ]
        return VideoAnalyticsSummary(
            total_frames_processed=120,
            duration_seconds=round(120 / self.fps, 2),
            total_footfall=self.spatial_engine.total_footfall,
            active_shoppers=len(active_tracks),
            zone_metrics=zone_metrics,
            queue_alerts=self.queue_monitor.alert_history,
            active_trajectories=trajectories,
        )
