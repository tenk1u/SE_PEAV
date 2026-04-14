"""
colmap_runner.py
----------------
Wrapper Python para ejecutar el pipeline completo de COLMAP:
    1. feature_extractor  – detecta y describe keypoints en cada imagen.
    2. exhaustive_matcher – empareja features entre todos los pares de imágenes.
    3. mapper             – reconstrucción Structure-from-Motion (SfM).
    4. image_undistorter  – prepara imágenes para MVS / 3DGS.

Requisitos:
    - COLMAP instalado y accesible en el PATH (o en /usr/local/bin/colmap).

Uso:
    python colmap_runner.py --images <dir_frames> --workspace <dir_salida>
"""

import argparse
import subprocess
import sys
from pathlib import Path


COLMAP_BIN = "colmap"


def run(cmd: list[str]) -> None:
    """Ejecuta un comando y sale con error si falla."""
    print(f"\n[COLMAP] $ {' '.join(cmd)}")
    result = subprocess.run(cmd, check=False)
    if result.returncode != 0:
        print(f"[ERROR] El comando falló con código {result.returncode}", file=sys.stderr)
        sys.exit(result.returncode)


def run_colmap_pipeline(images_dir: str, workspace_dir: str) -> None:
    images = Path(images_dir).resolve()
    workspace = Path(workspace_dir).resolve()
    database = workspace / "database.db"
    sparse_dir = workspace / "sparse"
    dense_dir = workspace / "dense"

    workspace.mkdir(parents=True, exist_ok=True)
    sparse_dir.mkdir(parents=True, exist_ok=True)
    dense_dir.mkdir(parents=True, exist_ok=True)

    # 1. Extracción de features
    run([
        COLMAP_BIN, "feature_extractor",
        "--database_path", str(database),
        "--image_path", str(images),
        "--ImageReader.single_camera", "1",
    ])

    # 2. Matching exhaustivo
    run([
        COLMAP_BIN, "exhaustive_matcher",
        "--database_path", str(database),
    ])

    # 3. SfM mapper
    run([
        COLMAP_BIN, "mapper",
        "--database_path", str(database),
        "--image_path", str(images),
        "--output_path", str(sparse_dir),
    ])

    # 4. Undistort para MVS / 3DGS
    run([
        COLMAP_BIN, "image_undistorter",
        "--image_path", str(images),
        "--input_path", str(sparse_dir / "0"),
        "--output_path", str(dense_dir),
        "--output_type", "COLMAP",
    ])

    print(f"\n[OK] Pipeline COLMAP completo. Resultados en '{workspace_dir}'")


def main() -> None:
    parser = argparse.ArgumentParser(description="Ejecuta el pipeline COLMAP completo.")
    parser.add_argument("--images", required=True, help="Directorio de imágenes de entrada")
    parser.add_argument("--workspace", required=True, help="Directorio de trabajo/salida")
    args = parser.parse_args()
    run_colmap_pipeline(args.images, args.workspace)


if __name__ == "__main__":
    main()
