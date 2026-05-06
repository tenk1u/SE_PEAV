@echo off
REM ─── Script para ejecutar tests en Windows ─────────────────────────────

echo ========================================
echo Ejecutando Tests - SE-PEAV Backend
echo ========================================

REM Verificar que estamos en el directorio correcto
if not exist "backend" (
    echo ERROR: Ejecutar desde el directorio raiz del proyecto
    pause
    exit /b 1
)

REM Cambiar al directorio del backend
cd backend

REM Verificar si pytest está instalated
python -m pytest --version >nul 2>&1
if errorlevel 1 (
    echo Instalando dependencias de test...
    pip install pytest pytest-asyncio pytest-cov httpx aiosqlite
)

echo.
echo Ejecutando tests unitarios...
echo.

REM Ejecutar tests
python -m pytest tests/ -v --tb=short

echo.
echo ========================================
echo Tests completados
echo ========================================

pause
