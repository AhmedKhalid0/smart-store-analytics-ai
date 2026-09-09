"""Commercial Store Zone definition, vertex editing, and layout configuration endpoints."""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from smart_store_analytics.core.spatial_analytics import StoreZone
from smart_store_analytics.core.video_processor import VideoProcessor
from smart_store_analytics.utils.geometry import Point2D

router = APIRouter(prefix="/api/v1/zones", tags=["Store Zones"])


class ZoneCreateRequest(BaseModel):
    """Payload to create a new commercial store zone."""

    id: str = Field(..., min_length=2, description="Unique slug identifier (e.g. 'zone_bakery')")
    name: str = Field(..., min_length=2, description="Human-readable zone name")
    polygon: List[Point2D] = Field(..., min_length=3, description="List of (x, y) vertex tuples")
    color_hex: str = Field("#a855f7", description="Hex color for UI and canvas rendering")
    category: str = Field("general", description="Category: entrance | showcase | aisle | checkout | service")


class ZoneUpdateRequest(BaseModel):
    """Payload to update an existing store zone."""

    name: Optional[str] = None
    polygon: Optional[List[Point2D]] = Field(None, min_length=3)
    color_hex: Optional[str] = None
    category: Optional[str] = None


@router.get("", response_model=List[StoreZone], status_code=status.HTTP_200_OK)
async def list_zones(request: Request) -> List[StoreZone]:
    """Returns all currently active commercial zones and their polygon boundaries."""
    processor: VideoProcessor = request.app.state.processor
    return processor.spatial_engine.get_zones()


@router.get("/{zone_id}", response_model=StoreZone, status_code=status.HTTP_200_OK)
async def get_zone(zone_id: str, request: Request) -> StoreZone:
    """Retrieves single commercial zone details."""
    processor: VideoProcessor = request.app.state.processor
    zone = processor.spatial_engine.get_zone(zone_id)
    if not zone:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Zone '{zone_id}' not found")
    return zone


@router.post("", response_model=StoreZone, status_code=status.HTTP_201_CREATED)
async def create_zone(payload: ZoneCreateRequest, request: Request) -> StoreZone:
    """Creates and registers a new commercial store zone."""
    processor: VideoProcessor = request.app.state.processor
    if processor.spatial_engine.get_zone(payload.id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Zone with ID '{payload.id}' already exists",
        )
    new_zone = StoreZone(
        id=payload.id,
        name=payload.name,
        polygon=payload.polygon,
        color_hex=payload.color_hex,
        category=payload.category,
    )
    return processor.spatial_engine.add_zone(new_zone)


@router.put("/{zone_id}", response_model=StoreZone, status_code=status.HTTP_200_OK)
async def update_zone(zone_id: str, payload: ZoneUpdateRequest, request: Request) -> StoreZone:
    """Updates zone vertices, display name, category, or hex color."""
    processor: VideoProcessor = request.app.state.processor
    updated = processor.spatial_engine.update_zone(
        zone_id=zone_id,
        polygon=payload.polygon,
        name=payload.name,
        color_hex=payload.color_hex,
        category=payload.category,
    )
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Zone '{zone_id}' not found")
    return updated


@router.delete("/{zone_id}", status_code=status.HTTP_200_OK)
async def delete_zone(zone_id: str, request: Request) -> dict:
    """Removes a zone from the retail floorplan."""
    processor: VideoProcessor = request.app.state.processor
    success = processor.spatial_engine.remove_zone(zone_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Zone '{zone_id}' not found")
    return {"status": "success", "message": f"Zone '{zone_id}' deleted successfully"}


@router.post("/reset", response_model=List[StoreZone], status_code=status.HTTP_200_OK)
async def reset_zones(request: Request) -> List[StoreZone]:
    """Resets floorplan back to standard factory default zones."""
    processor: VideoProcessor = request.app.state.processor
    return processor.spatial_engine.reset_default_zones()
