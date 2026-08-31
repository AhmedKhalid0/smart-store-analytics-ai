"""Unit tests for geometric math, IoU, centroids, and ray-casting algorithms."""

import unittest
from smart_store_analytics.utils.geometry import (
    calculate_centroid,
    calculate_iou,
    euclidean_distance,
    point_in_polygon,
)


class TestGeometry(unittest.TestCase):
    """Test cases for 2D spatial mathematics."""

    def test_calculate_iou_exact_overlap(self):
        box_a = (10.0, 10.0, 50.0, 50.0)
        box_b = (10.0, 10.0, 50.0, 50.0)
        self.assertAlmostEqual(calculate_iou(box_a, box_b), 1.0)

    def test_calculate_iou_no_overlap(self):
        box_a = (0.0, 0.0, 10.0, 10.0)
        box_b = (20.0, 20.0, 30.0, 30.0)
        self.assertEqual(calculate_iou(box_a, box_b), 0.0)

    def test_calculate_centroid(self):
        box = (10.0, 20.0, 50.0, 100.0)
        cx, cy = calculate_centroid(box)
        self.assertEqual(cx, 30.0)
        self.assertEqual(cy, 100.0)  # Ground contact point is bottom center

    def test_euclidean_distance(self):
        pt1 = (0.0, 0.0)
        pt2 = (3.0, 4.0)
        self.assertAlmostEqual(euclidean_distance(pt1, pt2), 5.0)

    def test_point_in_polygon(self):
        # Square from (0,0) to (100,100)
        poly = [(0.0, 0.0), (100.0, 0.0), (100.0, 100.0), (0.0, 100.0)]
        self.assertTrue(point_in_polygon((50.0, 50.0), poly))
        self.assertTrue(point_in_polygon((10.0, 10.0), poly))
        self.assertFalse(point_in_polygon((150.0, 50.0), poly))
        self.assertFalse(point_in_polygon((-10.0, 50.0), poly))


if __name__ == "__main__":
    unittest.main()
