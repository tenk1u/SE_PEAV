# SE-PEAV · Sistema Edge de Predimensionamiento Estructural y Análisis de Vulnerabilidad

**Sistema automatizado para el análisis estructural de viviendas autoconstruidas en zonas sísmicas**

Desarrollado para el curso de **Tesis II**

---

## Visión del Proyecto

SE-PEAV es un sistema que permite a usuarios capturar imágenes y videos de sus viviendas (interior con celular LiDAR, exterior con dron DJI M4E) para generar un análisis estructural completo con predimensionamiento según la norma peruana E.060, visualizado en 3D vía web.

### Problema que Resuelve

En Perú, muchas viviendas escalonadas son autoconstruidas por maestros de obras no profesionales, generando riesgos estructurales ocultos en un país con alto riesgo sísmico. SE-PEAV permite:

- **Detectar** elementos estructurales (columnas, vigas, muros, fisuras)
- **Analizar** vulnerabilidades según norma E.060
- **Visualizar** el modelo 3D interactivo
- **Generar** reportes con recomendaciones

---

## Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CAPA DE CAPTURA                                    │
│  ┌─────────────────┐    ┌─────────────────────────────────────────────────┐  │
│  │  DJI M4E        │    │  Flutter App (iOS/Android)                     │  │
│  │  - Video 4K     │    │  - LiDAR Scanner (iPhone Pro 15+)             │  │
│  │  - GPS/RTK      │    │  - ARKit/ARCore para tracking                 │  │
│  └────────┬────────┘    │  - Guía de captura visual                     │  │
│           │             └──────────────────────────┬──────────────────────┘  │
└───────────┼──────────────────────────────────────┼──────────────────────────┘
            │                                      │
            ▼                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    API GATEWAY + STORAGE                                     │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐          │
│  │  FastAPI         │    │  PostgreSQL     │    │  MinIO/S3       │          │
│  │  - Auth          │    │  - Metadata     │    │  - Videos       │          │
│  │  - Upload        │    │  - Users        │    │  - Point Clouds │          │
│  └────────┬────────┘    └─────────────────┘    └─────────────────┘          │
└───────────┼─────────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PIPELINE DE PROCESAMIENTO (Celery Workers)                │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  1. Frame Extraction (OpenCV)                                         │ │
│  │  2. LiDAR + Photogrammetry Fusion                                     │ │
│  │  3. COLMAP SfM (Structure from Motion)                                │ │
│  │  4. 3DGS Training (3D Gaussian Splatting)                             │ │
│  │  5. YOLO Detection (Elementos estructurales)                          │ │
│  │  6. Structural Analysis (FEM + Heurísticas E.060)                     │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CAPA DE PRESENTACIÓN                                      │
│  ┌─────────────────┐    ┌─────────────────────────────────────────────────┐ │
│  │  Three.js       │    │  Report Generator                             │ │
│  │  - 3DGS Viewer  │    │  - PDF con vulnerabilidades                   │ │
│  │  - Hotspots     │    │  - Recomendaciones                            │ │
│  └─────────────────┘    └─────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Estructura del Repositorio

```
SE_PEAV/
│
├── backend/                    # FastAPI + PostgreSQL + Celery
│   ├── app/
│   │   ├── api/v1/            # Endpoints REST
│   │   ├── core/              # Configuración, DB
│   │   ├── models/            # SQLAlchemy models
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── services/          # Lógica de negocio
│   │   └── workers/           # Tareas Celery
│   ├── alembic/               # Migraciones
│   └── tests/                 # Tests
│
├── mobile/                     # Flutter App (iOS/Android)
│   ├── lib/                   # Código Dart
│   ├── ios/                   # Configuración iOS
│   ├── android/               # Configuración Android
│   └── assets/                # Assets estáticos
│
├── frontend/                   # Three.js Viewer
│   ├── src/                   # Código JavaScript/TypeScript
│   └── public/                # Assets públicos
│
├── 01_ingest_layer/           # Extracción de frames (legacy)
├── 02_geometry_engine/        # COLMAP + 3DGS (legacy)
├── 03_ai_analysis/            # YOLO + SQLite (legacy)
├── 04_reporting_etl/          # Generador PDF (legacy)
│
├── docker-compose.yml         # Orquestador de servicios
└── README.md                  # Este archivo
```

---

## Requisitos Previos

| Herramienta | Versión mínima | Uso |
|-------------|---------------|-----|
| Docker | 24.x | Contenedores |
| Docker Compose | 2.x | Orquestación |
| NVIDIA GPU | CUDA ≥ 11.8 | geometry_engine y ai_analysis |
| Flutter SDK | 3.x | App móvil |
| Node.js | 18.x | Frontend |

---

## Puesta en Marcha

### 1. Clonar el repositorio

```bash
git clone https://github.com/tenk1u/SE_PEAV.git
cd SE_PEAV
```

### 2. Crear la estructura de trabajo local

```bash
mkdir -p workspace/raw_data workspace/processed_data
```

### 3. Configurar variables de entorno

```bash
cp backend/.env.example backend/.env
# Editar backend/.env con tus configuraciones
```

### 4. Construir y levantar servicios

```bash
# Servicios de infraestructura
docker compose up -d postgres redis minio

# Backend API
docker compose up -d backend celery_worker

# Pipeline original (opcional)
docker compose --profile pipeline up -d
```

### 5. Ejecutar migraciones

```bash
docker compose exec backend alembic upgrade head
```

---

## API del Backend

Una vez iniciado, la documentación interactiva está disponible en:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Endpoints Principales

#### Autenticación
- `POST /api/v1/auth/register` - Registro de usuarios
- `POST /api/v1/auth/login` - Login
- `GET /api/v1/auth/me` - Usuario actual

#### Proyectos
- `GET /api/v1/projects` - Listar proyectos
- `POST /api/v1/projects` - Crear proyecto
- `GET /api/v1/projects/{id}` - Obtener proyecto

#### Inspecciones
- `POST /api/v1/inspections` - Crear inspección
- `POST /api/v1/inspections/{id}/upload/dron` - Subir video de dron
- `POST /api/v1/inspections/{id}/upload/mobile` - Subir capturas móviles
- `POST /api/v1/inspections/{id}/process` - Iniciar procesamiento
- `GET /api/v1/inspections/{id}/status` - Estado del procesamiento

#### Reportes
- `GET /api/v1/reports` - Listar reportes
- `GET /api/v1/reports/{id}/download` - Descargar PDF
- `GET /api/v1/reports/{id}/viewer` - URL del visor 3D

---

## Análisis E.060 (Norma Peruana)

El sistema implementa las verificaciones de la norma E.060 (Reglamento Nacional de Edificaciones - Albañilería):

| Verificación | Requisito |
|--------------|-----------|
| Espesor mínimo de muros | 15cm (1 piso), 20cm (2 pisos), 25cm (3+ pisos) |
| Confinamiento | Máximo 4m entre confinamientos |
| Relación vano/muro | Máximo 0.6 |
| Refuerzo | Mínimo 0.25% del área bruta |

### Niveles de Vulnerabilidad

| Score | Nivel | Acción |
|-------|-------|--------|
| 0-24 | Bajo | Estructura aceptable |
| 25-49 | Medio | Monitorear |
| 50-74 | Alto | Reforzar recomendado |
| 75-100 | Crítico | Intervención inmediata |

---

## Desarrollo Local (sin Docker)

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Mobile (Flutter)

```bash
cd mobile
flutter pub get
flutter run
```

### Frontend (Three.js)

```bash
cd frontend
npm install
npm run dev
```

---

## Lo que NO se sube a GitHub

Ver `.gitignore`. Resumen:

- `workspace/` – vídeos, frames, nubes de puntos, bases de datos y PDFs generados
- `*.mp4`, `*.avi`, `*.mov` – archivos de vídeo
- `*.ply`, `*.pcd` – nubes de puntos y mallas 3D
- `*.pt`, `*.pth` – pesos de modelos de IA
- `.env` – variables de entorno sensibles
- `node_modules/`, `venv/` – dependencias

---

---

## Estado del Desarrollo

### Resumen General

| Fase | Estado | Progreso |
|------|--------|----------|
| Backend API | ✅ Completado | 100% |
| Infraestructura Docker | ✅ Completado | 100% |
| Análisis E.060 | ✅ Completado | 100% |
| Pipeline de Procesamiento | ✅ Completado | 100% |
| Tests Unitarios | ✅ Completado | 100% |
| App Flutter | ⏳ Pendiente | 0% |
| Visor Three.js | ⏳ Pendiente | 0% |
| Deploy Producción | ⏳ Pendiente | 0% |

### Detalle por Componente

#### ✅ Backend API (Completado)

| Módulo | Estado | Archivo |
|--------|--------|---------|
| Configuración | ✅ | `backend/app/core/config.py` |
| Base de datos | ✅ | `backend/app/core/database.py` |
| Modelos SQLAlchemy | ✅ | `backend/app/models/project.py` |
| Schemas Pydantic | ✅ | `backend/app/schemas/project.py` |
| Autenticación JWT | ✅ | `backend/app/api/v1/auth.py` |
| CRUD Proyectos | ✅ | `backend/app/api/v1/projects.py` |
| CRUD Inspecciones | ✅ | `backend/app/api/v1/inspections.py` |
| Reportes | ✅ | `backend/app/api/v1/reports.py` |
| Upload archivos | ✅ | `backend/app/api/v1/upload.py` |
| Storage S3/MinIO | ✅ | `backend/app/services/storage.py` |
| Migraciones Alembic | ✅ | `backend/alembic/` |

#### ✅ Pipeline de Procesamiento (Completado)

| Módulo | Estado | Archivo | Descripción |
|--------|--------|---------|-------------|
| Extracción de frames | ✅ | `backend/app/services/frame_extractor.py` | Adaptado de `01_ingest_layer` |
| Motor de geometría | ✅ | `backend/app/services/geometry_engine.py` | COLMAP + 3DGS |
| Detección YOLO | ✅ | `backend/app/services/yolo_detector.py` | Elementos constructivos |
| Análisis E.060 | ✅ | `backend/app/services/e060_analysis.py` | Norma peruana |
| Generador de reportes | ✅ | `backend/app/services/report_generator.py` | PDF + HTML |
| Orquestador Celery | ✅ | `backend/app/services/processing.py` | Pipeline completo |

#### ✅ Análisis E.060 (Completado)

| Verificación | Implementado | Descripción |
|--------------|--------------|-------------|
| Espesor mínimo de muros | ✅ | 15cm (1 piso), 20cm (2 pisos), 25cm (3+ pisos) |
| Confinamiento | ✅ | Máximo 4m entre confinamientos |
| Relación vano/muro | ✅ | Máximo 0.6 |
| Refuerzo mínimo | ✅ | 0.25% del área bruta |
| Cálculo de vulnerabilidad | ✅ | Score 0-100 con niveles (Bajo/Medio/Alto/Crítico) |
| Recomendaciones automáticas | ✅ | Basadas en análisis |

#### ✅ Tests Unitarios (Completado)

| Archivo | Tests | Estado |
|---------|-------|--------|
| `backend/tests/conftest.py` | Configuración | ✅ |
| `backend/tests/test_auth.py` | 7 tests | ✅ |
| `backend/tests/test_projects.py` | 8 tests | ✅ |
| `backend/tests/test_inspections.py` | 10 tests | ✅ |
| `backend/tests/test_e060_analysis.py` | 18 tests | ✅ |
| **Total** | **43 tests** | ✅ |

#### ✅ Infraestructura Docker (Completado)

| Servicio | Imagen | Puerto | Estado |
|----------|--------|--------|--------|
| PostgreSQL | postgres:15-alpine | 5432 | ✅ Healthy |
| Redis | redis:7-alpine | 6379 | ✅ Healthy |
| MinIO | minio/minio:latest | 9000/9001 | ✅ Healthy |
| Backend | se_peav/backend | 8000 | ✅ Running |
| Celery Worker | se_peav/backend | - | ✅ Running |

#### ⏳ App Flutter (Pendiente)

| Módulo | Estado | Descripción |
|--------|--------|-------------|
| Setup proyecto | ⏳ | Configuración inicial Flutter |
| UI principal | ⏳ | Pantallas de navegación |
| Captura de video | ⏳ | Grabación con cámara |
| LiDAR Scanner | ⏳ | Escaneo 3D con iPhone Pro |
| AR Tracking | ⏳ | ARKit/ARCore para posicionamiento |
| Upload a servidor | ⏳ | Envío de datos al backend |
| Visualización básica | ⏳ | Previsualización de capturas |

#### ⏳ Visor Three.js (Pendiente)

| Módulo | Estado | Descripción |
|--------|--------|-------------|
| Setup proyecto | ⏳ | Configuración inicial Three.js |
| Carga de modelos 3DGS | ⏳ | Conversión y renderizado |
| Interactividad | ⏳ | Rotación, zoom, pan |
| Hotspots de vulnerabilidad | ⏳ | Marcadores en el modelo |
| Mediciones | ⏳ | Herramienta de medición |
| Exportación | ⏳ | Captura de pantalla, compartir |

### Endpoints API Implementados

#### Autenticación
| Método | Endpoint | Estado | Descripción |
|--------|----------|--------|-------------|
| POST | `/api/v1/auth/register` | ✅ | Registro de usuarios |
| POST | `/api/v1/auth/login` | ✅ | Login con JWT |
| POST | `/api/v1/auth/token` | ✅ | OAuth2 token |
| GET | `/api/v1/auth/me` | ✅ | Usuario actual |

#### Proyectos
| Método | Endpoint | Estado | Descripción |
|--------|----------|--------|-------------|
| GET | `/api/v1/projects/` | ✅ | Listar proyectos |
| POST | `/api/v1/projects/` | ✅ | Crear proyecto |
| GET | `/api/v1/projects/{id}` | ✅ | Obtener proyecto |
| PATCH | `/api/v1/projects/{id}` | ✅ | Actualizar proyecto |
| DELETE | `/api/v1/projects/{id}` | ✅ | Eliminar proyecto |

#### Inspecciones
| Método | Endpoint | Estado | Descripción |
|--------|----------|--------|-------------|
| GET | `/api/v1/inspections/` | ✅ | Listar inspecciones |
| POST | `/api/v1/inspections/` | ✅ | Crear inspección |
| GET | `/api/v1/inspections/{id}` | ✅ | Obtener inspección |
| GET | `/api/v1/inspections/{id}/status` | ✅ | Estado procesamiento |
| POST | `/api/v1/inspections/{id}/upload/dron` | ✅ | Subir video dron |
| POST | `/api/v1/inspections/{id}/upload/mobile` | ✅ | Subir capturas móvil |
| POST | `/api/v1/inspections/{id}/process` | ✅ | Iniciar procesamiento |
| GET | `/api/v1/inspections/{id}/detections` | ✅ | Detecciones YOLO |
| GET | `/api/v1/inspections/{id}/metrics` | ✅ | Métricas E.060 |

#### Reportes
| Método | Endpoint | Estado | Descripción |
|--------|----------|--------|-------------|
| GET | `/api/v1/reports/` | ✅ | Listar reportes |
| GET | `/api/v1/reports/{id}` | ✅ | Obtener reporte |
| GET | `/api/v1/reports/{id}/download` | ✅ | Descargar PDF |
| GET | `/api/v1/reports/{id}/viewer` | ✅ | URL visor 3D |
| POST | `/api/v1/reports/{id}/generate` | ✅ | Generar reporte |

#### Upload
| Método | Endpoint | Estado | Descripción |
|--------|----------|--------|-------------|
| POST | `/api/v1/upload/video` | ✅ | Subir video |
| POST | `/api/v1/upload/images` | ✅ | Subir imágenes |
| POST | `/api/v1/upload/lidar` | ✅ | Subir datos LiDAR |
| POST | `/api/v1/upload/point-cloud` | ✅ | Subir nube de puntos |

### Próximos Pasos

1. **Setup Flutter** (Prioridad Alta)
   - Configurar proyecto Flutter
   - Implementar captura de video
   - Integrar LiDAR Scanner (iPhone Pro)

2. **Visor Three.js** (Prioridad Media)
   - Configurar proyecto Three.js
   - Implementar carga de modelos 3DGS
   - Agregar interactividad básica

3. **Integrar YOLO** (Prioridad Alta)
   - Descargar/entrenar modelo YOLO
   - Integrar con pipeline de procesamiento
   - Optimizar detección para elementos peruanos

4. **Deploy Producción** (Prioridad Baja)
   - Configurar dominio y SSL
   - Desplegar en cloud (AWS/GCP)
   - Monitoreo y logging

---

## Licencia

Proyecto académico — Tesis II. Todos los derechos reservados.
