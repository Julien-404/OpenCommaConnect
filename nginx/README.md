# Optional Nginx Reverse Proxy

⚠️ **This proxy is OPTIONAL and NOT recommended for production.**

## When to Use This

- ✅ Quick local testing
- ✅ Development without existing proxy
- ✅ Learning/experimentation

## When NOT to Use This

- ❌ Production deployments
- ❌ When you have an existing reverse proxy
- ❌ When you need automatic SSL renewal
- ❌ When you need advanced features

## How to Use

### 1. Start Services with Proxy

```bash
docker-compose -f docker-compose.yml -f docker-compose.proxy.yml up -d
```

### 2. Access Services

All services available at:
- Frontend: `http://localhost`
- API: `http://localhost/api/v1`
- WebSocket: `wss://localhost/ws`

### 3. SSL Certificates

For HTTPS, add your certificates:

```bash
# Copy your certificates
cp /path/to/fullchain.pem nginx/ssl/cert.pem
cp /path/to/privkey.pem nginx/ssl/key.pem

# Update nginx.conf to enable SSL
# Uncomment the SSL server block

# Restart nginx
docker-compose -f docker-compose.yml -f docker-compose.proxy.yml restart nginx
```

## For Production

**Don't use this proxy in production.** Instead, use:

### Traefik (Recommended)
- Automatic SSL with Let's Encrypt
- Service discovery
- Hot reload
- Dashboard

See: `examples/traefik-docker-compose.yml`

### Caddy
- Easiest automatic HTTPS
- Simple configuration
- Built-in ACME support

See: `examples/Caddyfile`

### Managed Nginx
- Better optimized
- More features
- Easier SSL management

See: `examples/nginx-external.conf`

## Configuration Files

- `nginx.conf` - Main configuration
- `ssl/` - SSL certificates directory
- `logs/` - Access and error logs

## Troubleshooting

### Port 80/443 already in use

Another service is using these ports. Either:
1. Stop the other service
2. Change ports in `.env`:
   ```bash
   NGINX_HTTP_PORT=8080
   NGINX_HTTPS_PORT=8443
   ```

### Services not accessible

Check nginx logs:
```bash
docker-compose -f docker-compose.yml -f docker-compose.proxy.yml logs nginx
```

### SSL not working

Make sure:
1. Certificates are in `nginx/ssl/`
2. SSL server block is uncommented in `nginx.conf`
3. Certificates are valid: `openssl x509 -in nginx/ssl/cert.pem -text -noout`

## Need Help?

See the main documentation:
- [DEPLOYMENT.md](../DEPLOYMENT.md) - Reverse proxy guide
- [examples/](../examples/) - Configuration examples
- [README.md](../README.md) - Main documentation
