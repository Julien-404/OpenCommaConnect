# Deployment Guide

This guide covers different deployment scenarios for Comma Connect.

## Table of Contents

1. [Deployment Modes](#deployment-modes)
2. [Without Reverse Proxy (Direct)](#without-reverse-proxy-direct)
3. [With Built-in Nginx Proxy](#with-built-in-nginx-proxy)
4. [With External Reverse Proxy](#with-external-reverse-proxy)
5. [Production Considerations](#production-considerations)

---

## Deployment Modes

Comma Connect supports flexible deployment configurations:

- **Direct Mode** (default): Services expose ports directly, no built-in proxy
- **Built-in Proxy Mode**: Use the included Nginx container
- **External Proxy Mode**: Integrate with your existing reverse proxy (Traefik, Caddy, etc.)

---

## Without Reverse Proxy (Direct)

This is the **default mode**. Each service exposes its port directly.

### Configuration

Edit `.env`:

```bash
# Ports exposed directly
API_PORT=8000
ATHENA_PORT=8001
FRONTEND_PORT=3000

# Frontend URLs
FRONTEND_API_URL=http://your-server:8000
FRONTEND_WS_URL=ws://your-server:8001
```

### Start Services

```bash
docker-compose up -d
```

### Access Points

- Frontend: `http://your-server:3000`
- API: `http://your-server:8000`
- WebSocket: `ws://your-server:8001`
- Grafana: `http://your-server:3000` (default Grafana port)
- MinIO Console: `http://your-server:9001`

### Pros

- ✅ Simple setup
- ✅ No proxy configuration needed
- ✅ Works with any external proxy

### Cons

- ❌ Multiple ports to manage
- ❌ No automatic SSL
- ❌ Manual CORS configuration needed

---

## With Built-in Nginx Proxy

Use the included Nginx container for a unified entry point.

### Configuration

Edit `.env`:

```bash
# Enable built-in proxy
NGINX_HTTP_PORT=80
NGINX_HTTPS_PORT=443

# Frontend URLs (through proxy)
FRONTEND_API_URL=https://your-domain.com
FRONTEND_WS_URL=wss://your-domain.com

# Domain
DOMAIN=your-domain.com
ENABLE_HTTPS=true
```

### Start Services with Proxy Profile

```bash
docker-compose --profile with-proxy up -d
```

### SSL Configuration

For production, replace self-signed certificates:

```bash
# Place your certificates
cp your-cert.pem nginx/ssl/cert.pem
cp your-key.pem nginx/ssl/key.pem

# Restart nginx
docker-compose restart nginx
```

### Access Points

All services through single domain:
- Frontend: `https://your-domain.com`
- API: `https://your-domain.com/api/v1`
- WebSocket: `wss://your-domain.com/ws`
- Grafana: `https://your-domain.com/grafana`

### Pros

- ✅ Single entry point
- ✅ Built-in SSL support
- ✅ Rate limiting configured
- ✅ CORS handled

### Cons

- ❌ Additional container to manage
- ❌ Less flexible than external proxy

---

## With External Reverse Proxy

Use your existing reverse proxy (Traefik, Caddy, Nginx, etc.).

### 1. Start Services Without Built-in Proxy

```bash
# Default mode - services expose ports directly
docker-compose up -d
```

### 2. Configure Your Reverse Proxy

#### Example: Traefik

Add labels to `docker-compose.override.yml`:

```yaml
version: '3.8'

services:
  api:
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.comma-api.rule=Host(`your-domain.com`) && PathPrefix(`/api`)"
      - "traefik.http.routers.comma-api.entrypoints=websecure"
      - "traefik.http.routers.comma-api.tls.certresolver=letsencrypt"
      - "traefik.http.services.comma-api.loadbalancer.server.port=8000"

  athena:
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.comma-ws.rule=Host(`your-domain.com`) && PathPrefix(`/ws`)"
      - "traefik.http.routers.comma-ws.entrypoints=websecure"
      - "traefik.http.routers.comma-ws.tls.certresolver=letsencrypt"
      - "traefik.http.services.comma-ws.loadbalancer.server.port=8001"

  frontend:
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.comma-frontend.rule=Host(`your-domain.com`)"
      - "traefik.http.routers.comma-frontend.entrypoints=websecure"
      - "traefik.http.routers.comma-frontend.tls.certresolver=letsencrypt"
      - "traefik.http.services.comma-frontend.loadbalancer.server.port=80"
```

#### Example: Caddy

Create `Caddyfile`:

```caddyfile
your-domain.com {
    # Frontend
    handle /* {
        reverse_proxy comma-frontend:80
    }

    # API
    handle /api/* {
        reverse_proxy comma-api:8000
    }

    # WebSocket
    handle /ws/* {
        reverse_proxy comma-athena:8001
    }
}
```

#### Example: External Nginx

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    # Frontend
    location / {
        proxy_pass http://comma-frontend:80;
        proxy_set_header Host $host;
    }

    # API
    location /api/ {
        proxy_pass http://comma-api:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # WebSocket
    location /ws/ {
        proxy_pass http://comma-athena:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### 3. Update Frontend URLs

Edit `.env`:

```bash
FRONTEND_API_URL=https://your-domain.com
FRONTEND_WS_URL=wss://your-domain.com
```

Rebuild frontend:

```bash
docker-compose up -d --build frontend
```

### Pros

- ✅ Use your existing infrastructure
- ✅ Consistent with other services
- ✅ Advanced features (automatic SSL, service discovery)
- ✅ Better integration with existing monitoring

### Cons

- ❌ Requires proxy already set up
- ❌ More initial configuration

---

## Production Considerations

### Security

1. **SSL/TLS**
   ```bash
   # Always use HTTPS in production
   ENABLE_HTTPS=true
   ```

2. **Firewall Rules**
   ```bash
   # Only expose necessary ports
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw deny 8000/tcp  # Block direct API access
   sudo ufw deny 8001/tcp  # Block direct WebSocket access
   ```

3. **Secrets Management**
   - Never commit `.env` to git
   - Use strong, random passwords (min 32 chars for JWT_SECRET)
   - Rotate secrets regularly

### Performance

1. **Resource Limits**

   Create `docker-compose.override.yml`:

   ```yaml
   version: '3.8'

   services:
     api:
       deploy:
         resources:
           limits:
             cpus: '2'
             memory: 4G
   ```

2. **Caching**
   - Configure Redis appropriately
   - Use CDN for static assets
   - Enable HTTP caching headers

3. **Database Optimization**
   ```bash
   # Tune PostgreSQL for your workload
   # Edit docker-compose.yml postgres command section
   ```

### Monitoring

1. **Health Checks**
   ```bash
   # Test all services
   curl http://localhost:8000/health
   curl http://localhost:8001/health
   ```

2. **Logs**
   ```bash
   # Centralized logging
   docker-compose logs -f

   # Specific service
   docker-compose logs -f api
   ```

3. **Metrics**
   - Access Grafana: `http://your-server:3000`
   - Configure alerts for critical metrics
   - Monitor disk space (videos can grow quickly)

### Backups

1. **Automated Database Backups**
   ```bash
   # Already configured in docker-compose.yml
   # Backups stored in ./database/backups/
   ```

2. **MinIO Data**
   ```bash
   # Configure MinIO mirroring or S3 sync
   # Consider external backup storage
   ```

### High Availability

For production deployments with multiple servers:

1. **Database**: Use PostgreSQL replication
2. **Object Storage**: MinIO distributed mode or external S3
3. **Load Balancing**: Multiple API/Athena instances behind load balancer
4. **Session Storage**: Redis cluster or Sentinel

---

## Comparison Table

| Feature | Direct Mode | Built-in Proxy | External Proxy |
|---------|-------------|----------------|----------------|
| Setup Complexity | ⭐ Easy | ⭐⭐ Medium | ⭐⭐⭐ Complex |
| SSL Support | Manual | ✅ Included | ✅ Via Proxy |
| Single Entry Point | ❌ No | ✅ Yes | ✅ Yes |
| Port Management | Multiple | Single | Single |
| Resource Usage | Low | Medium | Medium |
| Integration | Flexible | Standalone | Integrated |
| Best For | Development | Small deployments | Production |

---

## Quick Reference

### Direct Mode (Default)
```bash
docker-compose up -d
```

### With Built-in Proxy
```bash
docker-compose --profile with-proxy up -d
```

### Stop Services
```bash
# All services
docker-compose down

# Keep data
docker-compose down --volumes  # This removes volumes!
```

### View Logs
```bash
docker-compose logs -f [service-name]
```

### Rebuild After Config Changes
```bash
docker-compose up -d --build
```

---

## Need Help?

- 📖 [Main README](./README.md)
- 🚀 [Quick Start Guide](./QUICKSTART.md)
- 🐛 [Report Issues](https://github.com/yourorg/comma-connect-server/issues)
