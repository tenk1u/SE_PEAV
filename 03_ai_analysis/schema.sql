-- schema.sql
-- Esquema de la base de datos SQLite para el análisis de estructuras.

-- ─── Proyectos ───────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS projects (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL,
    description TEXT,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ─── Inspecciones (cada procesamiento de un vídeo) ───────────────────────────
CREATE TABLE IF NOT EXISTS inspections (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id  INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    video_path  TEXT,
    status      TEXT    NOT NULL DEFAULT 'pending',  -- pending | processing | done | error
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ─── Detecciones YOLO por frame ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS detections (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    inspection_id INTEGER NOT NULL REFERENCES inspections(id) ON DELETE CASCADE,
    frame_file    TEXT    NOT NULL,
    class_name    TEXT    NOT NULL,
    confidence    REAL    NOT NULL,
    bbox_x1       REAL,
    bbox_y1       REAL,
    bbox_x2       REAL,
    bbox_y2       REAL,
    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ─── Métricas estructurales ───────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS structural_metrics (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    inspection_id INTEGER NOT NULL REFERENCES inspections(id) ON DELETE CASCADE,
    metric_name   TEXT    NOT NULL,
    metric_value  REAL    NOT NULL,
    unit          TEXT,
    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ─── Índices ──────────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_detections_inspection ON detections(inspection_id);
CREATE INDEX IF NOT EXISTS idx_metrics_inspection    ON structural_metrics(inspection_id);
