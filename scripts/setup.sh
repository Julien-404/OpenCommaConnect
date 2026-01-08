#!/bin/bash

set -e

echo "========================================="
echo "Comma Connect Server Setup"
echo "========================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env

    echo ""
    echo "⚠️  Please edit .env file and set the following:"
    echo "  - POSTGRES_PASSWORD"
    echo "  - MINIO_ROOT_PASSWORD"
    echo "  - JWT_SECRET (min 32 characters)"
    echo "  - GRAFANA_ADMIN_PASSWORD"
    echo "  - DOMAIN (your domain or 'localhost' for testing)"
    echo ""
    echo "Run this script again after configuring .env"
    exit 0
fi

echo "✓ .env file exists"

# Source environment variables
source .env

# Check required variables
if [ -z "$JWT_SECRET" ] || [ ${#JWT_SECRET} -lt 32 ]; then
    echo "❌ JWT_SECRET must be at least 32 characters long"
    exit 1
fi

echo "✓ Environment variables configured"

# Create necessary directories
echo ""
echo "Creating directories..."
mkdir -p nginx/ssl nginx/logs
mkdir -p database/backups
mkdir -p maps/{data,styles,osm}
mkdir -p monitoring/grafana/{dashboards,datasources}

echo "✓ Directories created"

# Generate self-signed SSL certificate for testing
if [ ! -f nginx/ssl/cert.pem ]; then
    echo ""
    echo "Generating self-signed SSL certificate for testing..."
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout nginx/ssl/key.pem \
        -out nginx/ssl/cert.pem \
        -subj "/C=US/ST=State/L=City/O=Organization/CN=$DOMAIN"
    echo "✓ SSL certificate generated"
fi

# Pull Docker images
echo ""
echo "Pulling Docker images..."
docker-compose pull

echo ""
echo "========================================="
echo "Setup complete!"
echo "========================================="
echo ""
echo "To start the server:"
echo "  docker-compose up -d"
echo ""
echo "To view logs:"
echo "  docker-compose logs -f"
echo ""
echo "Access the application:"
echo "  Frontend: http://$DOMAIN"
echo "  Grafana: http://$DOMAIN:3000"
echo "  MinIO Console: http://$DOMAIN:9001"
echo ""
echo "First time setup:"
echo "  1. Wait for all services to start (30-60 seconds)"
echo "  2. Register a new user account"
echo "  3. Pair your comma device"
echo ""
