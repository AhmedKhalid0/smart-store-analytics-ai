"""Video streaming, CCTV file upload, and RTSP connection management API endpoints."""

import os
from pathlib import Path
import shutil
from typing import Optional
from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile, status
from pydantic import BaseModel, Field

from smart_store_analytics.core.stream_manager import MultiSourceStreamManager, StreamStatus
from smart_store_analytics.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/streams", tags=["Video Streams"])


class ConnectRTSPRequest(BaseModel):
    """Payload to establish connection with an IP camera RTSP feed."""

    rtsp_url: str = Field(..., description="RTSP URL (e.g. 'rtsp://admin:pass@192.168.1.50:554/stream1')")
    camera_name: Optional[str] = Field("CCTV Camera 01 (RTSP)", description="Human-readable camera designation")


def get_stream_manager(request: Request) -> MultiSourceStreamManager:
    """Safely retrieves or lazily initializes the MultiSourceStreamManager."""
    if not hasattr(request.app.state, "stream_manager") or request.app.state.stream_manager is None:
        processor = getattr(request.app.state, "processor", None)
        if processor is None:
            from smart_store_analytics.core.video_processor import VideoProcessor
            processor = VideoProcessor()
            request.app.state.processor = processor
        request.app.state.stream_manager = MultiSourceStreamManager(processor=processor)
    return request.app.state.stream_manager


@router.get("/status", response_model=StreamStatus, status_code=status.HTTP_200_OK)
async def get_stream_status(request: Request) -> StreamStatus:
    """Returns current active vision ingestion source, resolution, FPS, and operating state."""
    manager = get_stream_manager(request)
    return manager.get_status()


@router.post("/upload", response_model=StreamStatus, status_code=status.HTTP_200_OK)
async def upload_cctv_video(
    request: Request,
    file: UploadFile = File(...),
    camera_name: Optional[str] = Form(None),
) -> StreamStatus:
    """Uploads recorded retail CCTV footage (MP4, AVI, MOV, MKV) and mounts it into the vision engine."""
    manager = get_stream_manager(request)
    filename = file.filename or "uploaded_cctv.mp4"
    ext = Path(filename).suffix.lower()

    valid_exts = {".mp4", ".avi", ".mov", ".mkv"}
    if ext not in valid_exts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported video file format '{ext}'. Allowed formats: {sorted(list(valid_exts))}",
        )

    # Save to data/uploads
    uploads_dir = Path("data/uploads")
    uploads_dir.mkdir(parents=True, exist_ok=True)
    target_path = uploads_dir / filename

    try:
        with open(target_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        logger.error(f"Failed to save uploaded video file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save video file: {e}",
        )

    try:
        name = camera_name or f"CCTV Footage ({filename})"
        return manager.set_video_file_source(target_path, camera_name=name)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/connect-rtsp", response_model=StreamStatus, status_code=status.HTTP_200_OK)
async def connect_rtsp_camera(payload: ConnectRTSPRequest, request: Request) -> StreamStatus:
    """Connects vision pipeline to a live RTSP or HTTP network camera feed."""
    manager = get_stream_manager(request)
    try:
        return manager.set_rtsp_source(payload.rtsp_url, camera_name=payload.camera_name)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Unable to connect to camera endpoint: {e}",
        )


@router.post("/reset-synthetic", response_model=StreamStatus, status_code=status.HTTP_200_OK)
async def reset_to_synthetic(request: Request) -> StreamStatus:
    """Restores the zero-GPU mathematical synthetic simulation generator."""
    manager = get_stream_manager(request)
    return manager.set_synthetic_source()
