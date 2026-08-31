"""Spatial Store Zone analytics, Footfall counting, and Dwell-Time calculation."""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from smart_store_analytics.core.tracking_engine import TrackedPerson
from smart_store_analytics.utils.geometry import Point2D, point_in_polygon
from smart_store_analytics.utils.logger import get_logger

logger = get_logger(__name__)


class StoreZone(BaseModel):
    """Represents a defined 2D commercial zone inside the retail store floorplan."""

    id: str
    name: str
    polygon: List[Point2D] = Field(..., description="Ordered 2D polygon vertices (x, y)")
    color_hex: str = "#a855f7"
    category: str = "general"  # entrance | aisle | showcase | checkout


class ZoneDwellEvent(BaseModel):
    """Tracks a person's duration inside a specific store zone."""

    track_id: int
    zone_id: str
    entry_frame: int
    exit_frame: Optional[int] = None
    dwell_time_seconds: float = 0.0


class SpatialAnalyticsEngine:
    """Calculates footfall counts, zone transitions, and shopper dwell times."""

    def __init__(self, fps: float = 30.0) -> None:
        self.fps = fps
        self.zones: Dict[str, StoreZone] = {}
        self.active_dwell_sessions: Dict[str, ZoneDwellEvent] = {}  # key: f"{track_id}_{zone_id}"
        self.completed_dwell_events: List[ZoneDwellEvent] = []
        self.unique_visitors_seen: set = set()
        self._register_default_zones()

    def _register_default_zones(self) -> None:
        """Configures realistic retail zones for a 1280x720 store floorplan."""
        self.add_zone(
            StoreZone(
                id="zone_entrance",
                name="Entrance & Foyer",
                polygon=[(50, 50), (350, 50), (350, 250), (50, 250)],
                color_hex="#06b6d4",
                category="entrance",
            )
        )
        self.add_zone(
            StoreZone(
                id="zone_promotions",
                name="Promotions & New Arrivals",
                polygon=[(380, 200), (680, 200), (680, 480), (380, 480)],
                color_hex="#a855f7",
                category="showcase",
            )
        )
        self.add_zone(
            StoreZone(
                id="zone_electronics",
                name="Electronics & Premium Wall",
                polygon=[(750, 50), (1200, 50), (1200, 350), (750, 350)],
                color_hex="#10b981",
                category="showcase",
            )
        )
        self.add_zone(
            StoreZone(
                id="zone_checkout",
                name="Checkout & Service Queue",
                polygon=[(800, 420), (1220, 420), (1220, 680), (800, 680)],
                color_hex="#f59e0b",
                category="checkout",
            )
        )

    def add_zone(self, zone: StoreZone) -> None:
        """Registers a custom polygon store zone."""
        self.zones[zone.id] = zone
        logger.info(f"Registered store zone '{zone.id}' ({zone.name})")

    def update(self, tracks: List[TrackedPerson], frame_idx: int) -> None:
        """Processes current frame tracks and updates zone occupancy and dwell timers."""
        active_track_ids = {t.track_id for t in tracks}
        self.unique_visitors_seen.update(active_track_ids)

        for track in tracks:
            cx, cy = track.centroid

            for zone_id, zone in self.zones.items():
                is_inside = point_in_polygon((cx, cy), zone.polygon)
                session_key = f"{track.track_id}_{zone_id}"

                if is_inside:
                    if session_key not in self.active_dwell_sessions:
                        # Entry event
                        self.active_dwell_sessions[session_key] = ZoneDwellEvent(
                            track_id=track.track_id,
                            zone_id=zone_id,
                            entry_frame=frame_idx,
                        )
                    else:
                        # Update ongoing dwell time
                        session = self.active_dwell_sessions[session_key]
                        frames_elapsed = frame_idx - session.entry_frame
                        session.dwell_time_seconds = round(frames_elapsed / self.fps, 2)
                else:
                    # If previously inside, record exit
                    if session_key in self.active_dwell_sessions:
                        session = self.active_dwell_sessions.pop(session_key)
                        session.exit_frame = frame_idx
                        frames_elapsed = frame_idx - session.entry_frame
                        session.dwell_time_seconds = round(frames_elapsed / self.fps, 2)
                        self.completed_dwell_events.append(session)

        # Close sessions for tracks that disappeared
        to_close = []
        for session_key, session in self.active_dwell_sessions.items():
            if session.track_id not in active_track_ids:
                to_close.append(session_key)

        for key in to_close:
            session = self.active_dwell_sessions.pop(key)
            session.exit_frame = frame_idx
            frames_elapsed = frame_idx - session.entry_frame
            session.dwell_time_seconds = round(frames_elapsed / self.fps, 2)
            self.completed_dwell_events.append(session)

    def get_zone_analytics(self) -> Dict[str, dict]:
        """Calculates aggregate statistics for all store zones."""
        stats = {}
        all_events = self.completed_dwell_events + list(self.active_dwell_sessions.values())

        for zone_id, zone in self.zones.items():
            zone_events = [e for e in all_events if e.zone_id == zone_id]
            total_visits = len(zone_events)
            total_dwell = sum(e.dwell_time_seconds for e in zone_events)
            avg_dwell = round(total_dwell / total_visits, 2) if total_visits > 0 else 0.0

            # Current occupants inside zone
            current_occupants = sum(1 for e in self.active_dwell_sessions.values() if e.zone_id == zone_id)

            stats[zone_id] = {
                "id": zone.id,
                "name": zone.name,
                "color_hex": zone.color_hex,
                "category": zone.category,
                "total_visits": total_visits,
                "avg_dwell_seconds": avg_dwell,
                "current_occupants": current_occupants,
            }

        return stats

    @property
    def total_footfall(self) -> int:
        """Returns total unique shoppers detected."""
        return len(self.unique_visitors_seen)
