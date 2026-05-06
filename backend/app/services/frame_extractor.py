"""
Servicio de extracción de frames - Adaptado de 01_ingest_layer.

Este servicio extrae frames de videos (dron o móvil) y los almacena
en el sistema de archivos o S3.
"""
import cv2
import numpy as np
from pathlib import Path
from typing import List, Optional, Tuple
from dataclasses import dataclass
import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging

logger = logging.getLogger(__name__)


@dataclass
class FrameExtractionResult:
    """Resultado de la extracción de frames."""
    frames: List[str]  # Lista de paths de frames extraídos
    total_frames: int
    fps_used: float
    duration_seconds: float
    extraction_time_ms: float


class FrameExtractor:
    """Extractor de frames de videos."""

    def __init__(self, output_dir: str, target_fps: float = 0.5):
        """
        Args:
            output_dir: Directorio donde guardar los frames
            target_fps: Frames por segundo a extraer (0.5 = 1 frame cada 2 segundos)
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.target_fps = target_fps

    def extract_frames_from_video(
        self,
        video_path: str,
        max_frames: Optional[int] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None
    ) -> FrameExtractionResult:
        """
        Extrae frames de un archivo de video.

        Args:
            video_path: Ruta al archivo de video
            max_frames: Número máximo de frames a extraer
            start_time: Tiempo de inicio en segundos
            end_time: Tiempo de fin en segundos

        Returns:
            FrameExtractionResult con los frames extraídos
        """
        import time
        start = time.time()

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"No se pudo abrir el video: {video_path}")

        # Obtener propiedades del video
        video_fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / video_fps if video_fps > 0 else 0

        # Calcular intervalo de frames
        frame_interval = max(1, int(video_fps / self.target_fps))

        # Configurar tiempo de inicio
        if start_time:
            cap.set(cv2.CAP_PROP_POS_MSEC, start_time * 1000)

        frames = []
        frame_count = 0
        extracted_count = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Verificar tiempo de fin
            if end_time:
                current_time = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000
                if current_time > end_time:
                    break

            # Extraer frame según intervalo
            if frame_count % frame_interval == 0:
                if max_frames and extracted_count >= max_frames:
                    break

                # Guardar frame
                frame_filename = f"frame_{extracted_count:06d}.png"
                frame_path = self.output_dir / frame_filename
                cv2.imwrite(str(frame_path), frame)
                frames.append(str(frame_path))
                extracted_count += 1

            frame_count += 1

        cap.release()

        extraction_time = (time.time() - start) * 1000

        return FrameExtractionResult(
            frames=frames,
            total_frames=extracted_count,
            fps_used=self.target_fps,
            duration_seconds=duration,
            extraction_time_ms=extraction_time
        )

    async def extract_frames_async(
        self,
        video_path: str,
        max_frames: Optional[int] = None
    ) -> FrameExtractionResult:
        """Versión asíncrona de extracción de frames."""
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            return await loop.run_in_executor(
                executor,
                self.extract_frames_from_video,
                video_path,
                max_frames
            )


class LidarFrameExtractor:
    """Extractor de datos LiDAR desde capturas de iPhone Pro."""

    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def extract_lidar_data(
        self,
        lidar_file: str,
        format: str = "ply"
    ) -> dict:
        """
        Extrae y procesa datos LiDAR.

        Args:
            lidar_file: Ruta al archivo LiDAR (.usdz, .obj, .ply)
            format: Formato de salida

        Returns:
            Diccionario con información del LiDAR
        """
        # Esto se integrará con ARKit/ARCore para procesar datos LiDAR
        # Por ahora, placeholder
        return {
            "point_cloud_path": lidar_file,
            "num_points": 0,
            "bounds": None,
            "format": format
        }


def get_video_metadata(video_path: str) -> dict:
    """Obtiene metadatos de un archivo de video."""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"No se pudo abrir el video: {video_path}")

    metadata = {
        "fps": cap.get(cv2.CAP_PROP_FPS),
        "total_frames": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
        "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
        "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        "duration_seconds": 0,
        "codec": int(cap.get(cv2.CAP_PROP_FOURCC)),
    }
    metadata["duration_seconds"] = (
        metadata["total_frames"] / metadata["fps"]
        if metadata["fps"] > 0 else 0
    )

    cap.release()
    return metadata
