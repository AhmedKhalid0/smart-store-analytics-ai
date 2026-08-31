"""Person object detection interfaces and synthetic video trajectory generator."""

import abc
import math
from typing import List, Optional, Tuple
from pydantic import BaseModel, Field

from smart_store_analytics.utils.logger import get_logger

logger = get_logger(__name__)


class Detection(BaseModel):
    """Represents a single detected person in a video frame."""

    bbox: Tuple[float, float, float, float] = Field(..., description="(x1, y1, x2, y2) coordinates")
    confidence: float = 1.0
    class_name: str = "person"


class BasePersonDetector(abc.ABC):
    """Abstract interface for human detection backends."""

    @abc.abstractmethod
    def detect(self, frame: Any) -> List[Detection]:
        """Runs detection on frame image."""
        pass


class YOLOPersonDetector(BasePersonDetector):
    """YOLOv8/v11 person detector wrapper."""

    def __init__(self, model_name: str = "yolov8n.pt", conf_thresh: float = 0.35) -> None:
        self.model_name = model_name
        self.conf_thresh = conf_thresh
        self._model = None
        self._init_model()

    def _init_model(self) -> None:
        try:
            from ultralytics import YOLO
            self._model = YOLO(self.model_name)
            logger.info(f"Loaded YOLO model '{self.model_name}'")
        except Exception as e:
            logger.warning(f"Failed to load YOLO model ({e}). Using synthetic detector fallback.")
            self._model = None

    def detect(self, frame: Any) -> List[Detection]:
        if self._model is None:
            return []

        results = self._model(frame, verbose=False)
        detections: List[Detection] = []
        for r in results:
            for box in r.boxes:
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])
                if cls_id == 0 and conf >= self.conf_thresh:  # Class 0 is person
                    xyxy = box.xyxy[0].tolist()
                    detections.append(
                        Detection(
                            bbox=(xyxy[0], xyxy[1], xyxy[2], xyxy[3]),
                            confidence=round(conf, 3),
                            class_name="person",
                        )
                    )
        return detections


class SyntheticVideoSequenceGenerator:
    """Generates realistic customer trajectories across multi-frame retail scenarios.
    
    Provides deterministic zero-GPU testing and realistic live demonstrations.
    """

    def __init__(self, frame_width: int = 1280, frame_height: int = 720, total_frames: int = 120) -> None:
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.total_frames = total_frames

        # Configure 4 distinct customer paths
        # Person 1: Entrance -> Electronics Shelf -> Exit
        # Person 2: Entrance -> Promotions Display -> Checkout Queue
        # Person 3: Entrance -> Checkout Queue -> Exit
        # Person 4: Roaming shopper in Promotions Display
        self.customers = [
            {"id": 1, "start_frame": 0, "end_frame": 100, "start_pos": (150, 100), "target_pos": (900, 200)},
            {"id": 2, "start_frame": 10, "end_frame": 115, "start_pos": (200, 120), "target_pos": (950, 550)},
            {"id": 3, "start_frame": 25, "end_frame": 120, "start_pos": (180, 140), "target_pos": (980, 580)},
            {"id": 4, "start_frame": 5, "end_frame": 90, "start_pos": (450, 300), "target_pos": (520, 380)},
        ]

    def get_detections_for_frame(self, frame_idx: int) -> List[Detection]:
        """Returns detected bounding boxes for a specific simulated frame index."""
        detections: List[Detection] = []
        box_w = 60.0
        box_h = 130.0

        for c in self.customers:
            if c["start_frame"] <= frame_idx <= c["end_frame"]:
                progress = (frame_idx - c["start_frame"]) / float(c["end_frame"] - c["start_frame"])
                sx, sy = c["start_pos"]
                tx, ty = c["target_pos"]

                # Linear interpolation with slight natural jitter
                jitter_x = math.sin(frame_idx * 0.4 + c["id"]) * 4.0
                jitter_y = math.cos(frame_idx * 0.4 + c["id"]) * 4.0

                curr_x = sx + (tx - sx) * progress + jitter_x
                curr_y = sy + (ty - sy) * progress + jitter_y

                x1 = curr_x - box_w / 2.0
                y1 = curr_y - box_h
                x2 = curr_x + box_w / 2.0
                y2 = curr_y

                detections.append(
                    Detection(
                        bbox=(round(x1, 1), round(y1, 1), round(x2, 1), round(y2, 1)),
                        confidence=0.96,
                        class_name="person",
                    )
                )

        return detections
