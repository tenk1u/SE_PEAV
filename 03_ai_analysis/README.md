# 03 – AI Analysis

**Tecnología:** Python / PyTorch (LibTorch) / YOLO / SQLite  
**Propósito:** Detección de elementos constructivos (vigas, columnas, muros, daños) sobre los frames y la nube de puntos 3DGS. Los resultados se persisten en una base de datos SQLite para consulta por la capa ETL.

## Estructura

```
03_ai_analysis/
├── detect_elements.py      # Inferencia YOLO sobre frames
├── analyze_structure.py    # Análisis estructural con LibTorch
├── db_manager.py           # CRUD sobre la base de datos SQLite
├── schema.sql              # Esquema de la base de datos
├── models/
│   └── weights/            # Pesos de modelos (ignorados en Git, >100 MB)
├── requirements.txt        # Dependencias Python
└── output/                 # Resultados de análisis (ignorado en Git)
```

## Dependencias

```bash
pip install -r requirements.txt
```

| Paquete           | Uso                                     |
|-------------------|-----------------------------------------|
| torch             | Motor de inferencia (LibTorch via Python)|
| ultralytics       | YOLO v8+ detection & segmentation       |
| opencv-python     | Pre/post-procesado de imágenes          |
| numpy             | Operaciones matriciales                 |
| tqdm              | Barra de progreso                       |

## Uso rápido

```bash
# 1. Detectar elementos en los frames extraídos
python detect_elements.py \
    --images ../01_ingest_layer/output/frames/ \
    --weights models/weights/yolo_construction.pt \
    --db      output/analysis.db

# 2. Análisis estructural sobre la nube de puntos
python analyze_structure.py \
    --ply ../workspace/processed_data/3dgs_model/point_cloud.ply \
    --db  output/analysis.db
```

## Esquema de base de datos

Ver [`schema.sql`](schema.sql) para la definición completa de tablas.
