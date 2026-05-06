@echo off
REM ─── SE-PEAV Quick Start Script for Windows ────────────────────────────────
REM This script helps you set up and run the SE-PEAV system

echo ========================================
echo SE-PEAV Quick Start
echo ========================================

REM Check if Docker is installed
docker --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker is not installed. Please install Docker Desktop first.
    echo Download from: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

REM Check if Docker Compose is installed
docker compose version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker Compose is not available. Please update Docker Desktop.
    pause
    exit /b 1
)

echo.
echo Step 1: Creating workspace directories...
if not exist "workspace\raw_data" mkdir workspace\raw_data
if not exist "workspace\processed_data" mkdir workspace\processed_data
echo Done!

echo.
echo Step 2: Setting up environment variables...
if not exist ".env" (
    copy .env.example .env
    echo Created .env file from template.
    echo Please edit .env file with your configuration if needed.
) else (
    echo .env file already exists.
)

echo.
echo Step 3: Building and starting services...
echo This may take a few minutes on first run...
echo.

REM Start infrastructure services
echo Starting PostgreSQL, Redis, and MinIO...
docker compose up -d postgres redis minio

REM Wait for services to be healthy
echo Waiting for services to be ready...
timeout /t 10 /nobreak >nul

REM Build and start backend
echo Building and starting backend API...
docker compose up -d backend celery_worker

echo.
echo ========================================
echo Services are starting up!
echo ========================================
echo.
echo API will be available at: http://localhost:8000
echo API Documentation: http://localhost:8000/docs
echo MinIO Console: http://localhost:9001
echo.
echo Default credentials:
echo   API Admin: admin@se-peav.com / admin123
echo   MinIO: minioadmin / minioadmin
echo.
echo To view logs: docker compose logs -f
echo To stop services: docker compose down
echo ========================================

pause
