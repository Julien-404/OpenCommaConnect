# Quick Start Guide

Get your Comma Connect server running in 5 minutes!

## ⚠️ Before You Start

**This project requires a reverse proxy** (Traefik, Caddy, Nginx, etc.)

- For **production**: Use your existing reverse proxy (see [DEPLOYMENT.md](./DEPLOYMENT.md))
- For **testing**: Use the optional built-in proxy (instructions below)

## Prerequisites

- Docker and Docker Compose installed
- Minimum 8GB RAM, 4 CPU cores
- 100GB+ storage
- **A reverse proxy** (Traefik, Caddy, Nginx, cloud LB, etc.)
- Domain name (optional for testing)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourorg/comma-connect-server
cd comma-connect-server
```

### 2. Run Setup Script

```bash
./scripts/setup.sh
```

This will:
- Create `.env` file from example
- Prompt you to configure environment variables
- Create necessary directories
- Generate SSL certificates for testing

### 3. Configure Environment

Edit the `.env` file and set:

```bash
# Required settings
POSTGRES_PASSWORD=your_secure_password_here
MINIO_ROOT_PASSWORD=your_minio_password_here
JWT_SECRET=your_jwt_secret_min_32_characters_long
GRAFANA_ADMIN_PASSWORD=your_grafana_password_here

# Domain (use 'localhost' for testing)
DOMAIN=localhost
ENABLE_HTTPS=false
```

**Generate secure secrets:**

```bash
# JWT Secret (min 32 characters)
openssl rand -base64 32

# Passwords
openssl rand -base64 16
```

### 4. Start the Server

**Option A: With Your Own Reverse Proxy (Production)**

```bash
docker-compose up -d
```

This starts all backend services. Configure your reverse proxy to route traffic to:
- Frontend: `localhost:3000`
- API: `localhost:8000`
- WebSocket: `ws://localhost:8001`

See [examples/](./examples/) for Traefik, Caddy, and Nginx configurations.

**Option B: For Testing Only (Built-in Proxy)**

```bash
docker-compose -f docker-compose.yml -f docker-compose.proxy.yml up -d
```

This includes a basic Nginx proxy. Access at `http://localhost`

Services started:
- API server
- Athena WebSocket service
- PostgreSQL database
- Redis cache
- MinIO object storage
- Monitoring stack (Prometheus, Grafana)
- Frontend (React PWA)
- Optional: Basic Nginx proxy (only with option B)

### 5. Wait for Services to Start

```bash
# Check service status
docker-compose ps

# Watch logs
docker-compose logs -f

# Wait until all services are healthy (30-60 seconds)
```

### 6. Access the Application

Open your browser and navigate to:

- **Frontend**: http://localhost
- **Grafana**: http://localhost:3000 (admin/[your_password])
- **MinIO Console**: http://localhost:9001

### 7. Create Your Account

1. Click "Register" on the login page
2. Enter your email and password
3. Log in with your credentials

### 8. Add Your Comma Device

1. Go to "Devices" page
2. Click "Add Device"
3. Enter your device's dongle ID
4. Follow pairing instructions

## Configure Your Comma Device

SSH into your comma device:

```bash
ssh comma@192.168.x.x
```

Run this script:

```bash
URL="http://your-server-ip"
WEBSOCKET_URL="ws://your-server-ip"

cd /data/openpilot

# Add configuration
sed -i '3i # Self-hosted server configuration' launch_env.sh
sed -i "4i export ATHENA_HOST=\"$WEBSOCKET_URL\"" launch_env.sh
sed -i "5i export API_HOST=\"$URL\"" launch_env.sh
sed -i "6i export MAPS_HOST=\"$URL\"" launch_env.sh

# Reboot
sudo reboot
```

## Verify Everything Works

### Test API

```bash
./scripts/test-api.sh http://localhost:8000
```

### Check Health

```bash
curl http://localhost:8000/health
```

Should return:
```json
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected",
  "timestamp": "2024-01-08T12:00:00"
}
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f athena
```

## Troubleshooting

### Services won't start

```bash
# Check logs for errors
docker-compose logs

# Restart specific service
docker-compose restart api

# Rebuild and restart
docker-compose up -d --build
```

### Database connection errors

```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Check database logs
docker-compose logs postgres
```

### Can't connect from device

1. Check firewall allows connections on port 80/443
2. Verify ATHENA_HOST and API_HOST are correct
3. Check device can reach server: `ping your-server-ip`

### MinIO not working

```bash
# Check MinIO status
docker-compose ps minio

# Verify buckets exist
docker-compose exec minio mc ls myminio/
```

## Next Steps

1. **Add Map Data**: Download OSM data for your region
   ```bash
   cd maps/osm
   wget https://download.geofabrik.de/north-america/us/california-latest.osm.pbf -O map.osm.pbf
   docker-compose up routing-prepare
   ```

2. **Configure SSL**: For production, set up proper SSL certificates
   ```bash
   ./scripts/setup-ssl.sh your-domain.com
   ```

3. **Setup Backups**: Configure automated backups in docker-compose.yml

4. **Monitor System**: Access Grafana at http://localhost:3000

## Production Deployment

For production:

1. Use a proper domain name
2. Configure SSL/TLS (Let's Encrypt)
3. Set strong passwords
4. Configure firewall (allow 80, 443)
5. Setup automated backups
6. Monitor system resources

See [README.md](README.md) for detailed production setup.

## Getting Help

- 📖 [Full Documentation](./README.md)
- 🐛 [Report Issues](https://github.com/yourorg/comma-connect-server/issues)
- 💬 [Discord Community](https://discord.gg/your-invite)
- 📧 Email: support@your-domain.com

## What's Next?

- Drive with your comma device
- Watch routes appear in the web interface
- View driving statistics
- Share routes with friends
- Customize your setup

Happy driving! 🚗
