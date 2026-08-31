"""Spatial Heatmap matrix and image export endpoints."""

import io
from fastapi import APIRouter, Request, Response
from smart_store_analytics.api.schemas import HeatmapResponse
from smart_store_analytics.core.heatmap_generator import SpatialHeatmapGenerator

router = APIRouter(prefix="/api/v1/heatmap", tags=["Spatial Heatmap"])


@router.get("", response_model=HeatmapResponse)
async def get_heatmap_matrix(request: Request) -> HeatmapResponse:
    """Returns normalized 2D density grid matrix for spatial rendering."""
    heatmap_gen: SpatialHeatmapGenerator = request.app.state.heatmap_gen
    matrix = heatmap_gen.get_normalized_matrix()

    return HeatmapResponse(
        grid_width=heatmap_gen.grid_width,
        grid_height=heatmap_gen.grid_height,
        matrix=matrix,
    )


@router.get("/image")
async def get_heatmap_ppm_image(request: Request):
    """Generates and returns the colorized RGB PPM spatial heatmap."""
    heatmap_gen: SpatialHeatmapGenerator = request.app.state.heatmap_gen
    norm_matrix = heatmap_gen.get_normalized_matrix()

    header = f"P6\n{heatmap_gen.grid_width} {heatmap_gen.grid_height}\n255\n"
    pixel_bytes = bytearray()
    for row in norm_matrix:
        for val in row:
            r, g, b = heatmap_gen._val_to_turbo_colormap(val)
            pixel_bytes.extend((r, g, b))

    content = header.encode("ascii") + pixel_bytes

    return Response(
        content=bytes(content),
        media_type="image/x-portable-pixmap",
        headers={"Content-Disposition": "attachment; filename=store_traffic_heatmap.ppm"},
    )
