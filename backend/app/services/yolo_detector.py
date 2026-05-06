"""
Servicio de detección YOLO - Adaptado de 03_ai_analysis.

Este servicio maneja la detección de elementos constructivos usando YOLO.
"""
import asyncio
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class Detection:
    """Resultado de una detección individual."""
    class_name: str
    confidence: float
    bbox: tuple  # (x1, y1, x2, y2)
    frame_file: str
    position_3d: Optional[tuple] = None  # (x, y, z) si disponible


@dataclass
class DetectionResult:
    """Resultado de la detección en un frame."""
    detections: List[Detection]
    total_detections: int
    classes_found: List[str]
    processing_time_ms: float


class YOLODetector:
    """Detector de elementos constructivos usando YOLO."""

    # Clases de elementos constructivos
    CONSTRUCTION_CLASSES = {
        0: "column",
        1: "beam",
        2: "wall",
        3: "slab",
        4: "crack",
        5: "rebar",
        6: "window",
        7: "door",
        8: "stairs",
        9: "foundation",
    }

    def __init__(
        self,
        weights_path: str,
        confidence_threshold: float = 0.25,
        iou_threshold: float = 0.45,
        device: str = "auto"
    ):
        """
        Args:
            weights_path: Ruta a los pesos del modelo YOLO
            confidence_threshold: Umbral de confianza para detecciones
            iou_threshold: Umbral de IoU para NMS
            device: Dispositivo (cpu, cuda, auto)
        """
        self.weights_path = Path(weights_path)
        self.confidence_threshold = confidence_threshold
        self.iou_threshold = iou_threshold
        self.device = device
        self.model = None

    def _load_model(self):
        """Carga el modelo YOLO."""
        if self.model is not None:
            return

        try:
            from ultralytics import YOLO
            logger.info(f"Cargando modelo YOLO desde {self.weights_path}")
            self.model = YOLO(str(self.weights_path))
            logger.info("Modelo YOLO cargado exitosamente")
        except ImportError:
            logger.error("ultralytics no está instalado. Instalar con: pip install ultralytics")
            raise
        except Exception as e:
            logger.error(f"Error cargando modelo YOLO: {e}")
            raise

    def detect_frame(
        self,
        frame_path: str,
        classes: Optional[List[int]] = None
    ) -> DetectionResult:
        """
        Detecta elementos en un frame individual.

        Args:
            frame_path: Ruta al archivo de imagen
            classes: Lista de clases a detectar (None = todas)

        Returns:
            DetectionResult con las detecciones
        """
        import time
        start = time.time()

        self._load_model()

        # Ejecutar detección
        results = self.model(
            frame_path,
            conf=self.confidence_threshold,
            iou=self.iou_threshold,
            classes=classes,
            verbose=False
        )

        detections = []
        for result in results:
            if result.boxes is None:
                continue

            for box in result.boxes:
                cls_id = int(box.cls[0])
                class_name = self.CONSTRUCTION_CLASSES.get(cls_id, f"class_{cls_id}")
                confidence = float(box.conf[0])
                x1, y1, x2, y2 = box.xyxy[0].tolist()

                detections.append(Detection(
                    class_name=class_name,
                    confidence=confidence,
                    bbox=(x1, y1, x2, y2),
                    frame_file=Path(frame_path).name
                ))

        processing_time = (time.time() - start) * 1000

        # Obtener clases únicas encontradas
        classes_found = list(set(d.class_name for d in detections))

        return DetectionResult(
            detections=detections,
            total_detections=len(detections),
            classes_found=classes_found,
            processing_time_ms=processing_time
        )

    async def detect_frame_async(
        self,
        frame_path: str,
        classes: Optional[List[int]] = None
    ) -> DetectionResult:
        """Versión asíncrona de detección en frame."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.detect_frame,
            frame_path,
            classes
        )

    def detect_batch(
        self,
        frame_paths: List[str],
        classes: Optional[List[int]] = None,
        batch_size: int = 8
    ) -> List[DetectionResult]:
        """
        Detecta elementos en múltiples frames.

        Args:
            frame_paths: Lista de rutas a frames
            classes: Clases a detectar
            batch_size: Tamaño del batch

        Returns:
            Lista de DetectionResult
        """
        self._load_model()

        results = []
        for i in range(0, len(frame_paths), batch_size):
            batch = frame_paths[i:i + batch_size]

            # Ejecutar detección en batch
            batch_results = self.model(
                batch,
                conf=self.confidence_threshold,
                iou=self.iou_threshold,
                classes=classes,
                verbose=False
            )

            for j, result in enumerate(batch_results):
                detections = []
                if result.boxes is not None:
                    for box in result.boxes:
                        cls_id = int(box.cls[0])
                        class_name = self.CONSTRUCTION_CLASSES.get(cls_id, f"class_{cls_id}")
                        confidence = float(box.conf[0])
                        x1, y1, x2, y2 = box.xyxy[0].tolist()

                        detections.append(Detection(
                            class_name=class_name,
                            confidence=confidence,
                            bbox=(x1, y1, x2, y2),
                            frame_file=Path(batch[j]).name
                        ))

                classes_found = list(set(d.class_name for d in detections))

                results.append(DetectionResult(
                    detections=detections,
                    total_detections=len(detections),
                    classes_found=classes_found,
                    processing_time_ms=0  # No medimos por frame individual en batch
                ))

        return results

    def detect_frames_directory(
        self,
        frames_dir: str,
        classes: Optional[List[int]] = None,
        extensions: List[str] = [".png", ".jpg", ".jpeg"]
    ) -> List[DetectionResult]:
        """
        Detecta elementos en todos los frames de un directorio.

        Args:
            frames_dir: Directorio con frames
            classes: Clases a detectar
            extensions: Extensiones de archivo a procesar

        Returns:
            Lista de DetectionResult
        """
        frames_path = Path(frames_dir)
        if not frames_path.exists():
            raise ValueError(f"Directorio no existe: {frames_dir}")

        # Buscar frames
        frame_files = []
        for ext in extensions:
            frame_files.extend(frames_path.glob(f"*{ext}"))
            frame_files.extend(frames_path.glob(f"*{ext.upper()}"))

        frame_files = sorted(set(frame_files))

        if not frame_files:
            logger.warning(f"No se encontraron frames en {frames_dir}")
            return []

        logger.info(f"Detectando elementos en {len(frame_files)} frames...")

        return self.detect_batch(
            [str(f) for f in frame_files],
            classes=classes
        )


def get_detection_statistics(detections: List[DetectionResult]) -> Dict[str, Any]:
    """
    Calcula estadísticas de las detecciones.

    Args:
        detections: Lista de resultados de detección

    Returns:
        Diccionario con estadísticas
    """
    total_detections = sum(d.total_detections for d in detections)
    all_classes = []
    for d in detections:
        all_classes.extend([det.class_name for det in d.detections])

    # Contar por clase
    class_counts = {}
    for cls in all_classes:
        class_counts[cls] = class_counts.get(cls, 0) + 1

    # Calcular confianza promedio
    all_confidences = []
    for d in detections:
        all_confidences.extend([det.confidence for det in d.detections])

    avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0

    return {
        "total_frames_processed": len(detections),
        "total_detections": total_detections,
        "detections_per_frame": total_detections / len(detections) if detections else 0,
        "unique_classes": len(class_counts),
        "class_distribution": class_counts,
        "average_confidence": avg_confidence,
        "frames_with_detections": sum(1 for d in detections if d.total_detections > 0),
    }
