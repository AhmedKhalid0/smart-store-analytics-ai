"""Unit tests for spatial store zones, dwell-time calculation, and footfall counting."""

import unittest
from smart_store_analytics.core.spatial_analytics import SpatialAnalyticsEngine, StoreZone
from smart_store_analytics.core.tracking_engine import TrackedPerson, TrackState


class TestSpatialAnalytics(unittest.TestCase):
    """Test cases for spatial zones and dwell time."""

    def test_zone_entry_and_dwell_accumulation(self):
        engine = SpatialAnalyticsEngine(fps=10.0)
        zone = StoreZone(
            id="test_zone",
            name="Test Display",
            polygon=[(0.0, 0.0), (100.0, 0.0), (100.0, 100.0), (0.0, 100.0)],
        )
        engine.add_zone(zone)

        # Person 1 inside zone at (50, 50) on frame 0
        track = TrackedPerson(
            track_id=101,
            bbox=(30.0, 0.0, 70.0, 50.0),
            centroid=(50.0, 50.0),
            state=TrackState.CONFIRMED,
            first_seen_frame=0,
            last_seen_frame=0,
        )

        engine.update([track], frame_idx=0)
        self.assertEqual(engine.total_footfall, 1)

        # Still inside zone on frame 30 (3 seconds elapsed at 10 fps)
        engine.update([track], frame_idx=30)
        analytics = engine.get_zone_analytics()
        
        self.assertEqual(analytics["test_zone"]["total_visits"], 1)
        self.assertAlmostEqual(analytics["test_zone"]["avg_dwell_seconds"], 3.0)
        self.assertEqual(analytics["test_zone"]["current_occupants"], 1)


if __name__ == "__main__":
    unittest.main()
