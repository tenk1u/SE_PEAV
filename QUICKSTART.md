# Guía de Inicio Rápido - SE-PEAV

## Requisitos Previos

1. **Docker Desktop** instalado y ejecutándose
2. **Git** para clonar el repositorio
3. **(Opcional)** Flutter SDK para desarrollo móvil

## Inicio Rápido

### Windows

```bash
# Ejecutar el script de inicio
start.bat
```

### Linux/Mac

```bash
# Dar permisos de ejecución
chmod +x start.sh

# Ejecutar el script de inicio
./start.sh
```

### Manual

```bash
# 1. Crear directorios de trabajo
mkdir -p workspace/raw_data workspace/processed_data

# 2. Configurar variables de entorno
cp .env.example .env
# Editar .env si es necesario

# 3. Levantar servicios de infraestructura
docker compose up -d postgres redis minio

# 4. Esperar a que los servicios estén listos (10-15 segundos)

# 5. Levantar el backend
docker compose up -d backend celery_worker
```

## URLs de Acceso

| Servicio | URL | Credenciales |
|----------|-----|--------------|
| API Backend | http://localhost:8000 | - |
| Documentación API (Swagger) | http://localhost:8000/docs | - |
| Documentación API (ReDoc) | http://localhost:8000/redoc | - |
| MinIO Console | http://localhost:9001 | minioadmin / minioadmin |
| Admin API | - | admin@se-peav.com / admin123 |

## Comandos Útiles

### Ver logs

```bash
# Todos los servicios
docker compose logs -f

# Servicio específico
docker compose logs -f backend
docker compose logs -f celery_worker
```

### Detener servicios

```bash
# Detener todos los servicios
docker compose down

# Detener y eliminar volúmenes (cuidado: elimina datos)
docker compose down -v
```

### Reiniciar servicios

```bash
# Reiniciar un servicio específico
docker compose restart backend

# Reconstruir y reiniciar
docker compose up -d --build backend
```

### Acceder a la base de datos

```bash
# Conectar a PostgreSQL
docker compose exec postgres psql -U se_peav -d se_peav

# Ver tablas
\dt

# Salir
\q
```

## Estructura de la API

### Autenticación

```bash
# Registrar usuario
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "password123", "full_name": "Test User"}'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "password123"}'

# Respuesta: {"access_token": "...", "token_type": "bearer"}
```

### Proyectos

```bash
# Crear proyecto (requiere token)
curl -X POST http://localhost:8000/api/v1/projects \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Mi Casa", "address": "Av. Example 123", "latitude": -12.0464, "longitude": -77.0428}'

# Listar proyectos
curl http://localhost:8000/api/v1/projects \
  -H "Authorization: Bearer <TOKEN>"
```

### Inspecciones

```bash
# Crear inspección
curl -X POST http://localhost:8000/api/v1/inspections \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"project_id": 1, "capture_source": "dron"}'

# Subir video de dron
curl -X POST http://localhost:8000/api/v1/inspections/1/upload/dron \
  -H "Authorization: Bearer <TOKEN>" \
  -F "file=@video.mp4"

# Iniciar procesamiento
curl -X POST http://localhost:8000/api/v1/inspections/1/process \
  -H "Authorization: Bearer <TOKEN>"

# Ver estado
curl http://localhost:8000/api/v1/inspections/1/status \
  -H "Authorization: Bearer <TOKEN>"
```

## Desarrollo

### Ejecutar en modo desarrollo (sin Docker)

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate  # Windows

pip install -r requirements.txt
uvicorn app.main:app --reload

# En otra terminal, iniciar Celery
celery -A app.services.processing worker --loglevel=info
```

### Ejecutar tests

```bash
cd backend
pytest tests/
```

## Solución de Problemas

### Error: "port is already allocated"

```bash
# Ver qué está usando el puerto
netstat -ano | findstr :8000  # Windows
lsof -i :8000  # Linux/Mac

# Cambiar el puerto en docker-compose.yml
ports:
  - "8001:8000"  # Usar 8001 en lugar de 8000
```

### Error: "database does not exist"

```bash
# Conectar a PostgreSQL y crear la base de datos
docker compose exec postgres psql -U postgres
CREATE DATABASE se_peav;
\q
```

### Error: "relation does not exist"

```bash
# Ejecutar migraciones
docker compose exec backend alembic upgrade head
```

### MinIO no accesible

```bash
# Verificar que MinIO está corriendo
docker compose ps minio

# Reiniciar MinIO
docker compose restart minio
```

## Próximos Pasos

1. **Integrar pipeline legacy**: Conectar los scripts existentes (01-04) con el nuevo backend
2. **Setup Flutter**: Crear la aplicación móvil con LiDAR scanning
3. **Visor Three.js**: Implementar el visor 3D web
4. **Tests**: Crear tests unitarios y de integración
