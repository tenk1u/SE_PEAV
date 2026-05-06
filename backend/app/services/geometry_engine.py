"""
Servicio de geometría - Adaptado de 02_geometry_engine.

Este servicio maneja la reconstrucción 3D usando COLMAP y 3D Gaussian Splatting.
"""
import subprocess
import asyncio
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import logging
import json

logger = logging.getLogger(__name__)


@dataclass
class PointCloudResult:
    """Resultado de la generación de nube de puntos."""
    point_cloud_path: str
    num_points: int
    bounds: Dict[str, float]  # min_x, max_x, min_y, max_y, min_z, max_z
    processing_time_ms: float
    colmap_success: bool


@dataclass
class GaussianSplattingResult:
    """Resultado del entrenamiento de 3D Gaussian Splatting."""
    model_path: str
    num_gaussians: int
    training_iterations: int
    loss: float
    psnr: float
    training_time_ms: float


class GeometryEngine:
    """Motor de geometría para reconstrucción 3D."""

    def __init__(self, workspace_dir: str):
        """
        Args:
            workspace_dir: Directorio de trabajo para COLMAP y 3DGS
        """
        self.workspace_dir = Path(workspace_dir)
        self.workspace_dir.mkdir(parents=True, exist_ok=True)

        # Subdirectorios
        self.colmap_dir = self.workspace_dir / "colmap"
        self.colmap_dir.mkdir(exist_ok=True)

        self.output_dir = self.workspace_dir / "output"
        self.output_dir.mkdir(exist_ok=True)

    async def run_colmap(
        self,
        images_dir: str,
        camera_model: str = "SIMPLE_RADIAL",
        gpu_index: int = 0
    ) -> PointCloudResult:
        """
        Ejecuta COLMAP para Structure from Motion.

        Args:
            images_dir: Directorio con las imágenes
            camera_model: Modelo de cámara (SIMPLE_RADIAL, OPENCV, etc.)
            gpu_index: Índice de GPU a usar

        Returns:
            PointCloudResult con la nube de puntos generada
        """
        import time
        start = time.time()

        images_path = Path(images_dir)
        if not images_path.exists():
            raise ValueError(f"Directorio de imágenes no existe: {images_dir}")

        # Configurar directorios COLMAP
        database_path = self.colmap_dir / "database.db"
        sparse_dir = self.colmap_dir / "sparse"
        sparse_dir.mkdir(exist_ok=True)

        # Paso 1: Feature Extraction
        logger.info("Ejecutando COLMAP Feature Extraction...")
        feature_cmd = [
            "colmap", "feature_extractor",
            "--database_path", str(database_path),
            "--image_path", str(images_path),
            "--ImageReader.camera_model", camera_model,
            "--SiftExtraction.use_gpu", "1",
            "--SiftExtraction.gpu_index", str(gpu_index),
        ]

        try:
            subprocess.run(feature_cmd, check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"Error en Feature Extraction: {e.stderr}")
            raise

        # Paso 2: Feature Matching
        logger.info("Ejecutando COLMAP Feature Matching...")
        matching_cmd = [
            "colmap", "exhaustive_matcher",
            "--database_path", str(database_path),
            "--SiftMatching.use_gpu", "1",
            "--SiftMatching.gpu_index", str(gpu_index),
        ]

        try:
            subprocess.run(matching_cmd, check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"Error en Feature Matching: {e.stderr}")
            raise

        # Paso 3: Sparse Reconstruction
        logger.info("Ejecutando COLMAP Mapper...")
        mapper_cmd = [
            "colmap", "mapper",
            "--database_path", str(database_path),
            "--image_path", str(images_path),
            "--output_path", str(sparse_dir),
        ]

        try:
            subprocess.run(mapper_cmd, check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"Error en Mapper: {e.stderr}")
            raise

        # Paso 4: Convertir a nube de puntos densa
        logger.info("Generando nube de puntos densa...")
        dense_dir = self.colmap_dir / "dense"
        dense_dir.mkdir(exist_ok=True)

        # Undistortion
        undistort_cmd = [
            "colmap", "image_undistorter",
            "--image_path", str(images_path),
            "--input_path", str(sparse_dir / "0"),
            "--output_path", str(dense_dir),
            "--output_type", "COLMAP",
        ]

        try:
            subprocess.run(undistort_cmd, check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"Error en Undistortion: {e.stderr}")
            raise

        # Dense stereo
        stereo_cmd = [
            "colmap", "patch_match_stereo",
            "--workspace_path", str(dense_dir),
            "--PatchMatchStereo.geom_consistency", "true",
        ]

        try:
            subprocess.run(stereo_cmd, check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"Error en Patch Match Stereo: {e.stderr}")
            raise

        # Fusion
        fusion_cmd = [
            "colmap", "stereo_fusion",
            "--workspace_path", str(dense_dir),
            "--output_path", str(dense_dir / "fused.ply"),
        ]

        try:
            subprocess.run(fusion_cmd, check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"Error en Stereo Fusion: {e.stderr}")
            raise

        # Mover resultado final
        final_ply = self.output_dir / "point_cloud.ply"
        if (dense_dir / "fused.ply").exists():
            import shutil
            shutil.copy(dense_dir / "fused.ply", final_ply)

        processing_time = (time.time() - start) * 1000

        # Obtener información de la nube de puntos
        num_points = self._count_ply_points(str(final_ply))
        bounds = self._get_ply_bounds(str(final_ply))

        return PointCloudResult(
            point_cloud_path=str(final_ply),
            num_points=num_points,
            bounds=bounds,
            processing_time_ms=processing_time,
            colmap_success=True
        )

    def _count_ply_points(self, ply_path: str) -> int:
        """Cuenta el número de puntos en un archivo PLY."""
        try:
            with open(ply_path, 'rb') as f:
                # Leer header para encontrar num_points
                for line in f:
                    line = line.decode('utf-8', errors='ignore')
                    if line.startswith('element vertex'):
                        return int(line.split()[-1])
        except Exception:
            return 0
        return 0

    def _get_ply_bounds(self, ply_path: str) -> Dict[str, float]:
        """Obtiene los bounds de una nube de puntos PLY."""
        # Esto requeriría parsear el archivo PLY completo
        # Por ahora, retornar bounds por defecto
        return {
            "min_x": 0, "max_x": 0,
            "min_y": 0, "max_y": 0,
            "min_z": 0, "max_z": 0
        }


class GaussianSplattingTrainer:
    """Entrenador de 3D Gaussian Splatting."""

    def __init__(self, model_dir: str):
        """
        Args:
            model_dir: Directorio para guardar el modelo entrenado
        """
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)

    async def train(
        self,
        source_path: str,
        iterations: int = 30000,
        resolution: int = 1,
        gpu_index: int = 0
    ) -> GaussianSplattingResult:
        """
        Entrena un modelo de 3D Gaussian Splatting.

        Args:
            source_path: Ruta a los datos de entrada (formato COLMAP)
            iterations: Número de iteraciones de entrenamiento
            resolution: Resolución de las imágenes (1 = original)
            gpu_index: Índice de GPU

        Returns:
            GaussianSplattingResult con el modelo entrenado
        """
        import time
        start = time.time()

        # Verificar que existe el código de 3DGS
        # Esto asume que tienes el código de 3DGS en el directorio
        train_script = Path("/app/3dgs/train.py")  # En Docker
        if not train_script.exists():
            # Intentar ruta local
            train_script = Path("02_geometry_engine/train_3dgs.py")
            if not train_script.exists():
                raise FileNotFoundError("No se encontró el script de entrenamiento 3DGS")

        # Ejecutar entrenamiento
        cmd = [
            "python", str(train_script),
            "--source_path", source_path,
            "--model_path", str(self.model_dir),
            "--iterations", str(iterations),
            "--resolution", str(resolution),
        ]

        logger.info(f"Iniciando entrenamiento 3DGS con {iterations} iteraciones...")

        try:
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True
            )
            logger.info("Entrenamiento 3DGS completado")
        except subprocess.CalledProcessError as e:
            logger.error(f"Error en entrenamiento 3DGS: {e.stderr}")
            raise

        training_time = (time.time() - start) * 1000

        # Buscar el modelo entrenado
        model_files = list(self.model_dir.glob("**/*.ply"))
        if not model_files:
            raise FileNotFoundError("No se encontró el modelo entrenado")

        # Extraer métricas del log (simplificado)
        # En producción, parsear el log real
        num_gaussians = self._count_gaussians(model_files[0])

        return GaussianSplattingResult(
            model_path=str(model_files[0]),
            num_gaussians=num_gaussians,
            training_iterations=iterations,
            loss=0.0,  # Extraer del log
            psnr=0.0,  # Extraer del log
            training_time_ms=training_time
        )

    def _count_gaussians(self, model_path: Path) -> int:
        """Cuenta el número de gaussianas en el modelo."""
        try:
            with open(model_path, 'rb') as f:
                for line in f:
                    line = line.decode('utf-8', errors='ignore')
                    if line.startswith('element vertex'):
                        return int(line.split()[-1])
        except Exception:
            return 0
        return 0


async def run_geometry_pipeline(
    images_dir: str,
    workspace_dir: str,
    train_3dgs: bool = True,
    iterations: int = 30000
) -> Dict[str, Any]:
    """
    Ejecuta el pipeline completo de geometría.

    Args:
        images_dir: Directorio con imágenes
        workspace_dir: Directorio de trabajo
        train_3dgs: Si entrenar 3DGS después de COLMAP
        iterations: Iteraciones para 3DGS

    Returns:
        Diccionario con resultados del pipeline
    """
    engine = GeometryEngine(workspace_dir)

    # Ejecutar COLMAP
    logger.info("Iniciando pipeline COLMAP...")
    colmap_result = await engine.run_colmap(images_dir)

    result = {
        "colmap": {
            "point_cloud": colmap_result.point_cloud_path,
            "num_points": colmap_result.num_points,
            "bounds": colmap_result.bounds,
            "processing_time_ms": colmap_result.processing_time_ms
        }
    }

    # Entrenar 3DGS si se solicita
    if train_3dgs and colmap_result.colmap_success:
        logger.info("Iniciando entrenamiento 3DGS...")
        trainer = GaussianSplattingTrainer(workspace_dir + "/3dgs")
        gs_result = await trainer.train(
            source_path=colmap_result.point_cloud_path,
            iterations=iterations
        )
        result["gaussian_splatting"] = {
            "model_path": gs_result.model_path,
            "num_gaussians": gs_result.num_gaussians,
            "training_time_ms": gs_result.training_time_ms
        }

    return result
