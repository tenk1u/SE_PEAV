"""
detect_elements.py
------------------
Inferencia YOLO sobre un directorio de frames para detectar elementos
constructivos (columnas, vigas, muros, fisuras, etc.).

Los resultados se guardan en la base de datos SQLite del proyecto.

Uso:
    python detect_elements.py \
        --images  ../01_ingest_layer/output/frames/ \
        --weights models/weights/yolo_construction.pt \
        --db      output/analysis.db \
        [--conf 0.25] [--project_id 1]
"""

import argparse
import os
import sys
from pathlib import Path

from tqdm import tqdm
from ultralytics import YOLO

from db_manager import DatabaseManager


def detect_elements(
    images_dir: str,
    weights_path: str,
    db_path: str,
    conf_threshold: float = 0.25,
    project_id: int = 1,
) -> None:
    images = Path(images_dir)
    if not images.is_dir():
        print(f"[ERROR] Directorio no encontrado: {images_dir}", file=sys.stderr)
        sys.exit(1)

    if not Path(weights_path).is_file():
        print(f"[ERROR] Pesos no encontrados: {weights_path}", file=sys.stderr)
        sys.exit(1)

    image_files = sorted(
        p for p in images.iterdir()
        if p.suffix.lower() in (".png", ".jpg", ".jpeg")
    )

    if not image_files:
        print(f"[WARN] No se encontraron imágenes en: {images_dir}")
        return

    model = YOLO(weights_path)

    with DatabaseManager(db_path) as db:
        inspection_id = db.create_inspection(
            project_id=project_id,
            video_path=images_dir,
        )
        db.update_inspection_status(inspection_id, "processing")

        for img_path in tqdm(image_files, desc="Detectando", unit="frame"):
            results = model(str(img_path), conf=conf_threshold, verbose=False)
            for result in results:
                if result.boxes is None:
                    continue
                for box in result.boxes:
                    cls_id = int(box.cls[0])
                    class_name = model.names[cls_id]
                    confidence = float(box.conf[0])
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    db.save_detection(
                        inspection_id=inspection_id,
                        frame_file=img_path.name,
                        class_name=class_name,
                        confidence=confidence,
                        bbox=(x1, y1, x2, y2),
                    )

        db.update_inspection_status(inspection_id, "done")

    print(f"[OK] Detección completa. inspection_id={inspection_id} — DB: '{db_path}'")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Detecta elementos constructivos con YOLO."
    )
    parser.add_argument("--images", required=True, help="Directorio de frames")
    parser.add_argument("--weights", required=True, help="Ruta a los pesos YOLO (.pt)")
    parser.add_argument("--db", required=True, help="Ruta a la base de datos SQLite")
    parser.add_argument("--conf", type=float, default=0.25, help="Umbral de confianza")
    parser.add_argument("--project_id", type=int, default=1, help="ID del proyecto")
    args = parser.parse_args()
    detect_elements(args.images, args.weights, args.db, args.conf, args.project_id)


if __name__ == "__main__":
    main()
