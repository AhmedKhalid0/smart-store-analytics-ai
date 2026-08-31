"""Checkout Queue monitoring and bottleneck anomaly alert engine."""

from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field

from smart_store_analytics.core.spatial_analytics import SpatialAnalyticsEngine
from smart_store_analytics.utils.logger import get_logger

logger = get_logger(__name__)


class QueueAnomalyAlert(BaseModel):
    """Encapsulates a queue bottleneck SLA violation event."""

    alert_id: str
    zone_id: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).strftime("%H:%M:%S"))
    current_queue_length: int
    avg_wait_seconds: float
    severity: str = "WARNING"  # WARNING | CRITICAL
    recommendation: str


class QueueMonitor:
    """Detects checkout line congestion and wait-time bottlenecks in commercial areas."""

    def __init__(
        self,
        queue_zone_id: str = "zone_checkout",
        max_length_threshold: int = 4,
        max_wait_seconds: float = 120.0,
    ) -> None:
        self.queue_zone_id = queue_zone_id
        self.max_length_threshold = max_length_threshold
        self.max_wait_seconds = max_wait_seconds
        self.alert_history: List[QueueAnomalyAlert] = []

    def check_queue_health(self, spatial_engine: SpatialAnalyticsEngine) -> Optional[QueueAnomalyAlert]:
        """Evaluates checkout zone occupancy and generates alert if SLA is breached."""
        zone_stats = spatial_engine.get_zone_analytics().get(self.queue_zone_id)
        if not zone_stats:
            return None

        current_occupants = zone_stats["current_occupants"]
        avg_dwell = zone_stats["avg_dwell_seconds"]

        if current_occupants >= self.max_length_threshold or avg_dwell >= self.max_wait_seconds:
            severity = "CRITICAL" if current_occupants >= self.max_length_threshold * 1.5 else "WARNING"
            recommendation = (
                f"Open auxiliary cash registers immediately (Current Queue: {current_occupants} shoppers, "
                f"Avg Wait: {avg_dwell:.1f}s)."
            )
            alert = QueueAnomalyAlert(
                alert_id=f"alt-{len(self.alert_history) + 1:03d}",
                zone_id=self.queue_zone_id,
                current_queue_length=current_occupants,
                avg_wait_seconds=avg_dwell,
                severity=severity,
                recommendation=recommendation,
            )
            self.alert_history.append(alert)
            logger.warning(f"Queue Bottleneck Alert [{severity}]: {recommendation}")
            return alert

        return None
