"""Integration tests for FastAPI REST endpoints in Smart-Store-Analytics."""

import unittest
from fastapi.testclient import TestClient

from smart_store_analytics.api.app import create_app
from smart_store_analytics.core.heatmap_generator import SpatialHeatmapGenerator
from smart_store_analytics.core.spatial_analytics import SpatialAnalyticsEngine
from smart_store_analytics.core.video_processor import VideoProcessor
from smart_store_analytics.utils.config import Settings


class TestAPI(unittest.TestCase):
    """Test cases for REST API endpoints."""

    def setUp(self):
        settings = Settings(app_env="testing")
        spatial_engine = SpatialAnalyticsEngine()
        heatmap_gen = SpatialHeatmapGenerator()
        processor = VideoProcessor(spatial_engine=spatial_engine, heatmap_gen=heatmap_gen)

        self.app = create_app(
            settings=settings,
            processor=processor,
            spatial_engine=spatial_engine,
            heatmap_gen=heatmap_gen,
        )
        self.client = TestClient(self.app)

    def test_health_endpoint(self):
        res = self.client.get("/api/v1/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["environment"], "testing")
        self.assertGreater(data["zones_configured"], 0)

    def test_analytics_stats_endpoint(self):
        res = self.client.get("/api/v1/analytics/stats")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertGreater(data["total_footfall"], 0)
        self.assertGreater(len(data["zones"]), 0)

    def test_heatmap_matrix_endpoint(self):
        res = self.client.get("/api/v1/heatmap")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertGreater(data["grid_width"], 0)
        self.assertGreater(len(data["matrix"]), 0)

    def test_heatmap_image_endpoint(self):
        res = self.client.get("/api/v1/heatmap/image")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.headers["content-type"], "image/x-portable-pixmap")
        self.assertGreater(len(res.content), 0)


if __name__ == "__main__":
    unittest.main()
