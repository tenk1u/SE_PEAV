# SE-PEAV Backend

Backend API para el Sistema Edge de Predimensionamiento Estructural y Análisis de Vulnerabilidad.

## Arquitectura

```
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── auth.py          # Autenticación y usuarios
│   │       ├── projects.py      # CRUD de proyectos
│   │       ├── inspections.py   # Inspecciones y uploads
│   │       └── reports.py       # Generación de reportes
│   ├── core/
│   │   ├── config.py            # Configuración de la app
│   │   └── database.py          # Conexión a PostgreSQL
│   ├── models/
│   │   └── project.py           # Modelos SQLAlchemy
│   ├── schemas/
│   │   └── project.py           # Schemas Pydantic
│   ├── services/
│   │   ├── storage.py           # Servicio S3/MinIO
│   │   ├── processing.py        # Pipeline de procesamiento
│   │   └── e060_analysis.py     # Análisis estructural E.060
│   └── workers/
│       └── __init__.py          # Tareas Celery
├── alembic/                     # Migraciones de BD
├── tests/                       # Tests unitarios
├── Dockerfile
├── requirements.txt
└── .env.example
```

## Requisitos

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- MinIO o S3-compatible storage

## Instalación

### 1. Crear entorno virtual

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate  # Windows
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Configurar variables de entorno

```bash
cp .env.example .env
# Editar .env con tus configuraciones
```

### 4. Iniciar servicios (Docker)

```bash
docker compose up -d postgres redis minio
```

### 5. Ejecutar migraciones

```bash
alembic upgrade head
```

### 6. Iniciar el servidor

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Documentation

Una vez iniciado el servidor, la documentación interactiva está disponible en:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Endpoints Principales

### Autenticación
- `POST /api/v1/auth/register` - Registro de usuarios
- `POST /api/v1/auth/login` - Login
- `GET /api/v1/auth/me` - Usuario actual

### Proyectos
- `GET /api/v1/projects` - Listar proyectos
- `POST /api/v1/projects` - Crear proyecto
- `GET /api/v1/projects/{id}` - Obtener proyecto
- `PATCH /api/v1/projects/{id}` - Actualizar proyecto
- `DELETE /api/v1/projects/{id}` - Eliminar proyecto

### Inspecciones
- `GET /api/v1/inspections` - Listar inspecciones
- `POST /api/v1/inspections` - Crear inspección
- `POST /api/v1/inspections/{id}/upload/dron` - Subir video de dron
- `POST /api/v1/inspections/{id}/upload/mobile` - Subir capturas móviles
- `POST /api/v1/inspections/{id}/process` - Iniciar procesamiento
- `GET /api/v1/inspections/{id}/status` - Estado del procesamiento
- `GET /api/v1/inspections/{id}/detections` - Detecciones YOLO
- `GET /api/v1/inspections/{id}/metrics` - Métricas estructurales

## Análisis E.060

El backend implementa el análisis según la norma peruana E.060 (Reglamento Nacional de Edificaciones - Albañilería):

- **Espesor mínimo de muros**: 15cm (1 piso), 20cm (2 pisos), 25cm (3+ pisos)
- **Confinamiento**: Máximo 4m entre confinamientos
- **Relación vano/muro**: Máximo 0.6
- **Refuerzo**: Mínimo 0.25% del área bruta

## Testing

```bash
pytest tests/
```

## Docker

```bash
docker compose up -d
```

Esto levanta:
- API en puerto 8000
- PostgreSQL en puerto 5432
- Redis en puerto 6379
- MinIO en puerto 9000
- Celery worker para procesamiento
