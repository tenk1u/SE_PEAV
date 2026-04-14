"""
extract_frames.py
-----------------
Extrae frames individuales de un archivo de vídeo y los guarda como imágenes PNG.

Uso:
    python extract_frames.py --input <video> --output <dir> [--fps <rate>]

Argumentos:
    --input   Ruta al archivo de vídeo de entrada.
    --output  Directorio donde se guardarán los frames extraídos.
    --fps     Tasa de extracción en frames por segundo (default: 1.0).
              Valores < 1 extraen menos de un frame por segundo
              (ej. 0.5 → 1 frame cada 2 s).
"""

import argparse
import os
import sys

import cv2
from tqdm import tqdm


def extract_frames(input_path: str, output_dir: str, fps: float = 1.0) -> int:
    """
    Lee un vídeo y guarda frames en *output_dir* a la tasa indicada.

    Returns:
        Número total de frames guardados.
    """
    if not os.path.isfile(input_path):
        print(f"[ERROR] No se encontró el vídeo: {input_path}", file=sys.stderr)
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)

    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        print(f"[ERROR] No se pudo abrir el vídeo: {input_path}", file=sys.stderr)
        sys.exit(1)

    video_fps: float = cap.get(cv2.CAP_PROP_FPS)
    total_frames: int = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_interval: int = max(1, round(video_fps / fps))

    saved = 0
    with tqdm(total=total_frames, desc="Extrayendo frames", unit="frame") as pbar:
        frame_idx = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            if frame_idx % frame_interval == 0:
                filename = os.path.join(output_dir, f"frame_{saved:06d}.png")
                cv2.imwrite(filename, frame)
                saved += 1
            frame_idx += 1
            pbar.update(1)

    cap.release()
    print(f"[OK] {saved} frames guardados en '{output_dir}'")
    return saved


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extrae frames de un vídeo a una tasa configurable."
    )
    parser.add_argument("--input", required=True, help="Ruta al vídeo de entrada")
    parser.add_argument("--output", required=True, help="Directorio de salida")
    parser.add_argument(
        "--fps",
        type=float,
        default=1.0,
        help="Frames por segundo a extraer (default: 1.0)",
    )
    args = parser.parse_args()
    extract_frames(args.input, args.output, args.fps)


if __name__ == "__main__":
    main()
