"""Unit tests for Multi-Object Tracking state machine and ID continuity."""

import unittest
from smart_store_analytics.core.detector import Detection
from smart_store_analytics.core.tracking_engine import MultiObjectTracker, TrackState


class TestTracking(unittest.TestCase):
    """Test cases for Multi-Object Tracking."""

    def test_single_object_tracking_continuity(self):
        tracker = MultiObjectTracker(iou_threshold=0.2, min_hits=1)

        # Frame 0: detection at (100, 100, 150, 200)
        det_f0 = [Detection(bbox=(100.0, 100.0, 150.0, 200.0), confidence=0.9)]
        tracks_f0 = tracker.update(det_f0, frame_idx=0)
        self.assertEqual(len(tracks_f0), 1)
        initial_id = tracks_f0[0].track_id

        # Frame 1: shifted slightly to (105, 102, 155, 202)
        det_f1 = [Detection(bbox=(105.0, 102.0, 155.0, 202.0), confidence=0.9)]
        tracks_f1 = tracker.update(det_f1, frame_idx=1)
        self.assertEqual(len(tracks_f1), 1)
        self.assertEqual(tracks_f1[0].track_id, initial_id)
        self.assertEqual(tracks_f1[0].hits, 2)
        self.assertEqual(len(tracks_f1[0].trajectory), 2)

    def test_new_object_assigns_new_id(self):
        tracker = MultiObjectTracker(iou_threshold=0.2, min_hits=1)

        det_1 = [Detection(bbox=(50.0, 50.0, 100.0, 150.0), confidence=0.9)]
        tracks_1 = tracker.update(det_1, frame_idx=0)
        id_1 = tracks_1[0].track_id

        # Disjoint detection far away
        det_2 = [
            Detection(bbox=(50.0, 50.0, 100.0, 150.0), confidence=0.9),
            Detection(bbox=(600.0, 600.0, 650.0, 750.0), confidence=0.9),
        ]
        tracks_2 = tracker.update(det_2, frame_idx=1)
        self.assertEqual(len(tracks_2), 2)
        ids = {t.track_id for t in tracks_2}
        self.assertIn(id_1, ids)


if __name__ == "__main__":
    unittest.main()
