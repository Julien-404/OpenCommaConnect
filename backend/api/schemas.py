from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID

# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    name: Optional[str] = None

class UserCreate(UserBase):
    password: str = Field(..., min_length=12)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(UserBase):
    id: UUID
    role: str
    created_at: datetime

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

# Device Schemas
class DeviceBase(BaseModel):
    dongle_id: str
    alias: Optional[str] = None

class DeviceCreate(DeviceBase):
    public_key: Optional[str] = None

class DevicePair(BaseModel):
    dongle_id: str
    pairing_token: str

class DeviceResponse(DeviceBase):
    id: UUID
    is_paired: bool
    serial: Optional[str] = None
    last_seen: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

class DeviceStatusResponse(BaseModel):
    battery_percent: Optional[int] = None
    temperature_celsius: Optional[float] = None
    memory_usage_mb: Optional[int] = None
    storage_used_gb: Optional[float] = None
    storage_total_gb: Optional[float] = None
    network_type: Optional[str] = None
    openpilot_version: Optional[str] = None
    is_online: bool
    timestamp: datetime

    class Config:
        from_attributes = True

# Route Schemas
class RouteBase(BaseModel):
    fullname: str
    start_time: datetime

class RouteCreate(RouteBase):
    device_id: UUID
    end_time: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    distance_meters: Optional[float] = None

class RouteResponse(RouteBase):
    id: UUID
    device_id: UUID
    end_time: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    distance_meters: Optional[float] = None
    upload_complete: bool
    processed: bool
    has_video: bool
    created_at: datetime

    class Config:
        from_attributes = True

class RouteListResponse(BaseModel):
    routes: List[RouteResponse]
    total: int
    page: int
    page_size: int

# Route Segment Schemas
class RouteSegmentResponse(BaseModel):
    id: UUID
    segment_number: int
    canonical_name: str
    duration_seconds: Optional[int] = None
    distance_meters: Optional[float] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    upload_complete: bool
    has_video: bool = Field(default=False)
    has_log: bool = Field(default=False)

    class Config:
        from_attributes = True

    @property
    def has_video(self) -> bool:
        return self.video_path is not None

    @property
    def has_log(self) -> bool:
        return self.log_path is not None

# Event Schemas
class EventResponse(BaseModel):
    id: UUID
    event_type: str
    timestamp: datetime
    metadata: Optional[dict] = None

    class Config:
        from_attributes = True

# Upload Schemas
class UploadInitRequest(BaseModel):
    route_name: str
    segment_number: int
    file_type: str  # 'log', 'video', 'qlog', 'qcamera'
    file_size: int

class UploadInitResponse(BaseModel):
    upload_id: str
    presigned_url: str
    chunk_size: int = 10485760  # 10MB

class UploadCompleteRequest(BaseModel):
    upload_id: str
    parts: List[dict]

# Health Check
class HealthResponse(BaseModel):
    status: str
    database: str
    redis: str
    timestamp: datetime
