#!/bin/bash
# Production deployment script for WYGIWYH MCP Server
# Copyright (c) 2025 ReNewator.com

set -e

echo "================================================"
echo "WYGIWYH MCP Server - Production Deployment"
echo "================================================"

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Error: .env file not found!"
    echo "Please copy .env.example to .env and configure it."
    exit 1
fi

# Build Docker image
echo ""
echo "Building Docker image..."
docker build -t wygiwyh-mcp-server:latest .

# Stop and remove existing container if running
echo ""
echo "Stopping existing container (if any)..."
docker-compose down || true

# Start the service
echo ""
echo "Starting MCP server..."
docker-compose up -d

# Wait for health check
echo ""
echo "Waiting for server to be healthy..."
sleep 5

# Check container status
echo ""
echo "Container status:"
docker-compose ps

# Show logs
echo ""
echo "Recent logs:"
docker-compose logs --tail=20

echo ""
echo "================================================"
echo "Deployment complete!"
echo "================================================"
echo "Server URL: http://localhost:5000"
echo "Health check: http://localhost:5000/health"
echo ""
echo "To view logs: docker-compose logs -f"
echo "To stop: docker-compose down"
echo "================================================"
