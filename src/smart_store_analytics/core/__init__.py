"""Core computer vision, tracking, and spatial analytics engine."""

from smart_store_analytics.core.detector import Detection, SyntheticVideoSequenceGenerator
from smart_store_analytics.core.tracking_engine import MultiObjectTracker, TrackedPerson, TrackState
from smart_store_analytics.core.spatial_analytics import SpatialAnalyticsEngine, StoreZone, ZoneDwellEvent
from smart_store_analytics.core.heatmap_generator import SpatialHeatmapGenerator
from smart_store_analytics.core.queue_monitor import QueueMonitor, QueueAnomalyAlert
from smart_store_analytics.core.video_processor import VideoProcessor, VideoAnalyticsSummary

__all__ = [
    "Detection",
    "SyntheticVideoSequenceGenerator",
    "MultiObjectTracker",
    "TrackedPerson",
    "TrackState",
    "SpatialAnalyticsEngine",
    "StoreZone",
    "ZoneDwellEvent",
    "SpatialHeatmapGenerator",
    "QueueMonitor",
    "QueueAnomalyAlert",
    "VideoProcessor",
    "VideoAnalyticsSummary",
]
