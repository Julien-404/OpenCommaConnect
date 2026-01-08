#!/bin/bash

# Simple API health check script

API_URL="${1:-http://localhost:8000}"

echo "Testing Comma Connect API at $API_URL"
echo ""

# Test root endpoint
echo "Testing root endpoint..."
curl -s "$API_URL/" | jq '.' || echo "❌ Root endpoint failed"

echo ""

# Test health endpoint
echo "Testing health endpoint..."
curl -s "$API_URL/health" | jq '.' || echo "❌ Health endpoint failed"

echo ""
echo "API test complete!"
