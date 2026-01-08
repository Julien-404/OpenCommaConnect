from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from database import get_db
from models import User, Device, Route, RouteSegment, Event
from schemas import RouteResponse, RouteListResponse, RouteSegmentResponse, EventResponse
from auth import get_current_active_user

router = APIRouter()

@router.get("/", response_model=RouteListResponse)
async def list_routes(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    device_id: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List routes with pagination"""
    # Build query
    query = db.query(Route).join(Device).filter(Device.owner_id == current_user.id)

    if device_id:
        query = query.filter(Device.dongle_id == device_id)

    # Get total count
    total = query.count()

    # Apply pagination
    routes = query.order_by(Route.start_time.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return {
        "routes": routes,
        "total": total,
        "page": page,
        "page_size": page_size
    }

@router.get("/{route_name}", response_model=RouteResponse)
async def get_route(
    route_name: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get route details"""
    route = db.query(Route).join(Device).filter(
        Route.fullname == route_name,
        Device.owner_id == current_user.id
    ).first()

    if not route:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Route not found"
        )

    return route

@router.delete("/{route_name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_route(
    route_name: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a route"""
    route = db.query(Route).join(Device).filter(
        Route.fullname == route_name,
        Device.owner_id == current_user.id
    ).first()

    if not route:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Route not found"
        )

    db.delete(route)
    db.commit()

    return None

@router.get("/{route_name}/segments", response_model=List[RouteSegmentResponse])
async def get_route_segments(
    route_name: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get route segments"""
    route = db.query(Route).join(Device).filter(
        Route.fullname == route_name,
        Device.owner_id == current_user.id
    ).first()

    if not route:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Route not found"
        )

    segments = db.query(RouteSegment).filter(
        RouteSegment.route_id == route.id
    ).order_by(RouteSegment.segment_number).all()

    return segments

@router.get("/{route_name}/events", response_model=List[EventResponse])
async def get_route_events(
    route_name: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get route events"""
    route = db.query(Route).join(Device).filter(
        Route.fullname == route_name,
        Device.owner_id == current_user.id
    ).first()

    if not route:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Route not found"
        )

    events = db.query(Event).filter(
        Event.route_id == route.id
    ).order_by(Event.timestamp).all()

    return events

@router.get("/{route_name}/video")
async def stream_video(
    route_name: str,
    segment: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Stream video for a route"""
    route = db.query(Route).join(Device).filter(
        Route.fullname == route_name,
        Device.owner_id == current_user.id
    ).first()

    if not route:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Route not found"
        )

    # TODO: Implement video streaming from MinIO
    return {"message": "Video streaming not yet implemented"}

@router.get("/{route_name}/log")
async def download_log(
    route_name: str,
    segment: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Download log file for a route"""
    route = db.query(Route).join(Device).filter(
        Route.fullname == route_name,
        Device.owner_id == current_user.id
    ).first()

    if not route:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Route not found"
        )

    # TODO: Implement log download from MinIO
    return {"message": "Log download not yet implemented"}

@router.get("/{route_name}/thumbnail")
async def get_thumbnail(
    route_name: str,
    segment: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get thumbnail for a route"""
    route = db.query(Route).join(Device).filter(
        Route.fullname == route_name,
        Device.owner_id == current_user.id
    ).first()

    if not route:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Route not found"
        )

    # TODO: Implement thumbnail retrieval from MinIO
    return {"message": "Thumbnail not yet implemented"}

@router.post("/{route_name}/share")
async def share_route(
    route_name: str,
    share_with_email: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Share a route with another user"""
    route = db.query(Route).join(Device).filter(
        Route.fullname == route_name,
        Device.owner_id == current_user.id
    ).first()

    if not route:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Route not found"
        )

    # TODO: Implement route sharing
    return {"message": "Route sharing not yet implemented"}
