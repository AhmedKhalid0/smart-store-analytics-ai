"""Pydantic request and response schemas for REST endpoints."""

from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str
    detector_model: str
    tracking_algorithm: str
    zones_configured: int


class ZoneMetricSchema(BaseModel):
    id: str
    name: str
    polygon: List[Tuple[float, float]] = Field(default_factory=list)
    color_hex: str
    category: str
    total_visits: int
    avg_dwell_seconds: float
    current_occupants: int


class QueueAlertSchema(BaseModel):
    alert_id: str
    zone_id: str
    timestamp: str
    current_queue_length: int
    avg_wait_seconds: float
    severity: str
    recommendation: str


class TrajectoryPointSchema(BaseModel):
    track_id: int
    points: List[Tuple[float, float]]
    current_pos: Tuple[float, float]


class AnalyticsResponse(BaseModel):
    total_footfall: int
    active_shoppers: int
    total_frames_processed: int
    zones: List[ZoneMetricSchema]
    queue_alerts: List[QueueAlertSchema]
    trajectories: List[TrajectoryPointSchema]


class HeatmapResponse(BaseModel):
    grid_width: int
    grid_height: int
    matrix: List[List[float]]
