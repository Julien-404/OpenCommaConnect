from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from database import get_db
from models import User, Device, DeviceStatus
from schemas import DeviceCreate, DeviceResponse, DeviceStatusResponse, DevicePair
from auth import get_current_active_user

router = APIRouter()

@router.get("/", response_model=List[DeviceResponse])
async def list_devices(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all devices owned by the current user"""
    devices = db.query(Device).filter(Device.owner_id == current_user.id).all()
    return devices

@router.post("/", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
async def create_device(
    device_data: DeviceCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Register a new device"""
    # Check if device already exists
    existing_device = db.query(Device).filter(Device.dongle_id == device_data.dongle_id).first()
    if existing_device:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Device already registered"
        )

    # Create new device
    new_device = Device(
        dongle_id=device_data.dongle_id,
        alias=device_data.alias,
        public_key=device_data.public_key,
        owner_id=current_user.id,
        is_paired=False
    )

    db.add(new_device)
    db.commit()
    db.refresh(new_device)

    return new_device

@router.get("/{dongle_id}", response_model=DeviceResponse)
async def get_device(
    dongle_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get device details"""
    device = db.query(Device).filter(
        Device.dongle_id == dongle_id,
        Device.owner_id == current_user.id
    ).first()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )

    return device

@router.put("/{dongle_id}", response_model=DeviceResponse)
async def update_device(
    dongle_id: str,
    device_data: DeviceCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update device information"""
    device = db.query(Device).filter(
        Device.dongle_id == dongle_id,
        Device.owner_id == current_user.id
    ).first()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )

    # Update device
    if device_data.alias is not None:
        device.alias = device_data.alias
    if device_data.public_key is not None:
        device.public_key = device_data.public_key

    db.commit()
    db.refresh(device)

    return device

@router.delete("/{dongle_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_device(
    dongle_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a device"""
    device = db.query(Device).filter(
        Device.dongle_id == dongle_id,
        Device.owner_id == current_user.id
    ).first()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )

    db.delete(device)
    db.commit()

    return None

@router.post("/{dongle_id}/pair", response_model=DeviceResponse)
async def pair_device(
    dongle_id: str,
    pair_data: DevicePair,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Pair a device with the user account"""
    device = db.query(Device).filter(
        Device.dongle_id == dongle_id,
        Device.owner_id == current_user.id
    ).first()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )

    # In a real implementation, you would verify the pairing token
    # For now, we'll just set is_paired to True
    device.is_paired = True
    device.last_seen = datetime.utcnow()

    db.commit()
    db.refresh(device)

    return device

@router.get("/{dongle_id}/status", response_model=DeviceStatusResponse)
async def get_device_status(
    dongle_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get device status"""
    device = db.query(Device).filter(
        Device.dongle_id == dongle_id,
        Device.owner_id == current_user.id
    ).first()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )

    # Get latest status
    status = db.query(DeviceStatus).filter(
        DeviceStatus.device_id == device.id
    ).order_by(DeviceStatus.timestamp.desc()).first()

    if not status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No status available"
        )

    return status

@router.get("/{dongle_id}/location")
async def get_device_location(
    dongle_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get device location"""
    device = db.query(Device).filter(
        Device.dongle_id == dongle_id,
        Device.owner_id == current_user.id
    ).first()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )

    # Get latest status with location
    status = db.query(DeviceStatus).filter(
        DeviceStatus.device_id == device.id,
        DeviceStatus.location.isnot(None)
    ).order_by(DeviceStatus.timestamp.desc()).first()

    if not status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No location available"
        )

    # Extract location from Geography type
    # This is a simplified version - in production you'd use proper PostGIS functions
    return {
        "timestamp": status.timestamp,
        "location": "available"  # Replace with actual coordinates extraction
    }
