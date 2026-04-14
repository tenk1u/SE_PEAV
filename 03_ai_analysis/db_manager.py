"""
db_manager.py
-------------
CRUD simplificado sobre la base de datos SQLite del proyecto.
Inicializa el esquema si la base de datos no existe.

Uso como módulo:
    from db_manager import DatabaseManager
    db = DatabaseManager("output/analysis.db")
    inspection_id = db.create_inspection(project_id=1, video_path="...")
    db.save_detection(inspection_id, frame_file="frame_000001.png",
                      class_name="columna", confidence=0.92,
                      bbox=(10, 20, 110, 220))
"""

import sqlite3
from pathlib import Path
from typing import Any, Optional


SCHEMA_FILE = Path(__file__).parent / "schema.sql"


class DatabaseManager:
    def __init__(self, db_path: str) -> None:
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("PRAGMA journal_mode=WAL;")
        self.conn.execute("PRAGMA foreign_keys=ON;")
        self._init_schema()

    # ─── Inicialización ───────────────────────────────────────────────────────

    def _init_schema(self) -> None:
        schema = SCHEMA_FILE.read_text(encoding="utf-8")
        self.conn.executescript(schema)
        self.conn.commit()

    # ─── Proyectos ────────────────────────────────────────────────────────────

    def create_project(self, name: str, description: str = "") -> int:
        cur = self.conn.execute(
            "INSERT INTO projects (name, description) VALUES (?, ?)",
            (name, description),
        )
        self.conn.commit()
        return cur.lastrowid  # type: ignore[return-value]

    # ─── Inspecciones ─────────────────────────────────────────────────────────

    def create_inspection(self, project_id: int, video_path: str = "") -> int:
        cur = self.conn.execute(
            "INSERT INTO inspections (project_id, video_path) VALUES (?, ?)",
            (project_id, video_path),
        )
        self.conn.commit()
        return cur.lastrowid  # type: ignore[return-value]

    def update_inspection_status(self, inspection_id: int, status: str) -> None:
        self.conn.execute(
            "UPDATE inspections SET status=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (status, inspection_id),
        )
        self.conn.commit()

    # ─── Detecciones ──────────────────────────────────────────────────────────

    def save_detection(
        self,
        inspection_id: int,
        frame_file: str,
        class_name: str,
        confidence: float,
        bbox: Optional[tuple[float, float, float, float]] = None,
    ) -> int:
        x1, y1, x2, y2 = bbox if bbox else (None, None, None, None)
        cur = self.conn.execute(
            """INSERT INTO detections
               (inspection_id, frame_file, class_name, confidence,
                bbox_x1, bbox_y1, bbox_x2, bbox_y2)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (inspection_id, frame_file, class_name, confidence, x1, y1, x2, y2),
        )
        self.conn.commit()
        return cur.lastrowid  # type: ignore[return-value]

    # ─── Métricas estructurales ───────────────────────────────────────────────

    def save_metric(
        self,
        inspection_id: int,
        metric_name: str,
        metric_value: float,
        unit: str = "",
    ) -> int:
        cur = self.conn.execute(
            """INSERT INTO structural_metrics
               (inspection_id, metric_name, metric_value, unit)
               VALUES (?, ?, ?, ?)""",
            (inspection_id, metric_name, metric_value, unit),
        )
        self.conn.commit()
        return cur.lastrowid  # type: ignore[return-value]

    # ─── Consultas ────────────────────────────────────────────────────────────

    def get_detections(self, inspection_id: int) -> list[dict[str, Any]]:
        cur = self.conn.execute(
            "SELECT * FROM detections WHERE inspection_id=?", (inspection_id,)
        )
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]

    def get_metrics(self, inspection_id: int) -> list[dict[str, Any]]:
        cur = self.conn.execute(
            "SELECT * FROM structural_metrics WHERE inspection_id=?", (inspection_id,)
        )
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]

    # ─── Cierre ───────────────────────────────────────────────────────────────

    def close(self) -> None:
        self.conn.close()

    def __enter__(self) -> "DatabaseManager":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()
