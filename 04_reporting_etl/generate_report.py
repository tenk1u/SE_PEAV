"""
generate_report.py
------------------
Pipeline ETL que:
  1. Extrae datos de la base de datos SQLite (inspección, detecciones, métricas).
  2. Los transforma en un contexto Jinja2.
  3. Renderiza la plantilla HTML.
  4. Convierte el HTML a PDF con WeasyPrint.

Uso:
    python generate_report.py \
        --db            ../03_ai_analysis/output/analysis.db \
        --inspection_id 1 \
        --output        output/informe_inspeccion_1.pdf
"""

import argparse
import os
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape


TEMPLATES_DIR = Path(__file__).parent / "templates"
TEMPLATE_FILE = "report_template.html"


# ─── Extracción (E) ───────────────────────────────────────────────────────────

def _fetch_one(conn: sqlite3.Connection, query: str, params: tuple = ()) -> dict[str, Any]:
    cur = conn.execute(query, params)
    cols = [d[0] for d in cur.description]
    row = cur.fetchone()
    return dict(zip(cols, row)) if row else {}


def _fetch_all(conn: sqlite3.Connection, query: str, params: tuple = ()) -> list[dict[str, Any]]:
    cur = conn.execute(query, params)
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def extract(db_path: str, inspection_id: int) -> dict[str, Any]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # type: ignore[assignment]

    inspection = _fetch_one(conn, "SELECT * FROM inspections WHERE id=?", (inspection_id,))
    if not inspection:
        print(f"[ERROR] No se encontró la inspección con id={inspection_id}", file=sys.stderr)
        sys.exit(1)

    project = _fetch_one(
        conn, "SELECT * FROM projects WHERE id=?", (inspection["project_id"],)
    )
    detections = _fetch_all(
        conn, "SELECT * FROM detections WHERE inspection_id=?", (inspection_id,)
    )
    metrics = _fetch_all(
        conn, "SELECT * FROM structural_metrics WHERE inspection_id=?", (inspection_id,)
    )
    conn.close()
    return {
        "project": project,
        "inspection": inspection,
        "detections": detections,
        "metrics": metrics,
    }


# ─── Transformación (T) ───────────────────────────────────────────────────────

def transform(raw: dict[str, Any]) -> dict[str, Any]:
    detections = raw["detections"]
    confidences = [d["confidence"] for d in detections if d.get("confidence") is not None]
    classes = {d["class_name"] for d in detections}

    return {
        **raw,
        "total_detections": len(detections),
        "unique_classes": len(classes),
        "avg_confidence": sum(confidences) / len(confidences) if confidences else 0.0,
        "generated_at": datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    }


# ─── Carga / Generación (L) ───────────────────────────────────────────────────

def load(context: dict[str, Any], output_path: str) -> None:
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html"]),
    )
    template = env.get_template(TEMPLATE_FILE)
    html_content = template.render(**context)

    # Guardar HTML temporal para depuración
    html_path = Path(output_path).with_suffix(".html")
    html_path.parent.mkdir(parents=True, exist_ok=True)
    html_path.write_text(html_content, encoding="utf-8")

    # Convertir a PDF con WeasyPrint
    try:
        from weasyprint import HTML  # type: ignore[import]
        HTML(string=html_content, base_url=str(TEMPLATES_DIR)).write_pdf(output_path)
        print(f"[OK] PDF generado en '{output_path}'")
    except ImportError:
        print(
            "[WARN] WeasyPrint no está instalado. Se guardó sólo el HTML intermedio:\n"
            f"       {html_path}\n"
            "       Instala WeasyPrint con: pip install weasyprint",
        )


# ─── Pipeline principal ───────────────────────────────────────────────────────

def generate_report(db_path: str, inspection_id: int, output_path: str) -> None:
    print(f"[ETL] Extrayendo datos de '{db_path}' (inspection_id={inspection_id})…")
    raw = extract(db_path, inspection_id)

    print("[ETL] Transformando datos…")
    context = transform(raw)

    print(f"[ETL] Generando informe en '{output_path}'…")
    load(context, output_path)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Genera un informe PDF a partir de la base de datos de análisis."
    )
    parser.add_argument("--db", required=True, help="Ruta a la base de datos SQLite")
    parser.add_argument(
        "--inspection_id", type=int, required=True,
        help="ID de la inspección a reportar",
    )
    parser.add_argument("--output", required=True, help="Ruta del PDF de salida")
    args = parser.parse_args()
    generate_report(args.db, args.inspection_id, args.output)


if __name__ == "__main__":
    main()
