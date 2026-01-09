-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'user',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Devices (Dongles) table
CREATE TABLE devices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dongle_id VARCHAR(255) UNIQUE NOT NULL,
    owner_id UUID REFERENCES users(id) ON DELETE CASCADE,
    alias VARCHAR(255),
    public_key TEXT,
    is_paired BOOLEAN DEFAULT FALSE,
    serial VARCHAR(255),
    imei VARCHAR(255),
    last_seen TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Routes table
CREATE TABLE routes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id UUID REFERENCES devices(id) ON DELETE CASCADE,
    fullname VARCHAR(255) UNIQUE NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    duration_seconds INTEGER,
    distance_meters FLOAT,
    start_location GEOGRAPHY(POINT, 4326),
    end_location GEOGRAPHY(POINT, 4326),
    path GEOGRAPHY(LINESTRING, 4326),
    upload_complete BOOLEAN DEFAULT FALSE,
    processed BOOLEAN DEFAULT FALSE,
    has_video BOOLEAN DEFAULT FALSE,
    max_camera_points INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Route Segments table
CREATE TABLE route_segments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    route_id UUID REFERENCES routes(id) ON DELETE CASCADE,
    segment_number INTEGER NOT NULL,
    canonical_name VARCHAR(255) NOT NULL,
    duration_seconds INTEGER,
    distance_meters FLOAT,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    log_path VARCHAR(512),
    video_path VARCHAR(512),
    qlog_path VARCHAR(512),
    qcamera_path VARCHAR(512),
    thumbnail_path VARCHAR(512),
    upload_complete BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(route_id, segment_number)
);

-- Events table
CREATE TABLE events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    route_id UUID REFERENCES routes(id) ON DELETE CASCADE,
    segment_id UUID REFERENCES route_segments(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    location GEOGRAPHY(POINT, 4326),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Device Status table
CREATE TABLE device_status (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id UUID REFERENCES devices(id) ON DELETE CASCADE,
    timestamp TIMESTAMP DEFAULT NOW(),
    battery_percent INTEGER,
    temperature_celsius FLOAT,
    memory_usage_mb INTEGER,
    storage_used_gb FLOAT,
    storage_total_gb FLOAT,
    network_type VARCHAR(50),
    openpilot_version VARCHAR(100),
    location GEOGRAPHY(POINT, 4326),
    is_online BOOLEAN DEFAULT TRUE,
    metadata JSONB
);

-- Athena Connections table
CREATE TABLE athena_connections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id UUID REFERENCES devices(id) ON DELETE CASCADE,
    connection_id VARCHAR(255) UNIQUE NOT NULL,
    connected_at TIMESTAMP DEFAULT NOW(),
    disconnected_at TIMESTAMP,
    ip_address INET,
    is_active BOOLEAN DEFAULT TRUE
);

-- User Sessions table
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    ip_address INET,
    user_agent TEXT
);

-- Shared Routes table
CREATE TABLE shared_routes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    route_id UUID REFERENCES routes(id) ON DELETE CASCADE,
    shared_by UUID REFERENCES users(id) ON DELETE CASCADE,
    shared_with UUID REFERENCES users(id) ON DELETE CASCADE,
    permission VARCHAR(50) DEFAULT 'view',
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(route_id, shared_with)
);

-- Standard Indexes
CREATE INDEX idx_routes_device_id ON routes(device_id);
CREATE INDEX idx_routes_start_time ON routes(start_time DESC);
CREATE INDEX idx_routes_fullname ON routes(fullname);
CREATE INDEX idx_route_segments_route_id ON route_segments(route_id);
CREATE INDEX idx_events_route_id ON events(route_id);
CREATE INDEX idx_events_timestamp ON events(timestamp);
CREATE INDEX idx_device_status_device_id ON device_status(device_id);
CREATE INDEX idx_device_status_timestamp ON device_status(timestamp DESC);
CREATE INDEX idx_athena_connections_device_id ON athena_connections(device_id);
CREATE INDEX idx_sessions_user_id ON sessions(user_id);
CREATE INDEX idx_sessions_expires_at ON sessions(expires_at);

-- Spatial indexes (PostGIS)
CREATE INDEX idx_routes_start_location ON routes USING GIST(start_location);
CREATE INDEX idx_routes_path ON routes USING GIST(path);
CREATE INDEX idx_events_location ON events USING GIST(location);
CREATE INDEX idx_device_status_location ON device_status USING GIST(location);

-- Trigger function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply update trigger to relevant tables
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_devices_updated_at BEFORE UPDATE ON devices
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_routes_updated_at BEFORE UPDATE ON routes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
