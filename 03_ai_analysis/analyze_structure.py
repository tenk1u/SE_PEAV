"""
analyze_structure.py
---------------------
Análisis estructural simplificado sobre la nube de puntos generada por 3DGS.
Carga el archivo PLY, calcula métricas geométricas básicas (extensión del
bounding-box, densidad de puntos, etc.) y las persiste en SQLite.

Uso:
    python analyze_structure.py \
        --ply ../workspace/processed_data/3dgs_model/point_cloud.ply \
        --db  output/analysis.db \
        [--inspection_id 1]
"""

import argparse
import sys
from pathlib import Path

import numpy as np

from db_manager import DatabaseManager


def load_ply_positions(ply_path: str) -> np.ndarray:
    """
    Lee las posiciones XYZ de un archivo PLY (binario o ASCII) de forma
    minimal sin dependencias pesadas, usando numpy.

    Para archivos PLY complejos se recomienda instalar `plyfile`.
    """
    try:
        from plyfile import PlyData  # type: ignore[import]
        ply_data = PlyData.read(ply_path)
        vertex = ply_data["vertex"]
        return np.column_stack([vertex["x"], vertex["y"], vertex["z"]])
    except ImportError:
        pass

    # Fallback: leer PLY ASCII simple
    positions = []
    header_done = False
    with open(ply_path, "r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if line == "end_header":
                header_done = True
                continue
            if header_done:
                parts = line.split()
                if len(parts) >= 3:
                    try:
                        positions.append([float(p) for p in parts[:3]])
                    except ValueError:
                        continue
    return np.array(positions, dtype=np.float32)


def analyze_structure(ply_path: str, db_path: str, inspection_id: int = 1) -> None:
    path = Path(ply_path)
    if not path.is_file():
        print(f"[ERROR] Archivo PLY no encontrado: {ply_path}", file=sys.stderr)
        sys.exit(1)

    print(f"[INFO] Cargando nube de puntos: {ply_path}")
    points = load_ply_positions(ply_path)

    if points.size == 0:
        print("[WARN] La nube de puntos está vacía.")
        return

    min_xyz = points.min(axis=0)
    max_xyz = points.max(axis=0)
    extent = max_xyz - min_xyz
    volume_bb = float(extent[0] * extent[1] * extent[2])
    density = len(points) / volume_bb if volume_bb > 0 else 0.0

    metrics = [
        ("num_points",   float(len(points)),   "puntos"),
        ("extent_x",     float(extent[0]),      "m"),
        ("extent_y",     float(extent[1]),      "m"),
        ("extent_z",     float(extent[2]),      "m"),
        ("bounding_box_volume", volume_bb,      "m³"),
        ("point_density",       density,        "pts/m³"),
    ]

    with DatabaseManager(db_path) as db:
        for name, value, unit in metrics:
            db.save_metric(inspection_id, name, value, unit)
            print(f"  {name}: {value:.4f} {unit}")

    print(f"[OK] Métricas guardadas en '{db_path}' (inspection_id={inspection_id})")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analiza métricas estructurales de una nube de puntos PLY."
    )
    parser.add_argument("--ply", required=True, help="Ruta al archivo PLY")
    parser.add_argument("--db", required=True, help="Ruta a la base de datos SQLite")
    parser.add_argument(
        "--inspection_id", type=int, default=1,
        help="ID de la inspección en la BD (default: 1)",
    )
    args = parser.parse_args()
    analyze_structure(args.ply, args.db, args.inspection_id)


if __name__ == "__main__":
    main()
