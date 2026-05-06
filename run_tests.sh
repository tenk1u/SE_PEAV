#!/bin/bash
# ─── Script para ejecutar tests en Linux/Mac ─────────────────────────────

echo "========================================"
echo "Ejecutando Tests - SE-PEAV Backend"
echo "========================================"

# Verificar que estamos en el directorio correcto
if [ ! -d "backend" ]; then
    echo "ERROR: Ejecutar desde el directorio raiz del proyecto"
    exit 1
fi

# Cambiar al directorio del backend
cd backend

# Verificar si pytest está instalado
if ! python -m pytest --version &> /dev/null; then
    echo "Instalando dependencias de test..."
    pip install pytest pytest-asyncio pytest-cov httpx aiosqlite
fi

echo ""
echo "Ejecutando tests unitarios..."
echo ""

# Ejecutar tests
python -m pytest tests/ -v --tb=short

echo ""
echo "========================================"
echo "Tests completados"
echo "========================================"
