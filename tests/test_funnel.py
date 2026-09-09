"""Test suite for Shopper Flow and Conversion Funnel Engine & API Endpoints."""

import pytest
from fastapi.testclient import TestClient

from smart_store_analytics.api.app import create_app
from smart_store_analytics.core.funnel import ShopperFunnelEngine, ShopperFunnelReport
from smart_store_analytics.core.spatial_analytics import SpatialAnalyticsEngine
from smart_store_analytics.core.video_processor import VideoProcessor


class TestFunnelEngine:
    """Unit tests for ShopperFunnelEngine."""

    def test_default_funnel_generation(self):
        engine = ShopperFunnelEngine()
        report = engine.generate_funnel_report()
        assert isinstance(report, ShopperFunnelReport)
        assert report.total_store_footfall >= 1
        assert report.converted_shoppers >= 1
        assert 0.0 <= report.overall_conversion_pct <= 100.0
        assert 0.0 <= report.overall_abandonment_pct <= 100.0
        assert len(report.stages) == 4
        assert len(report.top_transitions) > 0

    def test_stage_ordering_and_drop_off_metrics(self):
        engine = ShopperFunnelEngine()
        report = engine.generate_funnel_report()
        stages = report.stages

        # Stage 1: Entrance
        assert stages[0].stage_id == "stage_1_entrance"
        assert stages[0].conversion_rate_pct == 100.0
        assert stages[0].drop_off_pct == 0.0

        # Stage 2: Browse
        assert stages[1].stage_id == "stage_2_browse"
        assert 0.0 <= stages[1].conversion_rate_pct <= 100.0
        assert stages[1].visitors <= stages[0].visitors

        # Stage 3: Engagement
        assert stages[2].stage_id == "stage_3_engagement"
        assert stages[2].visitors <= stages[1].visitors

        # Stage 4: Checkout
        assert stages[3].stage_id == "stage_4_checkout"
        assert stages[3].visitors <= stages[2].visitors

    def test_top_leakage_stage_identified(self):
        engine = ShopperFunnelEngine()
        report = engine.generate_funnel_report()
        assert "drop-off" in report.top_leakage_stage
        assert report.avg_journey_time_sec > 0.0

    def test_funnel_with_custom_spatial_engine(self):
        spatial_engine = SpatialAnalyticsEngine()
        processor = VideoProcessor(spatial_engine=spatial_engine)
        processor.process_synthetic_simulation(num_frames=40)
        engine = ShopperFunnelEngine(spatial_engine=spatial_engine)
        report = engine.generate_funnel_report()
        assert report.total_store_footfall >= 1
        assert report.converted_shoppers >= 1


class TestFunnelAPI:
    """Integration tests for /api/v1/funnel HTTP endpoints."""

    @pytest.fixture
    def client(self):
        import shutil
        import tempfile
        from pathlib import Path
        temp_dir = Path(tempfile.mkdtemp(prefix="test_funnel_api_"))
        try:
            spatial_engine = SpatialAnalyticsEngine()
            processor = VideoProcessor(spatial_engine=spatial_engine)
            app = create_app(processor=processor, spatial_engine=spatial_engine)
            c = TestClient(app)
            yield c
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_get_funnel_report_endpoint(self, client: TestClient):
        res = client.get("/api/v1/funnel/report")
        assert res.status_code == 200
        data = res.json()
        assert "stages" in data
        assert len(data["stages"]) == 4
        assert "overall_conversion_pct" in data
        assert "top_transitions" in data

    def test_get_funnel_transitions_endpoint(self, client: TestClient):
        res = client.get("/api/v1/funnel/transitions")
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)
        assert len(data) >= 3
        for item in data:
            assert "from_zone_id" in item
            assert "to_zone_id" in item
            assert "transition_count" in item
            assert "share_pct" in item
