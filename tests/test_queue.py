"""Unit tests for checkout queue monitoring and bottleneck alerting."""

import unittest
from smart_store_analytics.core.queue_monitor import QueueMonitor
from smart_store_analytics.core.spatial_analytics import SpatialAnalyticsEngine, StoreZone
from smart_store_analytics.core.tracking_engine import TrackedPerson, TrackState


class TestQueueMonitor(unittest.TestCase):
    """Test cases for queue length SLA threshold alerts."""

    def test_queue_alert_triggers_on_excessive_occupancy(self):
        spatial_engine = SpatialAnalyticsEngine(fps=10.0)
        # Register a checkout zone
        zone = StoreZone(
            id="zone_checkout",
            name="Checkout",
            polygon=[(0.0, 0.0), (100.0, 0.0), (100.0, 100.0), (0.0, 100.0)],
        )
        spatial_engine.add_zone(zone)

        # Place 6 people inside checkout zone (threshold is 4)
        tracks = [
            TrackedPerson(
                track_id=i + 1,
                bbox=(10.0, 10.0, 40.0, 50.0),
                centroid=(25.0, 50.0),
                state=TrackState.CONFIRMED,
                first_seen_frame=0,
                last_seen_frame=0,
            )
            for i in range(6)
        ]

        spatial_engine.update(tracks, frame_idx=0)

        monitor = QueueMonitor(queue_zone_id="zone_checkout", max_length_threshold=4)
        alert = monitor.check_queue_health(spatial_engine)

        self.assertIsNotNone(alert)
        self.assertEqual(alert.zone_id, "zone_checkout")
        self.assertEqual(alert.current_queue_length, 6)
        self.assertEqual(len(monitor.alert_history), 1)


if __name__ == "__main__":
    unittest.main()
