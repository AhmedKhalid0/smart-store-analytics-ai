"""Test suite for Multi-Source Video Stream Manager and API endpoints."""

import io
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from smart_store_analytics.api.app import create_app
from smart_store_analytics.core.spatial_analytics import SpatialAnalyticsEngine
from smart_store_analytics.core.stream_manager import MultiSourceStreamManager, StreamSourceType
from smart_store_analytics.core.video_processor import VideoProcessor


class TestStreamManager:
    """Unit tests for MultiSourceStreamManager."""

    def test_default_synthetic_state(self):
        processor = VideoProcessor()
        manager = MultiSourceStreamManager(processor=processor)
        status = manager.get_status()
        assert status.source_type == StreamSourceType.SYNTHETIC
        assert status.is_active is True
        assert "Camera 01" in status.camera_name

    def test_set_rtsp_source(self):
        processor = VideoProcessor()
        manager = MultiSourceStreamManager(processor=processor)
        status = manager.set_rtsp_source(
            rtsp_url="rtsp://admin:secret@192.168.1.100:554/ch0",
            camera_name="Entrance HD CCTV",
        )
        assert status.source_type == StreamSourceType.RTSP_STREAM
        assert status.camera_name == "Entrance HD CCTV"
        assert status.source_uri == "rtsp://admin:secret@192.168.1.100:554/ch0"

    def test_invalid_rtsp_url_raises_error(self):
        processor = VideoProcessor()
        manager = MultiSourceStreamManager(processor=processor)
        with pytest.raises(ValueError):
            manager.set_rtsp_source(rtsp_url="ftp://invalid.stream")

    def test_video_file_not_found_raises_error(self):
        processor = VideoProcessor()
        manager = MultiSourceStreamManager(processor=processor)
        with pytest.raises(FileNotFoundError):
            manager.set_video_file_source(Path("non_existent_video.mp4"))

    def test_invalid_video_extension_raises_error(self):
        import tempfile
        import shutil
        temp_dir = Path(tempfile.mkdtemp(prefix="test_stream_"))
        try:
            fake_txt = temp_dir / "test.txt"
            fake_txt.write_text("not a video")
            processor = VideoProcessor()
            manager = MultiSourceStreamManager(processor=processor)
            with pytest.raises(ValueError):
                manager.set_video_file_source(fake_txt)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_step_frame_execution(self):
        processor = VideoProcessor()
        manager = MultiSourceStreamManager(processor=processor)
        initial_frame = manager.current_frame
        next_frame = manager.step()
        assert next_frame == initial_frame + 1
        assert manager.current_frame == next_frame


class TestStreamsAPI:
    """Integration tests for /api/v1/streams HTTP endpoints."""

    @pytest.fixture
    def client(self):
        import tempfile
        import shutil
        temp_dir = Path(tempfile.mkdtemp(prefix="test_stream_api_"))
        try:
            spatial_engine = SpatialAnalyticsEngine()
            processor = VideoProcessor(spatial_engine=spatial_engine)
            manager = MultiSourceStreamManager(processor=processor)
            app = create_app(processor=processor, spatial_engine=spatial_engine, stream_manager=manager)
            c = TestClient(app)
            yield c
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_get_stream_status_endpoint(self, client: TestClient):
        res = client.get("/api/v1/streams/status")
        assert res.status_code == 200
        data = res.json()
        assert data["source_type"] == "synthetic"
        assert data["is_active"] is True

    def test_connect_rtsp_endpoint(self, client: TestClient):
        payload = {
            "rtsp_url": "rtsp://192.168.1.200:554/live",
            "camera_name": "Checkout Lane 1",
        }
        res = client.post("/api/v1/streams/connect-rtsp", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["source_type"] == "rtsp_stream"
        assert data["camera_name"] == "Checkout Lane 1"

    def test_connect_invalid_rtsp_endpoint(self, client: TestClient):
        payload = {"rtsp_url": "bad_protocol://test"}
        res = client.post("/api/v1/streams/connect-rtsp", json=payload)
        assert res.status_code == 400

    def test_reset_synthetic_endpoint(self, client: TestClient):
        client.post(
            "/api/v1/streams/connect-rtsp",
            json={"rtsp_url": "rtsp://192.168.1.50/live", "camera_name": "RTSP Test"},
        )
        res_reset = client.post("/api/v1/streams/reset-synthetic")
        assert res_reset.status_code == 200
        data = res_reset.json()
        assert data["source_type"] == "synthetic"

    def test_upload_invalid_format(self, client: TestClient):
        fake_file = io.BytesIO(b"fake data")
        res = client.post(
            "/api/v1/streams/upload",
            files={"file": ("test.pdf", fake_file, "application/pdf")},
        )
        assert res.status_code == 400

    def test_upload_valid_video_file(self, client: TestClient):
        import shutil
        import tempfile
        import cv2
        import numpy as np

        temp_dir = Path(tempfile.mkdtemp(prefix="test_vid_"))
        try:
            vid_path = temp_dir / "valid_sample.mp4"
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            writer = cv2.VideoWriter(str(vid_path), fourcc, 10.0, (64, 64))
            for _ in range(5):
                frame = np.zeros((64, 64, 3), dtype=np.uint8)
                writer.write(frame)
            writer.release()

            with open(vid_path, "rb") as f:
                res = client.post(
                    "/api/v1/streams/upload",
                    files={"file": ("store_sample.mp4", f, "video/mp4")},
                    data={"camera_name": "Recorded Aisle Footprint"},
                )
            assert res.status_code == 200
            data = res.json()
            assert data["source_type"] == "video_file"
            assert data["camera_name"] == "Recorded Aisle Footprint"
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
