"""
extract_exif.py
---------------
Lee los metadatos EXIF (incluidas coordenadas GPS si existen) de todas las
imágenes de un directorio y los exporta a un archivo JSON.

Uso:
    python extract_exif.py --input <dir_imagenes> --output <archivo.json>
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS


# ─── Funciones auxiliares ────────────────────────────────────────────────────


def _get_exif_data(image: Image.Image) -> Dict[str, Any]:
    """Extrae todos los tags EXIF de una imagen PIL."""
    exif_data: Dict[str, Any] = {}
    raw = image._getexif()  # type: ignore[attr-defined]
    if raw is None:
        return exif_data
    for tag_id, value in raw.items():
        tag = TAGS.get(tag_id, tag_id)
        if tag == "GPSInfo":
            gps: Dict[str, Any] = {}
            for gps_id, gps_val in value.items():
                gps_tag = GPSTAGS.get(gps_id, gps_id)
                gps[gps_tag] = gps_val
            exif_data[tag] = gps
        else:
            # Convertir tipos no serializables
            if isinstance(value, bytes):
                value = value.hex()
            exif_data[str(tag)] = value
    return exif_data


def _dms_to_decimal(dms: Any, ref: str) -> Optional[float]:
    """Convierte coordenadas DMS (grados, minutos, segundos) a grados decimales."""
    try:
        degrees = float(dms[0])
        minutes = float(dms[1])
        seconds = float(dms[2])
        decimal = degrees + minutes / 60 + seconds / 3600
        if ref in ("S", "W"):
            decimal = -decimal
        return round(decimal, 7)
    except (TypeError, IndexError, ZeroDivisionError):
        return None


def extract_exif_from_dir(
    input_dir: str,
    output_path: str,
    extensions: tuple = (".png", ".jpg", ".jpeg", ".tiff", ".tif"),
) -> int:
    """
    Recorre *input_dir* y escribe un JSON con los metadatos EXIF de cada imagen.

    Returns:
        Número de imágenes procesadas.
    """
    input_path = Path(input_dir)
    if not input_path.is_dir():
        print(f"[ERROR] Directorio no encontrado: {input_dir}", file=sys.stderr)
        sys.exit(1)

    image_files: List[Path] = sorted(
        p for p in input_path.iterdir() if p.suffix.lower() in extensions
    )

    if not image_files:
        print(f"[WARN] No se encontraron imágenes en: {input_dir}")
        return 0

    results: List[Dict[str, Any]] = []
    for img_file in image_files:
        entry: Dict[str, Any] = {"file": img_file.name}
        try:
            with Image.open(img_file) as img:
                exif = _get_exif_data(img)
                # Añadir coordenadas decimales si hay GPS
                gps_info = exif.get("GPSInfo", {})
                lat = _dms_to_decimal(
                    gps_info.get("GPSLatitude"), gps_info.get("GPSLatitudeRef", "N")
                )
                lon = _dms_to_decimal(
                    gps_info.get("GPSLongitude"), gps_info.get("GPSLongitudeRef", "E")
                )
                if lat is not None and lon is not None:
                    exif["latitude_decimal"] = lat
                    exif["longitude_decimal"] = lon
                entry["exif"] = exif
        except Exception as exc:
            entry["error"] = str(exc)
        results.append(entry)

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=2, ensure_ascii=False, default=str)

    print(f"[OK] Metadatos de {len(results)} imágenes guardados en '{output_path}'")
    return len(results)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extrae metadatos EXIF de imágenes y los exporta a JSON."
    )
    parser.add_argument("--input", required=True, help="Directorio con imágenes")
    parser.add_argument("--output", required=True, help="Archivo JSON de salida")
    args = parser.parse_args()
    extract_exif_from_dir(args.input, args.output)


if __name__ == "__main__":
    main()
