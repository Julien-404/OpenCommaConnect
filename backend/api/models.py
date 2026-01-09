from sqlalchemy import Column, String, Boolean, Integer, Float, DateTime, ForeignKey, Text, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID, INET, JSONB
from sqlalchemy.orm import relationship
from geoalchemy2 import Geography
from datetime import datetime
import uuid

from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(255))
    role = Column(String(50), default="user")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    devices = relationship("Device", back_populates="owner", cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")

class Device(Base):
    __tablename__ = "devices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dongle_id = Column(String(255), unique=True, nullable=False, index=True)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    alias = Column(String(255))
    public_key = Column(Text)
    is_paired = Column(Boolean, default=False)
    serial = Column(String(255))
    imei = Column(String(255))
    last_seen = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner = relationship("User", back_populates="devices")
    routes = relationship("Route", back_populates="device", cascade="all, delete-orphan")
    status_records = relationship("DeviceStatus", back_populates="device", cascade="all, delete-orphan")
    connections = relationship("AthenaConnection", back_populates="device", cascade="all, delete-orphan")

class Route(Base):
    __tablename__ = "routes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"), index=True)
    fullname = Column(String(255), unique=True, nullable=False, index=True)
    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime)
    duration_seconds = Column(Integer)
    distance_meters = Column(Float)
    start_location = Column(Geography(geometry_type='POINT', srid=4326))
    end_location = Column(Geography(geometry_type='POINT', srid=4326))
    path = Column(Geography(geometry_type='LINESTRING', srid=4326))
    upload_complete = Column(Boolean, default=False)
    processed = Column(Boolean, default=False)
    has_video = Column(Boolean, default=False)
    max_camera_points = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    device = relationship("Device", back_populates="routes")
    segments = relationship("RouteSegment", back_populates="route", cascade="all, delete-orphan")
    events = relationship("Event", back_populates="route", cascade="all, delete-orphan")
    shares = relationship("SharedRoute", back_populates="route", cascade="all, delete-orphan")

class RouteSegment(Base):
    __tablename__ = "route_segments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    route_id = Column(UUID(as_uuid=True), ForeignKey("routes.id", ondelete="CASCADE"), index=True)
    segment_number = Column(Integer, nullable=False)
    canonical_name = Column(String(255), nullable=False)
    duration_seconds = Column(Integer)
    distance_meters = Column(Float)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    log_path = Column(String(512))
    video_path = Column(String(512))
    qlog_path = Column(String(512))
    qcamera_path = Column(String(512))
    thumbnail_path = Column(String(512))
    upload_complete = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    route = relationship("Route", back_populates="segments")
    events = relationship("Event", back_populates="segment", cascade="all, delete-orphan")

class Event(Base):
    __tablename__ = "events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    route_id = Column(UUID(as_uuid=True), ForeignKey("routes.id", ondelete="CASCADE"), index=True)
    segment_id = Column(UUID(as_uuid=True), ForeignKey("route_segments.id", ondelete="CASCADE"))
    event_type = Column(String(50), nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)
    location = Column(Geography(geometry_type='POINT', srid=4326))
    metadata = Column(JSONB)
    created_at = Column(DateTime, default=datetime.utcnow)

    route = relationship("Route", back_populates="events")
    segment = relationship("RouteSegment", back_populates="events")

class DeviceStatus(Base):
    __tablename__ = "device_status"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"), index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    battery_percent = Column(Integer)
    temperature_celsius = Column(Float)
    memory_usage_mb = Column(Integer)
    storage_used_gb = Column(Float)
    storage_total_gb = Column(Float)
    network_type = Column(String(50))
    openpilot_version = Column(String(100))
    location = Column(Geography(geometry_type='POINT', srid=4326))
    is_online = Column(Boolean, default=True)
    metadata = Column(JSONB)

    device = relationship("Device", back_populates="status_records")

class AthenaConnection(Base):
    __tablename__ = "athena_connections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"), index=True)
    connection_id = Column(String(255), unique=True, nullable=False)
    connected_at = Column(DateTime, default=datetime.utcnow)
    disconnected_at = Column(DateTime)
    ip_address = Column(INET)
    is_active = Column(Boolean, default=True)

    device = relationship("Device", back_populates="connections")

class Session(Base):
    __tablename__ = "sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token_hash = Column(String(255), unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    ip_address = Column(INET)
    user_agent = Column(Text)

    user = relationship("User", back_populates="sessions")

class SharedRoute(Base):
    __tablename__ = "shared_routes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    route_id = Column(UUID(as_uuid=True), ForeignKey("routes.id", ondelete="CASCADE"))
    shared_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    shared_with = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    permission = Column(String(50), default="view")
    created_at = Column(DateTime, default=datetime.utcnow)

    route = relationship("Route", back_populates="shares")
