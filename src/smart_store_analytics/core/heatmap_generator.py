"""2D Spatial Heatmap generator accumulating customer footfall density."""

import math
from pathlib import Path
from typing import List, Tuple
from smart_store_analytics.utils.logger import get_logger

logger = get_logger(__name__)


class SpatialHeatmapGenerator:
    """Accumulates 2D Gaussian density matrices to visualize customer traffic hotspots."""

    def __init__(self, grid_width: int = 128, grid_height: int = 72) -> None:
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.grid: List[List[float]] = [[0.0 for _ in range(grid_width)] for _ in range(grid_height)]
        self.max_density = 0.0

    def add_point(
        self,
        x: float,
        y: float,
        frame_width: int = 1280,
        frame_height: int = 720,
        intensity: float = 1.0,
        radius: int = 4,
    ) -> None:
        """Adds a Gaussian accumulation kernel at normalized floor coordinates."""
        gx = int((x / float(frame_width)) * self.grid_width)
        gy = int((y / float(frame_height)) * self.grid_height)

        gx = max(0, min(self.grid_width - 1, gx))
        gy = max(0, min(self.grid_height - 1, gy))

        sigma = max(1.0, radius / 2.0)
        two_sigma_sq = 2.0 * (sigma ** 2)

        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                nx = gx + dx
                ny = gy + dy
                if 0 <= nx < self.grid_width and 0 <= ny < self.grid_height:
                    dist_sq = dx * dx + dy * dy
                    weight = math.exp(-dist_sq / two_sigma_sq) * intensity
                    self.grid[ny][nx] += weight
                    if self.grid[ny][nx] > self.max_density:
                        self.max_density = self.grid[ny][nx]

    def get_normalized_matrix(self) -> List[List[float]]:
        """Returns density matrix with values normalized between 0.0 and 1.0."""
        if self.max_density <= 0.0:
            return [[0.0 for _ in range(self.grid_width)] for _ in range(self.grid_height)]

        norm = []
        for row in self.grid:
            norm.append([round(val / self.max_density, 3) for val in row])
        return norm

    def export_ppm_image(self, output_path: str | Path) -> Path:
        """Exports 2D density grid to standard RGB PPM image format (Zero-dependency)."""
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        norm_matrix = self.get_normalized_matrix()

        with open(path, "wb") as f:
            header = f"P6\n{self.grid_width} {self.grid_height}\n255\n"
            f.write(header.encode("ascii"))

            pixel_bytes = bytearray()
            for row in norm_matrix:
                for val in row:
                    r, g, b = self._val_to_turbo_colormap(val)
                    pixel_bytes.extend((r, g, b))

            f.write(pixel_bytes)

        logger.info(f"Exported spatial heatmap to {path}")
        return path

    @staticmethod
    def _val_to_turbo_colormap(val: float) -> Tuple[int, int, int]:
        """Translates normalized 0.0-1.0 density into RGB color gradient (Dark Blue -> Cyan -> Green -> Yellow -> Red)."""
        if val <= 0.01:
            return 11, 15, 25  # Dark background matching UI
        elif val < 0.25:
            # Blue to Cyan
            ratio = val / 0.25
            return int(0), int(ratio * 180), int(150 + ratio * 105)
        elif val < 0.50:
            # Cyan to Green
            ratio = (val - 0.25) / 0.25
            return int(0), int(180 + ratio * 75), int(255 * (1.0 - ratio))
        elif val < 0.75:
            # Green to Yellow
            ratio = (val - 0.50) / 0.25
            return int(ratio * 245), int(255), int(0)
        else:
            # Yellow to Red
            ratio = (val - 0.75) / 0.25
            return int(245 + ratio * 10), int(255 * (1.0 - ratio * 0.8)), int(0)
