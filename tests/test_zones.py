"""Test suite for Dynamic Zone Configuration, Persistence, and API Endpoints."""

import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from smart_store_analytics.api.app import create_app
from smart_store_analytics.core.spatial_analytics import SpatialAnalyticsEngine, StoreZone
from smart_store_analytics.core.video_processor import VideoProcessor


class TestZonesEngine:
    """Unit tests for SpatialAnalyticsEngine dynamic zone management."""

    def test_default_zones_registration(self):
        engine = SpatialAnalyticsEngine()
        zones = engine.get_zones()
        assert len(zones) == 4
        zone_ids = {z.id for z in zones}
        assert "zone_entrance" in zone_ids
        assert "zone_promotions" in zone_ids
        assert "zone_electronics" in zone_ids
        assert "zone_checkout" in zone_ids

    def test_add_and_get_custom_zone(self):
        engine = SpatialAnalyticsEngine()
        new_zone = StoreZone(
            id="zone_cosmetics",
            name="Cosmetics & Fragrances",
            polygon=[(100, 100), (300, 100), (300, 300), (100, 300)],
            color_hex="#ec4899",
            category="showcase",
        )
        engine.add_zone(new_zone)
        retrieved = engine.get_zone("zone_cosmetics")
        assert retrieved is not None
        assert retrieved.name == "Cosmetics & Fragrances"
        assert retrieved.color_hex == "#ec4899"
        assert len(engine.get_zones()) == 5

    def test_update_zone_polygon_and_properties(self):
        engine = SpatialAnalyticsEngine()
        new_poly = [(60, 60), (360, 60), (360, 260), (60, 260)]
        updated = engine.update_zone(
            zone_id="zone_entrance",
            polygon=new_poly,
            name="Main Entrance & Turnstiles",
            color_hex="#0891b2",
        )
        assert updated is not None
        assert updated.name == "Main Entrance & Turnstiles"
        assert updated.polygon == new_poly
        assert updated.color_hex == "#0891b2"

    def test_remove_zone(self):
        engine = SpatialAnalyticsEngine()
        assert engine.get_zone("zone_entrance") is not None
        success = engine.remove_zone("zone_entrance")
        assert success is True
        assert engine.get_zone("zone_entrance") is None
        assert len(engine.get_zones()) == 3

        # Removing non-existent returns False
        assert engine.remove_zone("nonexistent_zone") is False

    def test_reset_default_zones(self):
        engine = SpatialAnalyticsEngine()
        engine.remove_zone("zone_entrance")
        assert len(engine.get_zones()) == 3
        reset_zones = engine.reset_default_zones()
        assert len(reset_zones) == 4
        assert engine.get_zone("zone_entrance") is not None

    def test_json_persistence(self):
        import tempfile
        import shutil
        temp_dir = Path(tempfile.mkdtemp(prefix="test_zones_"))
        try:
            config_file = temp_dir / "zones.json"
            engine = SpatialAnalyticsEngine(config_path=config_file)
            assert config_file.exists()

            # Add custom zone and verify it saves to file
            engine.add_zone(
                StoreZone(
                    id="zone_perfume",
                    name="Perfume Bar",
                    polygon=[(20, 20), (120, 20), (120, 120), (20, 120)],
                    color_hex="#d946ef",
                )
            )
            assert config_file.exists()

            # Load fresh engine from same file
            engine2 = SpatialAnalyticsEngine(config_path=config_file)
            assert engine2.get_zone("zone_perfume") is not None
            assert len(engine2.get_zones()) == 5
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


class TestZonesAPI:
    """Integration tests for /api/v1/zones HTTP endpoints."""

    @pytest.fixture
    def client(self):
        import tempfile
        import shutil
        temp_dir = Path(tempfile.mkdtemp(prefix="test_zones_api_"))
        cfg_file = temp_dir / "test_zones.json"
        spatial_engine = SpatialAnalyticsEngine(config_path=cfg_file)
        processor = VideoProcessor(spatial_engine=spatial_engine)
        app = create_app(processor=processor, spatial_engine=spatial_engine)
        c = TestClient(app)
        yield c
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_list_zones_endpoint(self, client: TestClient):
        response = client.get("/api/v1/zones")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 4
        assert data[0]["id"] == "zone_entrance"

    def test_get_single_zone_endpoint(self, client: TestClient):
        response = client.get("/api/v1/zones/zone_entrance")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Entrance & Foyer"

        # Not found
        res_404 = client.get("/api/v1/zones/zone_does_not_exist")
        assert res_404.status_code == 404

    def test_create_zone_endpoint(self, client: TestClient):
        payload = {
            "id": "zone_accessories",
            "name": "Luxury Accessories",
            "polygon": [[100, 100], [250, 100], [250, 250], [100, 250]],
            "color_hex": "#8b5cf6",
            "category": "showcase",
        }
        res = client.post("/api/v1/zones", json=payload)
        assert res.status_code == 201
        data = res.json()
        assert data["id"] == "zone_accessories"
        assert data["name"] == "Luxury Accessories"

        # Duplicate ID should conflict
        res_dup = client.post("/api/v1/zones", json=payload)
        assert res_dup.status_code == 409

    def test_update_zone_endpoint(self, client: TestClient):
        payload = {
            "name": "Updated Foyer",
            "polygon": [[40, 40], [340, 40], [340, 240], [40, 240]],
            "color_hex": "#0284c7",
        }
        res = client.put("/api/v1/zones/zone_entrance", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["name"] == "Updated Foyer"
        assert data["color_hex"] == "#0284c7"
        assert data["polygon"] == [[40, 40], [340, 40], [340, 240], [40, 240]]

    def test_delete_zone_endpoint(self, client: TestClient):
        res = client.delete("/api/v1/zones/zone_entrance")
        assert res.status_code == 200
        assert res.json()["status"] == "success"

        # Verify it was deleted
        res_check = client.get("/api/v1/zones/zone_entrance")
        assert res_check.status_code == 404

    def test_reset_zones_endpoint(self, client: TestClient):
        client.delete("/api/v1/zones/zone_entrance")
        res_reset = client.post("/api/v1/zones/reset")
        assert res_reset.status_code == 200
        data = res_reset.json()
        assert len(data) == 4
