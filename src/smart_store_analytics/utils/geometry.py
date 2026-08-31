"""Geometric calculations, bounding box metrics, and point-in-polygon math."""

import math
from typing import List, Tuple

# Bounding box represented as (x1, y1, x2, y2)
BBox = Tuple[float, float, float, float]
Point2D = Tuple[float, float]


def calculate_iou(box_a: BBox, box_b: BBox) -> float:
    """Calculates Intersection-over-Union (IoU) overlap between two bounding boxes."""
    xa1, ya1, xa2, ya2 = box_a
    xb1, yb1, xb2, yb2 = box_b

    # Coordinates of intersection rectangle
    x_left = max(xa1, xb1)
    y_top = max(ya1, yb1)
    x_right = min(xa2, xb2)
    y_bottom = min(ya2, yb2)

    if x_right < x_left or y_bottom < y_top:
        return 0.0

    intersection_area = (x_right - x_left) * (y_bottom - y_top)

    area_a = max(0.0, (xa2 - xa1) * (ya2 - ya1))
    area_b = max(0.0, (xb2 - xb1) * (yb2 - yb1))

    union_area = area_a + area_b - intersection_area
    if union_area <= 0.0:
        return 0.0

    return intersection_area / union_area


def calculate_centroid(box: BBox) -> Point2D:
    """Computes the bottom-center ground contact point of a person's bounding box."""
    x1, y1, x2, y2 = box
    cx = (x1 + x2) / 2.0
    cy = y2  # Ground contact point is at the bottom center of the bounding box
    return cx, cy


def euclidean_distance(pt_a: Point2D, pt_b: Point2D) -> float:
    """Computes 2D Euclidean distance between two points."""
    return math.sqrt((pt_a[0] - pt_b[0]) ** 2 + (pt_a[1] - pt_b[1]) ** 2)


def point_in_polygon(point: Point2D, polygon: List[Point2D]) -> bool:
    """Determines whether a 2D point lies within a polygon using ray-casting."""
    if len(polygon) < 3:
        return False

    x, y = point
    inside = False
    n = len(polygon)

    p1x, p1y = polygon[0]
    for i in range(n + 1):
        p2x, p2y = polygon[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        x_inters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    else:
                        x_inters = p1x
                    if p1x == p2x or x <= x_inters:
                        inside = not inside
        p1x, p1y = p2x, p2y

    return inside
