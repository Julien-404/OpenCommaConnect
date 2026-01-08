# Configuration Examples

This directory contains example configurations for integrating Comma Connect with popular reverse proxies.

## Available Examples

### 1. Traefik (Docker Labels)
**File:** `traefik-docker-compose.yml`

Copy relevant sections to your `docker-compose.override.yml`:

```bash
cp traefik-docker-compose.yml ../docker-compose.override.yml
# Edit and customize as needed
```

**Requirements:**
- Traefik v2+ running
- Traefik network created: `docker network create traefik-network`
- Let's Encrypt configured in Traefik

### 2. Caddy
**File:** `Caddyfile`

Use this Caddyfile configuration:

```bash
# Option A: Copy to Caddy config directory
sudo cp Caddyfile /etc/caddy/sites-available/comma-connect
sudo ln -s /etc/caddy/sites-available/comma-connect /etc/caddy/sites-enabled/

# Option B: Append to main Caddyfile
cat Caddyfile | sudo tee -a /etc/caddy/Caddyfile

# Reload Caddy
sudo systemctl reload caddy
```

### 3. External Nginx
**File:** `nginx-external.conf`

Install on your Nginx server:

```bash
# Copy configuration
sudo cp nginx-external.conf /etc/nginx/sites-available/comma-connect

# Enable site
sudo ln -s /etc/nginx/sites-available/comma-connect /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

## Configuration Steps

### Common Steps for All Proxies

1. **Start Comma Connect without built-in proxy**
   ```bash
   cd ..
   docker-compose up -d
   ```

2. **Update environment variables**

   Edit `.env`:
   ```bash
   FRONTEND_API_URL=https://your-domain.com
   FRONTEND_WS_URL=wss://your-domain.com
   ```

3. **Rebuild frontend**
   ```bash
   docker-compose up -d --build frontend
   ```

### Traefik Specific

1. **Ensure Traefik network exists**
   ```bash
   docker network create traefik-network
   ```

2. **Copy override file**
   ```bash
   cp examples/traefik-docker-compose.yml docker-compose.override.yml
   ```

3. **Edit domain in override file**
   Replace `comma.example.com` with your domain

4. **Restart services**
   ```bash
   docker-compose down
   docker-compose up -d
   ```

### Caddy Specific

1. **Replace domain placeholders**
   ```bash
   sed -i 's/comma.example.com/your-domain.com/g' Caddyfile
   ```

2. **Caddy will automatically get SSL certificates from Let's Encrypt**

### Nginx Specific

1. **Get SSL certificate (if not already)**
   ```bash
   sudo certbot --nginx -d comma.example.com
   ```

2. **Update domains in config**
   ```bash
   sed -i 's/comma.example.com/your-domain.com/g' nginx-external.conf
   ```

3. **Adjust upstream ports if needed**
   If you changed default ports in `.env`, update upstream definitions

## Testing

After configuration, test all endpoints:

```bash
# Frontend
curl https://your-domain.com

# API Health
curl https://your-domain.com/api/v1/health

# WebSocket (requires wscat or similar)
wscat -c wss://your-domain.com/ws/athena/your-dongle-id
```

## Troubleshooting

### Traefik

**Services not accessible:**
- Check Traefik logs: `docker logs traefik`
- Verify network: `docker network inspect traefik-network`
- Ensure labels are correct in override file

**SSL issues:**
- Check Let's Encrypt staging/production in Traefik config
- Verify DNS points to correct server
- Check Traefik dashboard for certificate status

### Caddy

**502 Bad Gateway:**
- Check if Comma Connect services are running: `docker-compose ps`
- Verify ports match between Caddy config and docker-compose
- Check Caddy logs: `sudo journalctl -u caddy -f`

**SSL not working:**
- Ensure port 443 is open: `sudo ufw allow 443/tcp`
- Check DNS: `dig your-domain.com`
- Verify Caddy can write to `/var/lib/caddy`

### Nginx

**Connection refused:**
- Check upstream servers are accessible from Nginx host
- If using Docker network, adjust upstream to container names
- Test direct connection: `curl http://localhost:8000/health`

**WebSocket not working:**
- Ensure Upgrade header is proxied
- Check WebSocket timeout settings
- Test with: `curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" http://localhost:8001/health`

## Security Recommendations

For all proxy configurations:

1. **Enable rate limiting** (shown in examples)
2. **Set security headers** (HSTS, CSP, etc.)
3. **Use strong SSL/TLS configuration**
4. **Keep proxy software updated**
5. **Monitor access logs**

## Need Help?

- 📖 [Main Documentation](../README.md)
- 🚀 [Deployment Guide](../DEPLOYMENT.md)
- 🐛 [Report Issues](https://github.com/yourorg/comma-connect-server/issues)
