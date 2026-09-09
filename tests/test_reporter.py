"""Unit and integration tests for ReportGenerator and Reporting API endpoints."""

import unittest
from fastapi.testclient import TestClient

from smart_store_analytics.api.app import create_app
from smart_store_analytics.core.heatmap_generator import SpatialHeatmapGenerator
from smart_store_analytics.core.reporter import ReportGenerator
from smart_store_analytics.core.spatial_analytics import SpatialAnalyticsEngine
from smart_store_analytics.core.video_processor import VideoProcessor
from smart_store_analytics.utils.config import Settings


class TestReporter(unittest.TestCase):
    """Test suite for executive report generation and CSV exports."""

    def setUp(self):
        self.settings = Settings(app_env="testing")
        self.spatial_engine = SpatialAnalyticsEngine()
        self.heatmap_gen = SpatialHeatmapGenerator()
        self.processor = VideoProcessor(spatial_engine=self.spatial_engine, heatmap_gen=self.heatmap_gen)
        # Pre-seed simulation data
        self.processor.process_synthetic_simulation(num_frames=40)

        self.reporter = ReportGenerator(self.processor)

        self.app = create_app(
            settings=self.settings,
            processor=self.processor,
            spatial_engine=self.spatial_engine,
            heatmap_gen=self.heatmap_gen,
        )
        self.client = TestClient(self.app)

    def test_generate_executive_html(self):
        html = self.reporter.generate_executive_html(store_name="Test Venue")
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("Test Venue", html)
        self.assertIn("Commercial Zone Engagement", html)
        self.assertIn("Entrance & Foyer", html)
        self.assertIn("@media print", html)

    def test_export_dwell_csv(self):
        csv_content = self.reporter.export_dwell_csv()
        self.assertIn("zone_id,zone_name,category", csv_content)
        self.assertIn("zone_entrance", csv_content)
        lines = csv_content.strip().split("\n")
        self.assertGreaterEqual(len(lines), 2)  # Header + at least 1 zone row

    def test_export_queue_csv(self):
        csv_content = self.reporter.export_queue_csv()
        self.assertIn("timestamp,severity,zone_id", csv_content)

    def test_api_executive_report_endpoint(self):
        res = self.client.get("/api/v1/reports/executive?store_name=Metro+Center")
        self.assertEqual(res.status_code, 200)
        self.assertIn("text/html", res.headers["content-type"])
        self.assertIn("Metro Center", res.text)

    def test_api_export_dwell_csv_endpoint(self):
        res = self.client.get("/api/v1/reports/export/dwell-csv")
        self.assertEqual(res.status_code, 200)
        self.assertIn("text/csv", res.headers["content-type"])
        self.assertIn("attachment; filename=store_dwell_telemetry.csv", res.headers.get("content-disposition", ""))
        self.assertIn("zone_entrance", res.text)

    def test_api_export_queue_csv_endpoint(self):
        res = self.client.get("/api/v1/reports/export/queue-csv")
        self.assertEqual(res.status_code, 200)
        self.assertIn("text/csv", res.headers["content-type"])
        self.assertIn("attachment; filename=queue_sla_violations.csv", res.headers.get("content-disposition", ""))
