# 04 – Reporting ETL

**Tecnología:** Python / Jinja2 / WeasyPrint  
**Propósito:** Extrae los datos de análisis de la base de datos SQLite, los transforma en un objeto de contexto estructurado y genera un informe PDF listo para entregar al cliente.

## Estructura

```
04_reporting_etl/
├── generate_report.py       # Pipeline ETL + generación de PDF
├── templates/
│   └── report_template.html # Plantilla Jinja2 del informe
├── requirements.txt         # Dependencias Python
└── output/                  # PDFs generados (ignorado en Git)
```

## Dependencias

```bash
pip install -r requirements.txt
```

| Paquete      | Uso                                   |
|--------------|---------------------------------------|
| Jinja2       | Motor de plantillas HTML              |
| WeasyPrint   | Conversión HTML → PDF                 |
| Pillow       | Inserción de imágenes en el informe   |

## Uso rápido

```bash
python generate_report.py \
    --db           ../03_ai_analysis/output/analysis.db \
    --inspection_id 1 \
    --output       output/informe_inspeccion_1.pdf
```

## Salidas esperadas

- `output/informe_inspeccion_<id>.pdf` – informe PDF con:
  - Resumen del proyecto e inspección
  - Tabla de detecciones YOLO
  - Métricas estructurales
  - Imágenes representativas de la escena 3D
