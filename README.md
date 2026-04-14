# SE-PEAV · Tesis 3DGS Autoconstrucción

**Sistema Edge de Predimensionamiento Estructural y Análisis de Vulnerabilidad**  
Desarrollado para el curso de **Tesis II**

---

## Estructura del repositorio

```
Tesis-3DGS-Autoconstruccion/
│
├── 01_ingest_layer/          # Python/C++  – Extracción de frames y metadatos EXIF
├── 02_geometry_engine/       # C++/CUDA    – COLMAP (SfM) y motor 3D Gaussian Splatting
├── 03_ai_analysis/           # Python/PyTorch – YOLO, LibTorch y base de datos SQLite
├── 04_reporting_etl/         # Python      – Generador de informes PDF con Jinja2
│
├── workspace/                # ⚠️ IGNORADA en Git (.gitignore)
│   ├── raw_data/             #    Vídeos de prueba (no se suben a GitHub)
│   └── processed_data/       #    Resultados del pipeline (frames, PLY, BD, PDFs)
│
├── docker-compose.yml        # Orquestador de contenedores
├── .gitignore                # Excluye vídeos pesados, archivos .ply y bases de datos locales
└── README.md                 # Este archivo
```

---

## Requisitos previos

| Herramienta     | Versión mínima | Uso                              |
|-----------------|---------------|----------------------------------|
| Docker          | 24.x          | Contenedores                     |
| Docker Compose  | 2.x           | Orquestación                     |
| NVIDIA GPU      | CUDA ≥ 11.8   | `geometry_engine` y `ai_analysis`|
| NVIDIA Container Toolkit | – | Soporte GPU en Docker            |

> **Sin GPU:** los servicios `geometry_engine` y `ai_analysis` requieren GPU.
> Para pruebas en CPU, comenta el bloque `deploy.resources` en `docker-compose.yml`.

---

## Puesta en marcha

### 1. Clonar el repositorio

```bash
git clone https://github.com/tenk1u/SE_PEAV.git
cd SE_PEAV
```

### 2. Crear la estructura de trabajo local

```bash
mkdir -p workspace/raw_data workspace/processed_data
```

Copia tus vídeos de obra en `workspace/raw_data/`.

### 3. Construir las imágenes Docker

```bash
docker compose build
```

---

## Ejecución del pipeline

Cada paso se ejecuta de forma independiente con `docker compose run`.

### Paso 1 – Extracción de frames

```bash
docker compose run --rm ingest \
  --input  /data/raw_data/video.mp4 \
  --output /data/processed_data/frames/ \
  --fps    0.5
```

### Paso 2 – Reconstrucción 3-D con COLMAP

```bash
docker compose run --rm geometry_engine \
  --images    /data/processed_data/frames/ \
  --workspace /data/processed_data/colmap_output/
```

### Paso 3 – Entrenamiento 3DGS

```bash
docker compose run --rm geometry_engine \
  python train_3dgs.py \
  --source_path /data/processed_data/colmap_output/ \
  --model_path  /data/processed_data/3dgs_model/
```

### Paso 4 – Detección de elementos con YOLO

```bash
docker compose run --rm ai_analysis \
  --images     /data/processed_data/frames/ \
  --weights    /app/models/weights/yolo_construction.pt \
  --db         /data/processed_data/analysis.db
```

### Paso 5 – Análisis estructural de la nube de puntos

```bash
docker compose run --rm ai_analysis \
  python analyze_structure.py \
  --ply /data/processed_data/3dgs_model/point_cloud.ply \
  --db  /data/processed_data/analysis.db
```

### Paso 6 – Generación del informe PDF

```bash
docker compose run --rm reporting_etl \
  --db            /data/processed_data/analysis.db \
  --inspection_id 1 \
  --output        /data/processed_data/reports/informe_1.pdf
```

El PDF se encontrará en `workspace/processed_data/reports/`.

---

## Desarrollo local (sin Docker)

Instala las dependencias de cada capa por separado:

```bash
pip install -r 01_ingest_layer/requirements.txt
pip install -r 03_ai_analysis/requirements.txt
pip install -r 04_reporting_etl/requirements.txt
```

Para la capa de geometría, consulta [`02_geometry_engine/README.md`](02_geometry_engine/README.md).

---

## Lo que NO se sube a GitHub

Ver `.gitignore`. Resumen:

- `workspace/` – vídeos, frames, nubes de puntos, bases de datos y PDFs generados
- `*.mp4`, `*.avi`, `*.mov`, … – archivos de vídeo
- `*.ply`, `*.pcd`, … – nubes de puntos y mallas 3-D
- `*.db`, `*.sqlite` – bases de datos locales
- `*.pt`, `*.pth`, `*.onnx` – pesos de modelos de IA
- Artefactos de compilación (`build/`, `__pycache__/`, …)

---

## Licencia

Proyecto académico — Tesis II. Todos los derechos reservados.
