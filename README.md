# Comma Connect Self-Hosted Server

Open-source implementation of the Comma Connect backend for self-hosting your openpilot data.

## ⚠️ Reverse Proxy Required

**This project does NOT include a reverse proxy by default.**

You must provide your own reverse proxy to access the services securely. This design allows:
- ✅ Integration with your existing infrastructure
- ✅ Use of your preferred proxy (Traefik, Caddy, Nginx, etc.)
- ✅ Flexibility for cloud deployments (AWS ALB, GCP LB, etc.)
- ✅ No forced SSL configuration

**Recommended Reverse Proxies:**
- 🌐 **Traefik** - Best for Docker, automatic SSL (Recommended)
- 🚀 **Caddy** - Easiest, automatic HTTPS
- ⚙️ **Nginx** - Most common, highly configurable
- ☁️ **Cloud Load Balancers** - AWS ALB, GCP, Azure

**Need a quick test proxy?**
We provide an optional basic Nginx configuration:
```bash
docker-compose -f docker-compose.yml -f docker-compose.proxy.yml up -d
```

📖 **See [DEPLOYMENT.md](./DEPLOYMENT.md) and [examples/](./examples/) for reverse proxy configuration guides**

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose installed
- Minimum 8GB RAM, 4 CPU cores, 100GB storage
- Domain name (optional, can use localhost for testing)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourorg/comma-connect-server
cd comma-connect-server
```

2. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your settings
nano .env
```

3. **Generate secrets**
```bash
# JWT Secret (min 32 characters)
openssl rand -base64 32

# Database Password
openssl rand -base64 16

# MinIO Password
openssl rand -base64 16
```

4. **Start the services**

```bash
docker-compose up -d
```

This starts all backend services. They expose ports directly:
- Frontend: `http://localhost:3000`
- API: `http://localhost:8000`
- WebSocket: `ws://localhost:8001`
- Grafana: `http://localhost:3000`
- MinIO Console: `http://localhost:9001`

5. **Configure your reverse proxy**

⚠️ **Required for production**: Configure your reverse proxy to route traffic to the services above.

See [DEPLOYMENT.md](./DEPLOYMENT.md) for:
- Traefik configuration
- Caddy configuration
- Nginx configuration
- Cloud load balancer examples

**For testing without a proxy:**
```bash
# Optional: Use the built-in basic proxy
docker-compose -f docker-compose.yml -f docker-compose.proxy.yml up -d
# Access at: http://localhost
```

## 📋 Architecture

```
┌─────────────────────────────────────────┐
│         OPENPILOT DEVICE                │
│  (comma 3, comma 3X)                    │
└─────────────┬───────────────────────────┘
              │
              │ HTTPS/WSS
              │
┌─────────────▼───────────────────────────┐
│         NGINX (Reverse Proxy)           │
│              + SSL/TLS                  │
└──┬────────┬──────────┬──────────┬───────┘
   │        │          │          │
┌──▼──┐ ┌──▼────┐ ┌───▼───┐ ┌────▼────┐
│ API │ │Athena │ │ Maps  │ │Frontend │
└──┬──┘ └──┬────┘ └───┬───┘ └─────────┘
   │       │          │
┌──▼───────▼──────────▼──┐
│      PostgreSQL         │
└─────────────────────────┘
   
┌─────────────────────────┐
│    MinIO Storage        │
│  (Videos, Logs, Data)   │
└─────────────────────────┘
```

## 🔧 Configuration

### Domain Setup

1. Point your domain to your server IP
2. Configure SSL certificates:

**Option A: Let's Encrypt (Recommended)**
```bash
./scripts/setup-ssl.sh your-domain.com
```

**Option B: Self-signed (Testing only)**
```bash
./scripts/generate-self-signed.sh your-domain.com
```

### Map Data

Download OSM data for your region:

```bash
# Download California data
wget https://download.geofabrik.de/north-america/us/california-latest.osm.pbf \
  -O maps/osm/map.osm.pbf

# Prepare routing data
docker-compose up routing-prepare
```

### Device Configuration

On your openpilot device, SSH in and run:

```bash
URL="https://your-domain.com"
WEBSOCKET_URL="wss://your-domain.com"

cd /data/openpilot

# Add configuration
sed -i '3i # Self-hosted server configuration' launch_env.sh
sed -i "4i export ATHENA_HOST=\"$WEBSOCKET_URL\"" launch_env.sh
sed -i "5i export API_HOST=\"$URL\"" launch_env.sh
sed -i "6i export MAPS_HOST=\"$URL\"" launch_env.sh

# Apply maps host to navd if it exists
if test -f selfdrive/navd/navd.py; then
  sed -i 's#self.mapbox_host = "https://maps.comma.ai"#self.mapbox_host = os.getenv("MAPS_HOST", "https://maps.comma.ai")#' selfdrive/navd/navd.py
fi

# Reboot
sudo reboot
```

## 📊 Monitoring

### Grafana Dashboards

Access Grafana at `https://your-domain.com:3000`

Default credentials:
- Username: `admin`
- Password: (from GRAFANA_ADMIN_PASSWORD in .env)

Pre-configured dashboards:
- **System Overview**: CPU, memory, disk usage
- **API Metrics**: Request rates, latencies, errors
- **Database**: Connection pool, query performance
- **Storage**: Upload rates, storage usage
- **WebSocket**: Active connections, message rates

### Logs

View logs in real-time:
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api

# Last 100 lines
docker-compose logs --tail=100 athena
```

## 🔐 Security

### Best Practices

1. **Change all default passwords**
2. **Use strong JWT secret** (min 32 characters)
3. **Enable HTTPS** (required for production)
4. **Configure firewall**:
   ```bash
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw enable
   ```
5. **Regular updates**:
   ```bash
   docker-compose pull
   docker-compose up -d
   ```

### Rate Limiting

Configure in `nginx/nginx.conf`:
```nginx
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=upload:10m rate=1r/s;
```

## 💾 Backup & Restore

### Automated Backups

Backups run daily at 2 AM and are stored in `./database/backups/`

Configure retention in docker-compose.yml:
```yaml
BACKUP_KEEP_DAYS=7
BACKUP_KEEP_WEEKS=4
BACKUP_KEEP_MONTHS=6
```

### Manual Backup

```bash
# Database
docker-compose exec postgres pg_dump -U comma commaconnect | gzip > backup.sql.gz

# MinIO data
docker-compose exec minio mc mirror myminio/comma-uploads /backups/minio/
```

### Restore

```bash
# Database
gunzip -c backup.sql.gz | docker-compose exec -T postgres psql -U comma commaconnect

# MinIO data
docker-compose exec minio mc mirror /backups/minio/ myminio/comma-uploads/
```

## 🔄 Updates

### Updating the Stack

```bash
# Pull latest images
docker-compose pull

# Restart services
docker-compose up -d

# Run migrations if needed
docker-compose exec api python manage.py migrate
```

### Database Migrations

```bash
# Check migration status
docker-compose exec api python manage.py showmigrations

# Run migrations
docker-compose exec api python manage.py migrate

# Create new migration (after model changes)
docker-compose exec api python manage.py makemigrations
```

## 🐛 Troubleshooting

### Common Issues

**Service won't start**
```bash
# Check logs
docker-compose logs [service-name]

# Check service status
docker-compose ps

# Restart service
docker-compose restart [service-name]
```

**Database connection errors**
```bash
# Check postgres is running
docker-compose ps postgres

# Check logs
docker-compose logs postgres

# Restart database
docker-compose restart postgres
```

**Upload failures**
```bash
# Check MinIO
docker-compose ps minio
docker-compose logs minio

# Verify buckets exist
docker-compose exec minio mc ls myminio/
```

**Map tiles not loading**
```bash
# Check tile server
docker-compose logs tile-server

# Verify data exists
ls -lh maps/data/

# Restart tile server
docker-compose restart tile-server
```

### Health Checks

```bash
# API health
curl https://your-domain.com/health

# Database
docker-compose exec postgres pg_isready -U comma

# Redis
docker-compose exec redis redis-cli ping

# MinIO
curl http://localhost:9000/minio/health/live
```

## 📖 Documentation

- [Full Requirements Specification](./comma-connect-requirements-specification.md)
- [API Documentation](./docs/api.md)
- [Database Schema](./docs/schema.md)
- [Contributing Guide](./CONTRIBUTING.md)

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guide](./CONTRIBUTING.md) first.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Comma.ai](https://comma.ai/) for openpilot and inspiration
- [OpenStreetMap](https://www.openstreetmap.org/) contributors
- All open-source projects used in this stack

## 💬 Support

- Issues: [GitHub Issues](https://github.com/yourorg/comma-connect-server/issues)
- Discussions: [GitHub Discussions](https://github.com/yourorg/comma-connect-server/discussions)
- Discord: [Join our server](https://discord.gg/your-invite)

## 🗺️ Roadmap

- [x] Core API implementation
- [x] WebSocket service
- [x] Frontend PWA
- [x] Docker Compose setup
- [ ] Advanced analytics
- [ ] Machine learning event detection
- [ ] Mobile app
- [ ] Plugin system
- [ ] Multi-language support

---

**Made with ❤️ by the community**
