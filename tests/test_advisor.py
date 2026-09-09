"""Unit and integration tests for RetailCopilotAdvisor and Advisor API endpoints."""

import unittest
from fastapi.testclient import TestClient

from smart_store_analytics.api.app import create_app
from smart_store_analytics.core.advisor import RetailCopilotAdvisor
from smart_store_analytics.core.heatmap_generator import SpatialHeatmapGenerator
from smart_store_analytics.core.spatial_analytics import SpatialAnalyticsEngine
from smart_store_analytics.core.video_processor import VideoProcessor
from smart_store_analytics.utils.config import Settings


class TestAdvisor(unittest.TestCase):
    """Test suite for AI Retail Copilot advisory engine."""

    def setUp(self):
        self.settings = Settings(app_env="testing")
        self.spatial_engine = SpatialAnalyticsEngine()
        self.heatmap_gen = SpatialHeatmapGenerator()
        self.processor = VideoProcessor(spatial_engine=self.spatial_engine, heatmap_gen=self.heatmap_gen)
        self.processor.process_synthetic_simulation(num_frames=60)

        self.advisor = RetailCopilotAdvisor(self.processor)

        self.app = create_app(
            settings=self.settings,
            processor=self.processor,
            spatial_engine=self.spatial_engine,
            heatmap_gen=self.heatmap_gen,
        )
        self.client = TestClient(self.app)

    def test_advisor_analysis_structure(self):
        result = self.advisor.analyze()
        self.assertGreaterEqual(result.health_score, 0)
        self.assertLessEqual(result.health_score, 100)
        self.assertGreater(result.total_insights, 0)
        self.assertIsNotNone(result.executive_summary)

        # Check fields of first insight
        first_insight = result.insights[0]
        self.assertTrue(hasattr(first_insight, "title"))
        self.assertTrue(hasattr(first_insight, "category"))
        self.assertTrue(hasattr(first_insight, "impact"))
        self.assertTrue(hasattr(first_insight, "problem"))
        self.assertTrue(hasattr(first_insight, "recommendation"))
        self.assertTrue(hasattr(first_insight, "projected_roi"))

    def test_api_advisor_insights_endpoint(self):
        res = self.client.get("/api/v1/advisor/insights")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("health_score", data)
        self.assertIn("executive_summary", data)
        self.assertIn("insights", data)
        self.assertGreater(len(data["insights"]), 0)
