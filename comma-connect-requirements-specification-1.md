# Requirements Specification - Self-Hosted Comma Connect Server

**Version:** 1.0  
**Date:** January 8, 2026  
**Project:** Open-source implementation of a Comma Connect compatible server for openpilot

---

## 1. Context and Objectives

### 1.1 Background
Comma.ai provides proprietary cloud infrastructure for managing comma devices and visualizing driving data through their Comma Connect application. The backend of this infrastructure is not open-source, creating a dependency on Comma.ai services.

### 1.2 Project Objectives
- **Primary Goal**: Develop a complete and functional Comma Connect backend implementation enabling self-hosting
- **Independence**: Allow users to manage their own data without depending on Comma servers
- **Privacy**: Ensure driving data remains under user control
- **Compatibility**: Ensure full compatibility with existing openpilot devices
- **Simplicity**: Easy deployment via Docker Compose

### 1.3 Scope
**Included in project:**
- Complete REST API backend
- Athena WebSocket service for real-time communication
- Mapping and navigation service
- Media storage and management service
- Customizable web frontend
- Database and caching system
- Complete documentation

**Excluded from project:**
- Modifications to openpilot software itself
- Billing/payment services
- Native mobile application (PWA usage)

---

## 2. Functional Specifications

### 2.1 Device Management

#### 2.1.1 Registration and Authentication
- **Initial pairing**: Device association via QR code or token
- **Authentication**: JWT tokens to secure communications
- **Multi-device**: Support for multiple devices per user
- **Key management**: Automatic token rotation

#### 2.1.2 Device Information
- **Device status**: Battery, temperature, connectivity, software version
- **Location**: Real-time GPS position
- **Configuration**: System parameters, calibration
- **Statistics**: System health data, disk space

### 2.2 Route Management

#### 2.2.1 Data Upload
- **Asynchronous upload**: Support for interrupted and resumed uploads
- **Supported formats**: 
  - Log files (rlog, bz2)
  - Videos (hevc, h264)
  - Telemetry data (can, gps, imu)
- **Chunking**: Upload in chunks for reliability
- **Validation**: File integrity verification

#### 2.2.2 Data Processing
- **Automatic parsing**: Metadata extraction from logs
- **Thumbnail generation**: Video preview creation
- **Transcoding**: Video conversion for web compatibility
- **Indexing**: Database of driving events

#### 2.2.3 Visualization
- **Timeline**: Chronological visualization of routes
- **Interactive map**: Route display on map
- **Statistics**: Distance, duration, average speed, events
- **Replay**: Synchronized playback video + telemetry
- **Events**: Automatic marking (braking, alerts, disengagements)

### 2.3 Athena Service (Command and Control)

#### 2.3.1 Real-time Communication
- **Bidirectional WebSocket**: Persistent connection with device
- **JSON-RPC 2.0**: Standardized command protocol
- **Heartbeat**: Connection maintenance and disconnection detection
- **Automatic reconnection**: Network interruption handling

#### 2.3.2 Supported Commands
- **System status**: `getSystemInfo`, `getStats`
- **Navigation**: `setDestination`, `clearRoute`
- **Snapshot**: `takeSnapshot` (on-demand photo)
- **Configuration**: `getParams`, `setParams`
- **Update**: `checkUpdate`, `installUpdate`
- **Remote control**: `reboot`, `powerOff`

#### 2.3.3 Data Streaming
- **Live telemetry**: Position, speed, real-time status
- **Notifications**: System alerts and events
- **Live logs**: System log streaming

### 2.4 Mapping Service

#### 2.4.1 Map Data
- **Source**: OpenStreetMap (OSM)
- **Vector tiles**: Mapbox Vector Tiles format
- **Local hosting**: Self-hosted tile server
- **Updates**: OSM data update process

#### 2.4.2 Route Calculation
- **Routing engine**: OSRM or Valhalla
- **Profiles**: Car, eco, fast
- **Avoidance**: Areas to avoid, tolls
- **Alternative routes**: Multiple option calculation

#### 2.4.3 Points of Interest
- **Search**: Address and POI search
- **Geocoding**: Address ↔ coordinates conversion
- **Favorites**: Favorite location management

### 2.5 User Management

#### 2.5.1 User Accounts
- **Registration**: Account creation (email + password)
- **Authentication**: Login with JWT
- **Profiles**: Personal information, preferences
- **Multi-user**: Support for multiple users per instance

#### 2.5.2 Permissions and Roles
- **Roles**: Admin, User, Viewer
- **Granular permissions**: Read, write, delete
- **Sharing**: Route sharing with other users

### 2.6 Web Frontend

#### 2.6.1 User Interface
- **Dashboard**: Overview of devices and recent routes
- **Interactive map**: Geographic visualization
- **Timeline**: Chronological list of routes
- **Video player**: Route replay with data synchronization
- **Settings**: Device and account configuration

#### 2.6.2 Features
- **Responsive**: Mobile, tablet, desktop adaptation
- **PWA**: Installation as application
- **Offline mode**: Data caching for offline viewing
- **Dark/Light theme**: Theme switcher
- **Internationalization**: Multi-language support

---

## 3. Technical Specifications

### 3.1 Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                         OPENPILOT DEVICE                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Camera     │  │  Telemetry   │  │   Location   │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                  │                  │              │
│         └──────────────────┴──────────────────┘              │
│                            │                                 │
│                    ┌───────▼────────┐                        │
│                    │  Athena Client │                        │
│                    └───────┬────────┘                        │
└────────────────────────────┼──────────────────────────────────┘
                             │
                    ┌────────▼────────┐
                    │  Internet/LAN   │
                    └────────┬────────┘
                             │
┌────────────────────────────┼──────────────────────────────────┐
│                    SELF-HOSTED SERVER                         │
│                             │                                 │
│  ┌──────────────────────────▼──────────────────────────────┐ │
│  │              NGINX Reverse Proxy + SSL                   │ │
│  └──┬────────────┬──────────────┬──────────────┬───────────┘ │
│     │            │              │              │             │
│  ┌──▼────┐  ┌───▼─────┐  ┌─────▼────┐  ┌─────▼──────┐     │
│  │ API   │  │ Athena  │  │  Maps    │  │  Frontend  │     │
│  │Service│  │WebSocket│  │ Service  │  │    (PWA)   │     │
│  └──┬────┘  └───┬─────┘  └─────┬────┘  └────────────┘     │
│     │            │              │                            │
│  ┌──▼────────────▼──────────────▼─────┐                     │
│  │         Redis Cache                 │                     │
│  └──┬──────────────────────────────────┘                     │
│     │                                                         │
│  ┌──▼──────────────────────────────────┐                     │
│  │      PostgreSQL Database            │                     │
│  └─────────────────────────────────────┘                     │
│                                                               │
│  ┌─────────────────────────────────────┐                     │
│  │     MinIO Object Storage            │                     │
│  │  (Videos, Logs, Thumbnails)         │                     │
│  └─────────────────────────────────────┘                     │
│                                                               │
│  ┌─────────────────────────────────────┐                     │
│  │    Background Workers               │                     │
│  │  (Video processing, Log parsing)    │                     │
│  └─────────────────────────────────────┘                     │
└───────────────────────────────────────────────────────────────┘
```

### 3.2 Technology Stack

#### 3.2.1 Backend Services
```yaml
API Service:
  Language: Python 3.11+
  Framework: FastAPI
  Purpose: REST API, authentication, business logic
  
Athena WebSocket:
  Language: Python 3.11+ or Go 1.21+
  Framework: FastAPI/WebSockets or Gorilla WebSocket
  Purpose: Real-time device communication
  
Maps Service:
  Tile Server: tileserver-gl (OpenMapTiles)
  Routing: OSRM Backend
  Geocoding: Nominatim
  
Worker Service:
  Framework: Celery (Python) or custom Go workers
  Purpose: Async processing, video encoding, log parsing
```

#### 3.2.2 Data Storage
```yaml
Database:
  Primary: PostgreSQL 15+
  Features:
    - PostGIS extension for geo queries
    - Full-text search
    - JSON support for flexible schemas
  
Cache:
  Primary: Redis 7+
  Features:
    - Session storage
    - API rate limiting
    - Real-time data caching
  
Object Storage:
  Solution: MinIO
  Purpose:
    - Video files (.hevc, .mp4)
    - Log files (.rlog, .bz2)
    - Thumbnails and previews
  Features:
    - S3-compatible API
    - Automatic data distribution
    - Lifecycle policies
```

#### 3.2.3 Frontend
```yaml
Framework: React 18+ with TypeScript
Build Tool: Vite
State Management: Redux Toolkit or Zustand
UI Library: 
  - Material-UI (MUI) or Shadcn/ui
  - TailwindCSS for styling
Map Library: Mapbox GL JS or MapLibre GL
Video Player: Video.js or custom HLS player
Charts: Recharts or Chart.js
```

#### 3.2.4 Infrastructure
```yaml
Containerization: Docker + Docker Compose
Reverse Proxy: Nginx
SSL/TLS: Let's Encrypt (Certbot)
Monitoring: 
  - Prometheus + Grafana
  - Loki for logs
CI/CD: GitHub Actions
```

### 3.3 Database Schema

#### 3.3.1 Core Tables

```sql
-- Users
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'user',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Devices (Dongles)
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

-- Routes
CREATE TABLE routes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id UUID REFERENCES devices(id) ON DELETE CASCADE,
    fullname VARCHAR(255) UNIQUE NOT NULL, -- dongle_id|timestamp
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    duration_seconds INTEGER,
    distance_meters FLOAT,
    start_location GEOGRAPHY(POINT),
    end_location GEOGRAPHY(POINT),
    path GEOGRAPHY(LINESTRING),
    upload_complete BOOLEAN DEFAULT FALSE,
    processed BOOLEAN DEFAULT FALSE,
    has_video BOOLEAN DEFAULT FALSE,
    max_camera_points INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Route Segments
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

-- Events
CREATE TABLE events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    route_id UUID REFERENCES routes(id) ON DELETE CASCADE,
    segment_id UUID REFERENCES route_segments(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL, -- 'alert', 'disengage', 'engagement', etc.
    timestamp TIMESTAMP NOT NULL,
    location GEOGRAPHY(POINT),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Device Status
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
    location GEOGRAPHY(POINT),
    is_online BOOLEAN DEFAULT TRUE,
    metadata JSONB
);

-- Athena Connections
CREATE TABLE athena_connections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id UUID REFERENCES devices(id) ON DELETE CASCADE,
    connection_id VARCHAR(255) UNIQUE NOT NULL,
    connected_at TIMESTAMP DEFAULT NOW(),
    disconnected_at TIMESTAMP,
    ip_address INET,
    is_active BOOLEAN DEFAULT TRUE
);

-- User Sessions
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    ip_address INET,
    user_agent TEXT
);

-- Shared Routes
CREATE TABLE shared_routes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    route_id UUID REFERENCES routes(id) ON DELETE CASCADE,
    shared_by UUID REFERENCES users(id) ON DELETE CASCADE,
    shared_with UUID REFERENCES users(id) ON DELETE CASCADE,
    permission VARCHAR(50) DEFAULT 'view', -- 'view', 'comment'
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(route_id, shared_with)
);

-- Indexes
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
```

### 3.4 API Endpoints

#### 3.4.1 Authentication API
```
POST   /api/v1/auth/register              - User registration
POST   /api/v1/auth/login                 - User login
POST   /api/v1/auth/refresh               - Refresh JWT token
POST   /api/v1/auth/logout                - Logout
GET    /api/v1/auth/me                    - Get current user info
```

#### 3.4.2 Device API
```
GET    /api/v1/devices                    - List user's devices
GET    /api/v1/devices/{dongle_id}        - Get device details
POST   /api/v1/devices                    - Register new device
PUT    /api/v1/devices/{dongle_id}        - Update device (alias, etc)
DELETE /api/v1/devices/{dongle_id}        - Remove device
GET    /api/v1/devices/{dongle_id}/status - Get device status
GET    /api/v1/devices/{dongle_id}/location - Get device location
POST   /api/v1/devices/{dongle_id}/pair   - Pair device
```

#### 3.4.3 Routes API
```
GET    /api/v1/routes                     - List routes (paginated)
GET    /api/v1/routes/{route_name}        - Get route details
GET    /api/v1/routes/{route_name}/segments - Get route segments
GET    /api/v1/routes/{route_name}/events - Get route events
DELETE /api/v1/routes/{route_name}        - Delete route
GET    /api/v1/routes/{route_name}/video  - Stream video
GET    /api/v1/routes/{route_name}/log    - Download log
GET    /api/v1/routes/{route_name}/thumbnail - Get thumbnail
POST   /api/v1/routes/{route_name}/share  - Share route
```

#### 3.4.4 Upload API
```
POST   /api/v1/upload/init                - Initialize upload session
POST   /api/v1/upload/chunk               - Upload chunk
POST   /api/v1/upload/complete            - Complete upload
POST   /api/v1/upload/cancel              - Cancel upload
GET    /api/v1/upload/presigned           - Get presigned URL (S3)
```

#### 3.4.5 Maps API
```
GET    /api/v1/maps/tiles/{z}/{x}/{y}     - Get map tile
POST   /api/v1/maps/route                 - Calculate route
GET    /api/v1/maps/geocode               - Geocode address
GET    /api/v1/maps/reverse               - Reverse geocode
GET    /api/v1/maps/search                - Search POI
```

#### 3.4.6 Athena WebSocket
```
WS     /ws/athena/{dongle_id}             - WebSocket connection

Commands (JSON-RPC 2.0):
{
  "method": "getSystemInfo",
  "params": {},
  "id": 1
}

{
  "method": "takeSnapshot",
  "params": {},
  "id": 2
}

{
  "method": "setDestination", 
  "params": {"lat": 37.7749, "lon": -122.4194},
  "id": 3
}
```

### 3.5 Docker Compose Configuration

#### 3.5.1 Services Overview
```yaml
services:
  - nginx: Reverse proxy and SSL termination
  - api: Main REST API service
  - athena: WebSocket service
  - worker: Background task processor
  - frontend: React web application
  - postgres: Primary database
  - redis: Cache and session storage
  - minio: Object storage
  - tile-server: Map tile server
  - routing: OSRM routing engine
  - monitoring: Prometheus + Grafana
```

#### 3.5.2 Resource Requirements

**Minimum Configuration:**
```
CPU: 4 cores
RAM: 8 GB
Storage: 100 GB (expandable for video storage)
Network: 100 Mbps
```

**Recommended Configuration:**
```
CPU: 8+ cores
RAM: 16+ GB
Storage: 500 GB - 2 TB SSD
Network: 1 Gbps
```

**Storage Planning:**
- Database: ~10 GB per 10,000 routes
- Video: ~1-2 GB per hour of driving
- Logs: ~100-200 MB per hour
- Map tiles: ~50-100 GB (full planet)

### 3.6 Security Requirements

#### 3.6.1 Authentication & Authorization
- JWT tokens with 1-hour expiration
- Refresh tokens with 30-day expiration
- HTTPS only (redirect HTTP to HTTPS)
- Password requirements: min 12 chars, complexity rules
- Rate limiting on login attempts (5 attempts per 15 min)
- CORS configuration for frontend domain only

#### 3.6.2 Data Security
- Passwords hashed with bcrypt (cost 12)
- JWT secrets stored in environment variables
- Database credentials in Docker secrets
- API keys encrypted at rest
- TLS 1.3 for all connections
- Regular security updates (automated)

#### 3.6.3 Privacy
- No telemetry or tracking
- User data never shared
- GDPR-compliant data export
- Right to deletion implemented
- Audit logs for admin actions

### 3.7 Performance Requirements

#### 3.7.1 API Performance
- API response time: < 200ms (p95)
- WebSocket latency: < 100ms
- Video streaming: smooth playback at 1080p
- Concurrent users: 100+ per instance
- Upload speed: limited by network, not server

#### 3.7.2 Scalability
- Horizontal scaling support (multiple API instances)
- Database connection pooling
- CDN support for static assets
- Background job queuing
- Auto-scaling workers based on load

---

## 4. Development Phases

### Phase 1: Core Infrastructure (Weeks 1-3)
**Deliverables:**
- [x] Docker Compose setup
- [x] PostgreSQL schema
- [x] Basic API framework (FastAPI)
- [x] Authentication system
- [x] User registration/login
- [x] Device pairing

**Acceptance Criteria:**
- User can create account
- User can pair a device
- Basic API endpoints operational

### Phase 2: Data Upload & Storage (Weeks 4-6)
**Deliverables:**
- [x] MinIO object storage integration
- [x] Chunked upload endpoint
- [x] Route creation and management
- [x] Basic log parsing
- [x] Video storage

**Acceptance Criteria:**
- openpilot device can upload logs
- Videos stored and accessible
- Basic route information extracted

### Phase 3: Athena WebSocket (Weeks 7-9)
**Deliverables:**
- [x] WebSocket server
- [x] JSON-RPC handler
- [x] Basic commands (getSystemInfo, takeSnapshot)
- [x] Heartbeat mechanism
- [x] Connection management

**Acceptance Criteria:**
- Device connects via WebSocket
- Commands execute successfully
- Real-time telemetry streams

### Phase 4: Frontend Development (Weeks 10-14)
**Deliverables:**
- [x] React application setup
- [x] Dashboard page
- [x] Route list and details
- [x] Map integration
- [x] Video player
- [x] Device management UI

**Acceptance Criteria:**
- Users can view all routes
- Map displays route path
- Video playback functional
- Mobile responsive

### Phase 5: Maps & Navigation (Weeks 15-17)
**Deliverables:**
- [x] OSM tile server
- [x] OSRM routing
- [x] Geocoding service
- [x] Navigation UI
- [x] POI search

**Acceptance Criteria:**
- Map tiles load quickly
- Route calculation works
- Address search functional

### Phase 6: Advanced Features (Weeks 18-20)
**Deliverables:**
- [x] Video transcoding
- [x] Thumbnail generation
- [x] Event detection and marking
- [x] Statistics calculations
- [x] Sharing functionality

**Acceptance Criteria:**
- Videos play in browser
- Thumbnails auto-generated
- Events automatically detected

### Phase 7: Testing & Optimization (Weeks 21-23)
**Deliverables:**
- [x] Unit tests (>80% coverage)
- [x] Integration tests
- [x] Performance optimization
- [x] Security audit
- [x] Load testing

**Acceptance Criteria:**
- All tests pass
- Performance targets met
- No critical security issues

### Phase 8: Documentation & Release (Week 24)
**Deliverables:**
- [x] User documentation
- [x] Admin documentation
- [x] API documentation (OpenAPI/Swagger)
- [x] Deployment guide
- [x] Video tutorials

**Acceptance Criteria:**
- Complete documentation available
- Deployment tested on fresh server
- README with quick start guide

---

## 5. Testing Strategy

### 5.1 Unit Testing
```
Target Coverage: 80%+
Framework: pytest (Python), Jest (JavaScript)
Scope:
  - API endpoint logic
  - Database models
  - Business logic functions
  - Frontend components
```

### 5.2 Integration Testing
```
Tools: pytest with test client, Playwright for frontend
Scope:
  - API endpoint workflows
  - Database transactions
  - Authentication flows
  - WebSocket connections
```

### 5.3 End-to-End Testing
```
Tools: Playwright or Cypress
Scenarios:
  - User registration → device pairing → route upload → viewing
  - Live device connection → command execution
  - Route sharing workflow
```

### 5.4 Performance Testing
```
Tools: Locust or k6
Metrics:
  - API response times under load
  - Concurrent WebSocket connections
  - Video streaming performance
  - Database query performance
```

### 5.5 Security Testing
```
Tools: OWASP ZAP, Bandit, npm audit
Checks:
  - SQL injection vulnerabilities
  - XSS vulnerabilities
  - Authentication bypass attempts
  - Dependency vulnerabilities
```

---

## 6. Deployment & Operations

### 6.1 Installation Methods

#### Method 1: Docker Compose (Recommended)
```bash
git clone https://github.com/yourorg/comma-connect-server
cd comma-connect-server
cp .env.example .env
# Edit .env with your configuration
docker-compose up -d
```

#### Method 2: Manual Installation
```bash
# Install dependencies
# Build services
# Configure database
# Run migrations
# Start services
```

### 6.2 Configuration

**Environment Variables:**
```bash
# Database
DATABASE_URL=postgresql://user:pass@postgres:5432/commaconnect
REDIS_URL=redis://redis:6379/0

# Object Storage
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=admin
MINIO_SECRET_KEY=supersecret
MINIO_BUCKET=comma-uploads

# Security
JWT_SECRET=your-secret-key-min-32-chars
JWT_EXPIRATION=3600
REFRESH_TOKEN_EXPIRATION=2592000

# Server
API_HOST=0.0.0.0
API_PORT=8000
DOMAIN=connect.yourdomain.com
ENABLE_HTTPS=true

# Maps
OSM_TILE_SERVER=http://tile-server:8080
OSRM_SERVER=http://routing:5000

# Features
ENABLE_REGISTRATION=true
ENABLE_SHARING=true
MAX_UPLOAD_SIZE=10737418240  # 10GB
```

### 6.3 Backup Strategy

**Database Backups:**
```bash
# Daily automated backups
0 2 * * * docker exec postgres pg_dump -U user commaconnect | gzip > backup_$(date +\%Y\%m\%d).sql.gz

# Retention: 7 daily, 4 weekly, 12 monthly
```

**Object Storage Backups:**
```bash
# Use MinIO mirroring or S3 sync
# Backup critical data only (not all videos)
# Consider external storage for redundancy
```

### 6.4 Monitoring

**Metrics to Track:**
- API request rate and latency
- Database connection pool usage
- Disk space usage
- CPU and memory utilization
- Active WebSocket connections
- Upload success rate
- Error rates by endpoint

**Alerting:**
- Disk space < 10% remaining
- API error rate > 5%
- Database down
- Any service crash
- SSL certificate expiring soon

### 6.5 Maintenance

**Regular Tasks:**
- Weekly: Review error logs
- Monthly: Database vacuum and analyze
- Quarterly: Security updates
- Annually: SSL certificate renewal (auto with Let's Encrypt)

**Database Maintenance:**
```sql
-- Weekly vacuum
VACUUM ANALYZE;

-- Clean old sessions
DELETE FROM sessions WHERE expires_at < NOW() - INTERVAL '7 days';

-- Clean orphaned data
DELETE FROM route_segments WHERE route_id NOT IN (SELECT id FROM routes);
```

---

## 7. Documentation Requirements

### 7.1 User Documentation
- Quick start guide
- Device pairing instructions
- Route viewing tutorial
- Sharing routes guide
- FAQ
- Troubleshooting common issues

### 7.2 Admin Documentation
- Installation guide
- Configuration reference
- Backup and restore procedures
- Upgrade guide
- Performance tuning
- Security best practices

### 7.3 Developer Documentation
- Architecture overview
- API reference (OpenAPI/Swagger)
- Database schema
- Contributing guide
- Code style guide
- Testing guide

### 7.4 API Documentation
- OpenAPI 3.0 specification
- Interactive API explorer (Swagger UI)
- Authentication examples
- Rate limiting information
- Error code reference
- Webhook documentation

---

## 8. Success Criteria

### 8.1 Functional Success
- [x] All core features implemented
- [x] Compatible with openpilot devices
- [x] Frontend provides good UX
- [x] All tests passing
- [x] Documentation complete

### 8.2 Performance Success
- [x] API response time < 200ms (p95)
- [x] Video streaming smooth
- [x] Supports 100+ concurrent users
- [x] Upload speed not bottlenecked by server
- [x] WebSocket latency < 100ms

### 8.3 Reliability Success
- [x] 99.9% uptime
- [x] Zero data loss
- [x] Graceful error handling
- [x] Automatic recovery from failures
- [x] Successful backups daily

### 8.4 Security Success
- [x] No critical security vulnerabilities
- [x] HTTPS enforced
- [x] Authentication works correctly
- [x] Rate limiting effective
- [x] Passes security audit

### 8.5 Usability Success
- [x] Can deploy in < 30 minutes
- [x] Clear documentation
- [x] Intuitive UI
- [x] Mobile-friendly
- [x] Positive user feedback

---

## 9. Future Enhancements

### 9.1 Phase 2 Features (Post-Launch)
- **Advanced Analytics**: Driving score, safety metrics
- **Social Features**: Driver profiles, leaderboards
- **Machine Learning**: Event detection improvement
- **Mobile Apps**: Native iOS/Android apps
- **Plugin System**: Third-party integrations
- **Multi-language**: i18n support
- **Export Tools**: Export data to other formats

### 9.2 Enterprise Features
- **SSO Integration**: LDAP, OAuth providers
- **Fleet Management**: Manage multiple devices
- **Advanced Permissions**: Role-based access control
- **API Rate Tiers**: Different limits per user
- **White-labeling**: Custom branding
- **SLA Guarantees**: Uptime commitments

### 9.3 Community Features
- **Public Routes**: Share routes publicly
- **Forums**: Discussion boards
- **Plugins**: Community plugins
- **Themes**: Custom UI themes
- **Translations**: Community translations

---

## 10. Risks and Mitigation

### 10.1 Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Openpilot API changes | Medium | High | Version detection, fallback modes |
| Storage costs | High | Medium | Compression, lifecycle policies |
| Performance at scale | Medium | High | Horizontal scaling, caching |
| Video transcoding load | High | Medium | Queue system, hardware encoding |
| Database growth | High | Medium | Partitioning, archiving old data |

### 10.2 Security Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Unauthorized access | Medium | Critical | Strong auth, rate limiting |
| Data breach | Low | Critical | Encryption, security audits |
| DDoS attack | Medium | High | Cloudflare, rate limiting |
| Malicious uploads | Medium | Medium | Virus scanning, validation |

### 10.3 Operational Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Data loss | Low | Critical | Regular backups, redundancy |
| Service downtime | Medium | High | Monitoring, auto-restart |
| Insufficient storage | High | High | Monitoring, cleanup policies |
| Network issues | Medium | Medium | Retry logic, offline mode |

---

## 11. Appendices

### 11.1 Glossary

**Terms:**
- **Dongle**: The comma device (comma 3, comma 3X)
- **Route**: A driving session from start to stop
- **Segment**: A subdivision of a route (typically 1 minute)
- **Athena**: Real-time communication protocol with device
- **rlog**: Comma log file format (capnproto)
- **HEVC**: Video codec used by comma devices

### 11.2 References

**Official Documentation:**
- [openpilot GitHub](https://github.com/commaai/openpilot)
- [Comma Connect GitHub](https://github.com/commaai/connect)
- [Comma API Unofficial Docs](https://github.com/commaai/connect/wiki)

**Technical References:**
- FastAPI: https://fastapi.tiangolo.com
- Docker Compose: https://docs.docker.com/compose
- PostgreSQL + PostGIS: https://postgis.net
- OSRM: http://project-osrm.org
- Mapbox GL JS: https://docs.mapbox.com/mapbox-gl-js

### 11.3 Contributors

**Project Roles:**
- Project Manager
- Backend Developer (Python/Go)
- Frontend Developer (React)
- DevOps Engineer
- QA Engineer
- Technical Writer

---

**Document Status:** Draft v1.0  
**Last Updated:** January 8, 2026  
**Next Review:** As needed during development