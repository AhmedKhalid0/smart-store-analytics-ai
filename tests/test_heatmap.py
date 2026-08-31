"""Unit tests for 2D spatial heatmap density grid accumulation."""

import tempfile
import unittest
from pathlib import Path
from smart_store_analytics.core.heatmap_generator import SpatialHeatmapGenerator


class TestHeatmap(unittest.TestCase):
    """Test cases for spatial heatmap accumulation and export."""

    def test_heatmap_point_accumulation(self):
        generator = SpatialHeatmapGenerator(grid_width=50, grid_height=50)
        generator.add_point(x=640, y=360, frame_width=1280, frame_height=720, intensity=1.0)

        matrix = generator.get_normalized_matrix()
        self.assertEqual(len(matrix), 50)
        self.assertEqual(len(matrix[0]), 50)
        self.assertGreater(generator.max_density, 0.0)

        # Center should have highest normalized density of 1.0
        center_val = matrix[25][25]
        self.assertAlmostEqual(center_val, 1.0)

    def test_export_ppm_image(self):
        generator = SpatialHeatmapGenerator(grid_width=20, grid_height=20)
        generator.add_point(x=50, y=50, frame_width=100, frame_height=100)

        with tempfile.TemporaryDirectory() as tmp:
            img_path = Path(tmp) / "test_heatmap.ppm"
            exported = generator.export_ppm_image(img_path)
            self.assertTrue(exported.exists())
            self.assertGreater(exported.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
