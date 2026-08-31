"""Multi-Object Tracking (MOT) engine maintaining persistent customer IDs and trajectories."""

from enum import Enum
from typing import Dict, List, Set, Tuple
from pydantic import BaseModel, Field

from smart_store_analytics.core.detector import Detection
from smart_store_analytics.utils.geometry import BBox, Point2D, calculate_centroid, calculate_iou, euclidean_distance
from smart_store_analytics.utils.logger import get_logger

logger = get_logger(__name__)


class TrackState(str, Enum):
    """Lifecycle states of a tracked individual."""

    TENTATIVE = "tentative"
    CONFIRMED = "confirmed"
    LOST = "lost"
    DELETED = "deleted"


class TrackedPerson(BaseModel):
    """State and movement history of an individual shopper."""

    track_id: int
    bbox: BBox
    centroid: Point2D
    trajectory: List[Point2D] = Field(default_factory=list)
    state: TrackState = TrackState.TENTATIVE
    hits: int = 1
    age_frames: int = 1
    time_since_update: int = 0
    first_seen_frame: int
    last_seen_frame: int


class MultiObjectTracker:
    """Multi-Object Tracker using IoU association and trajectory persistence."""

    def __init__(
        self,
        iou_threshold: float = 0.3,
        dist_threshold: float = 80.0,
        max_age_frames: int = 30,
        min_hits: int = 2,
    ) -> None:
        self.iou_threshold = iou_threshold
        self.dist_threshold = dist_threshold
        self.max_age_frames = max_age_frames
        self.min_hits = min_hits
        self.next_track_id = 1
        self.tracks: Dict[int, TrackedPerson] = {}

    def update(self, detections: List[Detection], frame_idx: int) -> List[TrackedPerson]:
        """Updates tracks with new detections for current video frame."""
        # Record track IDs that existed prior to this update
        pre_existing_track_ids = set(self.tracks.keys())

        # 1. Increment age and time_since_update for pre-existing tracks
        for track_id in pre_existing_track_ids:
            track = self.tracks[track_id]
            track.age_frames += 1
            track.time_since_update += 1

        matched_tracks: Set[int] = set()
        matched_detections: Set[int] = set()

        # 2. Match detections with existing tracks using IoU + Centroid proximity
        if pre_existing_track_ids and detections:
            for det_idx, det in enumerate(detections):
                det_centroid = calculate_centroid(det.bbox)
                best_track_id = None
                best_iou = -1.0
                best_dist = float("inf")

                for track_id in pre_existing_track_ids:
                    if track_id in matched_tracks:
                        continue

                    track = self.tracks[track_id]
                    iou = calculate_iou(det.bbox, track.bbox)
                    dist = euclidean_distance(det_centroid, track.centroid)

                    if iou >= self.iou_threshold and iou > best_iou:
                        best_iou = iou
                        best_track_id = track_id
                    elif iou == 0.0 and dist <= self.dist_threshold and dist < best_dist:
                        best_dist = dist
                        best_track_id = track_id

                if best_track_id is not None:
                    matched_tracks.add(best_track_id)
                    matched_detections.add(det_idx)

                    # Update track state
                    track = self.tracks[best_track_id]
                    track.bbox = det.bbox
                    track.centroid = det_centroid
                    track.trajectory.append(det_centroid)
                    track.hits += 1
                    track.time_since_update = 0
                    track.last_seen_frame = frame_idx
                    if track.hits >= self.min_hits:
                        track.state = TrackState.CONFIRMED

        # 3. Create new tracks for unmatched detections
        for det_idx, det in enumerate(detections):
            if det_idx not in matched_detections:
                c = calculate_centroid(det.bbox)
                new_track = TrackedPerson(
                    track_id=self.next_track_id,
                    bbox=det.bbox,
                    centroid=c,
                    trajectory=[c],
                    state=TrackState.CONFIRMED if self.min_hits <= 1 else TrackState.TENTATIVE,
                    hits=1,
                    age_frames=1,
                    time_since_update=0,
                    first_seen_frame=frame_idx,
                    last_seen_frame=frame_idx,
                )
                self.tracks[self.next_track_id] = new_track
                self.next_track_id += 1

        # 4. Update unmatched pre-existing tracks (mark LOST or remove DELETED)
        to_delete: List[int] = []
        for track_id in pre_existing_track_ids:
            if track_id not in matched_tracks:
                track = self.tracks[track_id]
                if track.time_since_update > self.max_age_frames:
                    to_delete.append(track_id)
                elif track.state == TrackState.CONFIRMED:
                    track.state = TrackState.LOST

        for track_id in to_delete:
            del self.tracks[track_id]

        # Return all active confirmed or tentative tracks
        return [t for t in self.tracks.values() if t.state in [TrackState.CONFIRMED, TrackState.TENTATIVE]]
