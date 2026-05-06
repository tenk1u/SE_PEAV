#!/bin/bash
# ─── SE-PEAV Quick Start Script for Linux/Mac ──────────────────────────────
# This script helps you set up and run the SE-PEAV system

set -e

echo "========================================"
echo "SE-PEAV Quick Start"
echo "========================================"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker is not installed. Please install Docker first."
    echo "Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! docker compose version &> /dev/null; then
    echo "ERROR: Docker Compose is not available. Please update Docker."
    exit 1
fi

echo ""
echo "Step 1: Creating workspace directories..."
mkdir -p workspace/raw_data workspace/processed_data
echo "Done!"

echo ""
echo "Step 2: Setting up environment variables..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env file from template."
    echo "Please edit .env file with your configuration if needed."
else
    echo ".env file already exists."
fi

echo ""
echo "Step 3: Building and starting services..."
echo "This may take a few minutes on first run..."
echo ""

# Start infrastructure services
echo "Starting PostgreSQL, Redis, and MinIO..."
docker compose up -d postgres redis minio

# Wait for services to be healthy
echo "Waiting for services to be ready..."
sleep 10

# Build and start backend
echo "Building and starting backend API..."
docker compose up -d backend celery_worker

echo ""
echo "========================================"
echo "Services are starting up!"
echo "========================================"
echo ""
echo "API will be available at: http://localhost:8000"
echo "API Documentation: http://localhost:8000/docs"
echo "MinIO Console: http://localhost:9001"
echo ""
echo "Default credentials:"
echo "  API Admin: admin@se-peav.com / admin123"
echo "  MinIO: minioadmin / minioadmin"
echo ""
echo "To view logs: docker compose logs -f"
echo "To stop services: docker compose down"
echo "========================================"
