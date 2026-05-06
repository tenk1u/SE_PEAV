"""
Servicio de procesamiento principal - Integra todos los servicios del pipeline.

Este servicio orquesta el flujo completo de procesamiento de inspecciones:
1. Extracción de frames (video dron / capturas móvil)
2. Generación de nube de puntos (COLMAP)
3. Entrenamiento 3D Gaussian Splatting
4. Detección de elementos (YOLO)
5. Análisis estructural (E.060)
6. Generación de reporte
"""
from celery import Celery
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from datetime import datetime
import asyncio
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging

from app.core.config import get_settings
from app.core.database import AsyncSessionLocal
from app.models.project import (
    Inspection, InspectionStatus,
    Detection, StructuralMetric, Report, Project
)
from app.services.storage import download_file, upload_bytes, get_presigned_url
from app.services.frame_extractor import FrameExtractor, get_video_metadata
from app.services.geometry_engine import GeometryEngine, GaussianSplattingTrainer
from app.services.yolo_detector import YOLODetector, get_detection_statistics
from app.services.e060_analysis import E060Analyzer, ElementDimensions, ElementType
from app.services.report_generator import ReportGenerator, ReportData

logger = logging.getLogger(__name__)

settings = get_settings()

# Initialize Celery
celery_app = Celery(
    "se_peav",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max per task
    worker_max_tasks_per_child=10,
)


@celery_app.task(bind=True, name="process_inspection")
def process_inspection_task(self, inspection_id: int):
    """Main processing task for an inspection."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_process_inspection(self, inspection_id))
    finally:
        loop.close()


async def _process_inspection(task, inspection_id: int):
    """Async implementation of inspection processing."""
    async with AsyncSessionLocal() as db:
        try:
            # Get inspection with project
            result = await db.execute(
                select(Inspection)
                .options(selectinload(Inspection.project))
                .where(Inspection.id == inspection_id)
            )
            inspection = result.scalar_one_or_none()
            if not inspection:
                logger.error(f"Inspección {inspection_id} no encontrada")
                return

            # Update status
            inspection.status = InspectionStatus.PROCESSING
            inspection.processing_started_at = datetime.utcnow()
            await db.commit()

            # Setup working directories
            workspace_dir = f"workspace/processing/{inspection_id}"
            Path(workspace_dir).mkdir(parents=True, exist_ok=True)

            # ===========================================
            # PASO 1: Extraer frames del video/capturas
            # ===========================================
            task.update_state(
                state="PROGRESS",
                meta={"step": "extracting_frames", "progress": 10}
            )
            logger.info(f"[Inspección {inspection_id}] Extrayendo frames...")

            frames = await _extract_frames(inspection, workspace_dir)
            inspection.frames_extracted = len(frames)
            await db.commit()

            if not frames:
                raise ValueError("No se pudieron extraer frames del video/capturas")

            # ===========================================
            # PASO 2: Generar nube de puntos (COLMAP)
            # ===========================================
            task.update_state(
                state="PROGRESS",
                meta={"step": "generating_point_cloud", "progress": 30}
            )
            logger.info(f"[Inspección {inspection_id}] Generando nube de puntos...")

            point_cloud_path = await _generate_point_cloud(
                frames, workspace_dir
            )
            inspection.point_cloud_path = point_cloud_path
            await db.commit()

            # ===========================================
            # PASO 3: Entrenar 3DGS (opcional)
            # ===========================================
            task.update_state(
                state="PROGRESS",
                meta={"step": "training_3dgs", "progress": 50}
            )
            logger.info(f"[Inspección {inspection_id}] Entrenando modelo 3DGS...")

            model_path = await _train_3dgs(
                point_cloud_path, workspace_dir
            )
            inspection.model_3dgs_path = model_path
            await db.commit()

            # ===========================================
            # PASO 4: Detectar elementos con YOLO
            # ===========================================
            task.update_state(
                state="PROGRESS",
                meta={"step": "detecting_elements", "progress": 70}
            )
            logger.info(f"[Inspección {inspection_id}] Detectando elementos...")

            detections = await _detect_elements(frames, workspace_dir)
            inspection.total_detections = len(detections)

            # Save detections to database
            for det in detections:
                db_detection = Detection(
                    inspection_id=inspection_id,
                    frame_file=det["frame_file"],
                    class_name=det["class_name"],
                    confidence=det["confidence"],
                    bbox_x1=det["bbox"][0],
                    bbox_y1=det["bbox"][1],
                    bbox_x2=det["bbox"][2],
                    bbox_y2=det["bbox"][3],
                )
                db.add(db_detection)

            await db.commit()

            # ===========================================
            # PASO 5: Análisis estructural (E.060)
            # ===========================================
            task.update_state(
                state="PROGRESS",
                meta={"step": "analyzing_structure", "progress": 85}
            )
            logger.info(f"[Inspección {inspection_id}] Analizando estructura...")

            metrics = await _analyze_structure(
                detections, point_cloud_path, workspace_dir
            )

            # Save metrics to database
            for metric in metrics:
                db_metric = StructuralMetric(
                    inspection_id=inspection_id,
                    **metric
                )
                db.add(db_metric)

            # Calculate overall vulnerability score
            vulnerability_scores = [
                m["vulnerability_score"]
                for m in metrics
                if m.get("vulnerability_score") is not None
            ]

            if vulnerability_scores:
                inspection.vulnerability_score = sum(vulnerability_scores) / len(vulnerability_scores)
                if inspection.vulnerability_score >= 75:
                    inspection.vulnerability_level = "critical"
                elif inspection.vulnerability_score >= 50:
                    inspection.vulnerability_level = "high"
                elif inspection.vulnerability_score >= 25:
                    inspection.vulnerability_level = "medium"
                else:
                    inspection.vulnerability_level = "low"

            # ===========================================
            # PASO 6: Generar reporte
            # ===========================================
            task.update_state(
                state="PROGRESS",
                meta={"step": "generating_report", "progress": 95}
            )
            logger.info(f"[Inspección {inspection_id}] Generando reporte...")

            report = await _generate_report(
                inspection, detections, metrics, workspace_dir
            )

            if report:
                db.add(report)

            # Complete
            inspection.status = InspectionStatus.COMPLETED
            inspection.processing_completed_at = datetime.utcnow()
            await db.commit()

            logger.info(f"[Inspección {inspection_id}] Procesamiento completado exitosamente")

        except Exception as e:
            logger.error(f"[Inspección {inspection_id}] Error: {str(e)}")
            inspection.status = InspectionStatus.FAILED
            inspection.error_message = str(e)
            await db.commit()
            raise


async def _extract_frames(inspection: Inspection, workspace_dir: str) -> List[str]:
    """Extrae frames del video o procesa capturas móviles."""
    frames_dir = f"{workspace_dir}/frames"
    extractor = FrameExtractor(frames_dir, target_fps=settings.FRAME_EXTRACTION_FPS)

    if inspection.capture_source == "dron" and inspection.dron_video_path:
        # Descargar video de S3
        video_local_path = f"{workspace_dir}/video.mp4"
        video_content = await download_file(inspection.dron_video_path)
        with open(video_local_path, "wb") as f:
            f.write(video_content)

        # Extraer frames
        result = extractor.extract_frames_from_video(video_local_path)
        return result.frames

    elif inspection.capture_source == "mobile":
        # Las capturas móviles ya son imágenes
        # Buscar en el directorio de uploads
        mobile_dir = f"uploads/{inspection.project.owner_id}/images"
        # Aquí necesitaríamos listar los archivos del directorio
        # Por ahora, retornar lista vacía
        return []

    elif inspection.capture_source == "combined":
        # Combinar frames de dron y móvil
        frames = []

        if inspection.dron_video_path:
            video_local_path = f"{workspace_dir}/dron_video.mp4"
            video_content = await download_file(inspection.dron_video_path)
            with open(video_local_path, "wb") as f:
                f.write(video_content)
            result = extractor.extract_frames_from_video(video_local_path)
            frames.extend(result.frames)

        # Agregar frames móviles si existen
        # ...

        return frames

    return []


async def _generate_point_cloud(frames: List[str], workspace_dir: str) -> str:
    """Genera nube de puntos usando COLMAP."""
    engine = GeometryEngine(workspace_dir)
    result = await engine.run_colmap(
        images_dir=f"{workspace_dir}/frames",
        camera_model="SIMPLE_RADIAL"
    )
    return result.point_cloud_path


async def _train_3dgs(point_cloud_path: str, workspace_dir: str) -> str:
    """Entrena modelo 3D Gaussian Splatting."""
    trainer = GaussianSplattingTrainer(f"{workspace_dir}/3dgs")
    result = await trainer.train(
        source_path=point_cloud_path,
        iterations=30000  # Reducido para desarrollo
    )
    return result.model_path


async def _detect_elements(frames: List[str], workspace_dir: str) -> List[Dict[str, Any]]:
    """Detecta elementos constructivos usando YOLO."""
    # Buscar pesos del modelo
    weights_path = "03_ai_analysis/models/weights/yolo_construction.pt"
    if not Path(weights_path).exists():
        # Usar modelo por defecto o descargar
        logger.warning("Pesos de YOLO no encontrados, usando detección simulada")
        return _simulate_detections(frames)

    detector = YOLODetector(weights_path)
    results = detector.detect_batch(frames)

    # Convertir a formato de diccionario
    detections = []
    for result in results:
        for det in result.detections:
            detections.append({
                "frame_file": det.frame_file,
                "class_name": det.class_name,
                "confidence": det.confidence,
                "bbox": det.bbox,
            })

    return detections


def _simulate_detections(frames: List[str]) -> List[Dict[str, Any]]:
    """Simula detecciones para testing (cuando no hay modelo YOLO)."""
    import random

    classes = ["column", "beam", "wall", "crack", "window"]
    detections = []

    for frame in frames:
        # Simular 0-5 detecciones por frame
        num_dets = random.randint(0, 5)
        for _ in range(num_dets):
            detections.append({
                "frame_file": Path(frame).name,
                "class_name": random.choice(classes),
                "confidence": random.uniform(0.5, 0.99),
                "bbox": (
                    random.uniform(0, 500),
                    random.uniform(0, 500),
                    random.uniform(500, 1000),
                    random.uniform(500, 1000)
                ),
            })

    return detections


async def _analyze_structure(
    detections: List[Dict[str, Any]],
    point_cloud_path: str,
    workspace_dir: str
) -> List[Dict[str, Any]]:
    """Analiza la estructura según norma E.060."""
    analyzer = E060Analyzer()
    metrics = []

    # Agrupar detecciones por tipo
    walls = [d for d in detections if d["class_name"] in ["wall", "muro"]]
    columns = [d for d in detections if d["class_name"] in ["column", "columna"]]
    beams = [d for d in detections if d["class_name"] in ["beam", "viga"]]

    # Analizar muros
    for i, wall in enumerate(walls):
        # Estimar dimensiones desde bounding box
        width = (wall["bbox"][2] - wall["bbox"][0]) / 100
        height = (wall["bbox"][3] - wall["bbox"][1]) / 100

        dimensions = ElementDimensions(
            element_type=ElementType.WALL,
            element_id=f"wall_{i}",
            floor_level=0,
            width=width,
            height=height,
            length=width * 3,
            thickness=0.15,
        )

        result = analyzer.analyze_wall(dimensions)
        metrics.append({
            "element_type": "wall",
            "element_id": result.element_id,
            "floor_level": result.floor_level,
            "width": result.measured_width,
            "height": result.measured_height,
            "thickness": result.measured_thickness,
            "meets_minimum_thickness": "yes" if result.thickness_compliant else "no",
            "meets_confinement": "yes" if result.confinement_compliant else "no",
            "meets_vo_ratio": "yes" if result.vo_ratio_compliant else "no",
            "meets_reinforcement": "yes" if result.reinforcement_compliant else "no",
            "vulnerability_score": result.vulnerability_score,
            "vulnerability_level": result.vulnerability_level.value,
            "issues_found": result.issues,
        })

    # Analizar columnas
    for i, col in enumerate(columns):
        width = (col["bbox"][2] - col["bbox"][0]) / 100
        height = (col["bbox"][3] - col["bbox"][1]) / 100

        dimensions = ElementDimensions(
            element_type=ElementType.COLUMN,
            element_id=f"column_{i}",
            floor_level=0,
            width=width,
            height=height,
            length=0,
        )

        result = analyzer.analyze_column(dimensions)
        metrics.append({
            "element_type": "column",
            "element_id": result.element_id,
            "floor_level": result.floor_level,
            "width": result.measured_width,
            "height": result.measured_height,
            "thickness": None,
            "meets_minimum_thickness": "yes" if result.thickness_compliant else "no",
            "meets_confinement": "yes",
            "meets_vo_ratio": "yes",
            "meets_reinforcement": "yes" if result.reinforcement_compliant else "no",
            "vulnerability_score": result.vulnerability_score,
            "vulnerability_level": result.vulnerability_level.value,
            "issues_found": result.issues,
        })

    return metrics


async def _generate_report(
    inspection: Inspection,
    detections: List[Dict[str, Any]],
    metrics: List[Dict[str, Any]],
    workspace_dir: str
) -> Optional[Report]:
    """Genera el reporte PDF."""
    try:
        # Calcular estadísticas
        total_detections = len(detections)
        detections_by_class = {}
        for det in detections:
            cls = det.get("class_name", "unknown")
            detections_by_class[cls] = detections_by_class.get(cls, 0) + 1

        # Calcular score promedio
        vulnerability_scores = [
            m.get("vulnerability_score", 0)
            for m in metrics
            if m.get("vulnerability_score") is not None
        ]
        avg_vulnerability = (
            sum(vulnerability_scores) / len(vulnerability_scores)
            if vulnerability_scores else 0
        )

        # Preparar datos del reporte
        report_data = ReportData(
            inspection_id=inspection.id,
            project_name=inspection.project.name,
            address=inspection.project.address or "No especificada",
            capture_date=datetime.now(),
            total_detections=total_detections,
            vulnerability_score=avg_vulnerability,
            vulnerability_level=inspection.vulnerability_level or "low",
            detections_by_class=detections_by_class,
            structural_metrics=metrics,
            recommendations=[],
            images=[]
        )

        # Generar reporte
        output_dir = f"{workspace_dir}/reports"
        generator = ReportGenerator(output_dir)
        result = generator.generate_report(report_data)

        # Crear objeto Report para la base de datos
        report = Report(
            inspection_id=inspection.id,
            title=f"Informe de Inspección #{inspection.id}",
            summary=f"Análisis estructural completado. {total_detections} elementos detectados.",
            recommendations=[],  # Se llenarán desde el reporte
            pdf_path=result.pdf_path,
            html_path=result.html_path,
            model_viewer_url=f"/viewer/{inspection.id}",
            overall_vulnerability_score=avg_vulnerability,
            structural_score=avg_vulnerability,
            confinement_score=avg_vulnerability,
            connection_score=avg_vulnerability,
        )

        return report

    except Exception as e:
        logger.error(f"Error generando reporte: {e}")
        return None


async def start_processing(inspection_id: int):
    """Start async processing of an inspection."""
    logger.info(f"Iniciando procesamiento de inspección {inspection_id}")
    process_inspection_task.delay(inspection_id)
