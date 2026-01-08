from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
import httpx
import os

from auth import get_current_active_user
from models import User

router = APIRouter()

TILE_SERVER_URL = os.getenv("OSM_TILE_SERVER", "http://tile-server:8080")
OSRM_SERVER_URL = os.getenv("OSRM_SERVER", "http://routing:5000")
NOMINATIM_URL = os.getenv("NOMINATIM_URL", "http://geocoder:8080")

@router.get("/tiles/{z}/{x}/{y}")
async def get_map_tile(
    z: int,
    x: int,
    y: int,
    current_user: User = Depends(get_current_active_user)
):
    """Proxy map tiles from tile server"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{TILE_SERVER_URL}/tiles/{z}/{x}/{y}.pbf")
            return response.content
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch tile: {str(e)}"
        )

@router.post("/route")
async def calculate_route(
    start_lat: float,
    start_lon: float,
    end_lat: float,
    end_lon: float,
    profile: Optional[str] = "car",
    current_user: User = Depends(get_current_active_user)
):
    """Calculate route between two points"""
    try:
        async with httpx.AsyncClient() as client:
            url = f"{OSRM_SERVER_URL}/route/v1/{profile}/{start_lon},{start_lat};{end_lon},{end_lat}"
            params = {
                "overview": "full",
                "geometries": "geojson",
                "steps": "true"
            }
            response = await client.get(url, params=params)
            return response.json()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate route: {str(e)}"
        )

@router.get("/geocode")
async def geocode_address(
    q: str = Query(..., description="Address to geocode"),
    limit: int = Query(5, ge=1, le=20),
    current_user: User = Depends(get_current_active_user)
):
    """Geocode an address to coordinates"""
    try:
        async with httpx.AsyncClient() as client:
            url = f"{NOMINATIM_URL}/search"
            params = {
                "q": q,
                "format": "json",
                "limit": limit
            }
            response = await client.get(url, params=params)
            return response.json()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to geocode address: {str(e)}"
        )

@router.get("/reverse")
async def reverse_geocode(
    lat: float,
    lon: float,
    current_user: User = Depends(get_current_active_user)
):
    """Reverse geocode coordinates to address"""
    try:
        async with httpx.AsyncClient() as client:
            url = f"{NOMINATIM_URL}/reverse"
            params = {
                "lat": lat,
                "lon": lon,
                "format": "json"
            }
            response = await client.get(url, params=params)
            return response.json()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reverse geocode: {str(e)}"
        )

@router.get("/search")
async def search_poi(
    q: str = Query(..., description="Search query"),
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    radius: Optional[int] = Query(5000, description="Search radius in meters"),
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_active_user)
):
    """Search for points of interest"""
    try:
        async with httpx.AsyncClient() as client:
            url = f"{NOMINATIM_URL}/search"
            params = {
                "q": q,
                "format": "json",
                "limit": limit
            }

            if lat and lon:
                params["lat"] = lat
                params["lon"] = lon
                params["radius"] = radius

            response = await client.get(url, params=params)
            return response.json()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search POI: {str(e)}"
        )
