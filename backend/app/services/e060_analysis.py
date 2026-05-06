"""
Análisis estructural según Norma E.060 (Perú)
Reglamento Nacional de Edificaciones - Albañilería

Este módulo implementa las verificaciones de predimensionamiento para
viviendas de albañilería, incluyendo:
- Espesores mínimos de muros
- Confinamiento de muros
- Relación vano/muro
- Refuerzo horizontal y vertical
"""
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum
import math


class ElementType(str, Enum):
    WALL = "wall"
    COLUMN = "column"
    BEAM = "beam"
    SLAB = "slab"


class VulnerabilityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class E060Config:
    """Configuración de la norma E.060"""
    # Espesores mínimos de muros (cm)
    MIN_WALL_THICKNESS_1FLOOR = 15  # 1 piso
    MIN_WALL_THICKNESS_2FLOORS = 20  # 2 pisos
    MIN_WALL_THICKNESS_3FLOORS = 25  # 3+ pisos

    # Confinamiento
    MAX_CONFINEMENT_SPACING = 4.0  # metros - máximo entre confinamientos
    MIN_CONFINEMENT_WIDTH = 20  # cm - ancho mínimo de confinamiento
    MIN_CONFINEMENT_DEPTH = 20  # cm - profundidad mínima

    # Relación vano/muro
    MAX_VO_RATIO = 0.6  # relación máximo vano/longitud de muro

    # Refuerzo
    MIN_REINFORCEMENT_RATIO = 0.0025  # 0.25% del área bruta
    MAX_REINFORCEMENT_SPACING_H = 20  # cm - horizontal
    MAX_REINFORCEMENT_SPACING_V = 40  # cm - vertical

    # Niveles
    MAX_FLOOR_LEVELNESS = 0.01  # 1cm/m desviación máxima


@dataclass
class ElementDimensions:
    """Dimensiones medidas de un elemento estructural"""
    element_type: ElementType
    element_id: str
    floor_level: int
    width: float  # metros
    height: float  # metros
    length: float  # metros
    thickness: Optional[float] = None  # metros (para muros)
    position_x: float = 0
    position_y: float = 0
    position_z: float = 0


@dataclass
class E060AnalysisResult:
    """Resultado del análisis E.060"""
    element_type: ElementType
    element_id: str
    floor_level: int

    # Dimensiones medidas
    measured_width: float
    measured_height: float
    measured_thickness: Optional[float]

    # Requisitos E.060
    required_thickness: float
    required_confinement_spacing: float
    required_vo_ratio: float

    # Cumplimiento
    thickness_compliant: bool
    confinement_compliant: bool
    vo_ratio_compliant: bool
    reinforcement_compliant: bool

    # Vulnerabilidad
    vulnerability_score: float  # 0-100
    vulnerability_level: VulnerabilityLevel
    issues: List[str]
    recommendations: List[str]


class E060Analyzer:
    """Analizador de estructuras según norma E.060"""

    def __init__(self, config: Optional[E060Config] = None):
        self.config = config or E060Config()

    def get_required_thickness(self, floor_level: int) -> float:
        """Retorna el espesor mínimo requerido según el número de pisos"""
        if floor_level <= 1:
            return self.config.MIN_WALL_THICKNESS_1FLOOR / 100  # convertir a metros
        elif floor_level == 2:
            return self.config.MIN_WALL_THICKNESS_2FLOORS / 100
        else:
            return self.config.MIN_WALL_THICKNESS_3FLOORS / 100

    def check_thickness(self, measured_thickness: float, floor_level: int) -> tuple[bool, str]:
        """Verifica si el espesor cumple con E.060"""
        required = self.get_required_thickness(floor_level)
        if measured_thickness >= required:
            return True, f"Espesor {measured_thickness*100:.0f}cm >= {required*100:.0f}cm requerido"
        else:
            return False, f"Espesor {measured_thickness*100:.0f}cm < {required*100:.0f}cm requerido"

    def check_confinement(
        self,
        wall_length: float,
        nearest_confinement_distance: Optional[float]
    ) -> tuple[bool, str]:
        """Verifica el confinamiento del muro"""
        max_spacing = self.config.MAX_CONFINEMENT_SPACING

        if nearest_confinement_distance is None:
            return False, "No se detectó confinamiento en el muro"

        if nearest_confinement_distance <= max_spacing:
            return True, f"Distancia a confinamiento {nearest_confinement_distance:.1f}m <= {max_spacing:.1f}m máximo"
        else:
            return False, f"Distancia a confinamiento {nearest_confinement_distance:.1f}m > {max_spacing:.1f}m máximo"

    def check_vo_ratio(
        self,
        wall_length: float,
        opening_width: float
    ) -> tuple[bool, str]:
        """Verifica la relación vano/muro"""
        if wall_length == 0:
            return False, "Longitud de muro es cero"

        vo_ratio = opening_width / wall_length
        max_ratio = self.config.MAX_VO_RATIO

        if vo_ratio <= max_ratio:
            return True, f"Relación vano/muro {vo_ratio:.2f} <= {max_ratio:.2f} máximo"
        else:
            return False, f"Relación vano/muro {vo_ratio:.2f} > {max_ratio:.2f} máximo"

    def check_reinforcement(
        self,
        wall_area: float,
        reinforcement_area: Optional[float]
    ) -> tuple[bool, str]:
        """Verifica el refuerzo del muro"""
        if reinforcement_area is None:
            return False, "No se detectó refuerzo en el muro"

        min_ratio = self.config.MIN_REINFORCEMENT_RATIO
        actual_ratio = reinforcement_area / wall_area if wall_area > 0 else 0

        if actual_ratio >= min_ratio:
            return True, f"Ratio de refuerzo {actual_ratio:.4f} >= {min_ratio:.4f} mínimo"
        else:
            return False, f"Ratio de refuerzo {actual_ratio:.4f} < {min_ratio:.4f} mínimo"

    def calculate_vulnerability_score(
        self,
        thickness_compliant: bool,
        confinement_compliant: bool,
        vo_ratio_compliant: bool,
        reinforcement_compliant: bool
    ) -> tuple[float, VulnerabilityLevel]:
        """Calcula el score de vulnerabilidad (0-100)"""
        score = 0

        # Espesor (30% del score)
        if not thickness_compliant:
            score += 30

        # Confinamiento (30% del score)
        if not confinement_compliant:
            score += 30

        # Relación vano/muro (20% del score)
        if not vo_ratio_compliant:
            score += 20

        # Refuerzo (20% del score)
        if not reinforcement_compliant:
            score += 20

        # Determinar nivel
        if score >= 75:
            level = VulnerabilityLevel.CRITICAL
        elif score >= 50:
            level = VulnerabilityLevel.HIGH
        elif score >= 25:
            level = VulnerabilityLevel.MEDIUM
        else:
            level = VulnerabilityLevel.LOW

        return score, level

    def analyze_wall(
        self,
        dimensions: ElementDimensions,
        nearest_confinement_distance: Optional[float] = None,
        opening_width: float = 0,
        reinforcement_area: Optional[float] = None
    ) -> E060AnalysisResult:
        """Analiza un muro según E.060"""
        issues = []
        recommendations = []

        # Verificar espesor
        thickness_compliant = True
        if dimensions.thickness:
            thickness_compliant, msg = self.check_thickness(
                dimensions.thickness, dimensions.floor_level
            )
            if not thickness_compliant:
                issues.append(msg)
                recommendations.append(
                    f"Aumentar espesor del muro a mínimo {self.get_required_thickness(dimensions.floor_level)*100:.0f}cm"
                )

        # Verificar confinamiento
        confinement_compliant, msg = self.check_confinement(
            dimensions.length, nearest_confinement_distance
        )
        if not confinement_compliant:
            issues.append(msg)
            recommendations.append(
                f"Agregar confinamiento cada {self.config.MAX_CONFINEMENT_SPACING:.0f}m como máximo"
            )

        # Verificar relación vano/muro
        vo_ratio_compliant = True
        if opening_width > 0:
            vo_ratio_compliant, msg = self.check_vo_ratio(
                dimensions.length, opening_width
            )
            if not vo_ratio_compliant:
                issues.append(msg)
                recommendations.append(
                    f"Reducir el ancho del vano o aumentar la longitud del muro"
                )

        # Verificar refuerzo
        reinforcement_compliant = True
        if dimensions.thickness:
            wall_area = dimensions.length * dimensions.thickness
            reinforcement_compliant, msg = self.check_reinforcement(
                wall_area, reinforcement_area
            )
            if not reinforcement_compliant:
                issues.append(msg)
                recommendations.append(
                    f"Agregar refuerzo mínimo del {self.config.MIN_REINFORCEMENT_RATIO*100:.2f}% del área bruta"
                )

        # Calcular vulnerabilidad
        vulnerability_score, vulnerability_level = self.calculate_vulnerability_score(
            thickness_compliant,
            confinement_compliant,
            vo_ratio_compliant,
            reinforcement_compliant
        )

        # Agregar recomendaciones generales si hay vulnerabilidad
        if vulnerability_level in [VulnerabilityLevel.HIGH, VulnerabilityLevel.CRITICAL]:
            recommendations.append("Consultar con un ingeniero estructural profesional")
            recommendations.append("Considerar reforzamiento de la estructura")

        return E060AnalysisResult(
            element_type=ElementType.WALL,
            element_id=dimensions.element_id,
            floor_level=dimensions.floor_level,
            measured_width=dimensions.width,
            measured_height=dimensions.height,
            measured_thickness=dimensions.thickness,
            required_thickness=self.get_required_thickness(dimensions.floor_level),
            required_confinement_spacing=self.config.MAX_CONFINEMENT_SPACING,
            required_vo_ratio=self.config.MAX_VO_RATIO,
            thickness_compliant=thickness_compliant,
            confinement_compliant=confinement_compliant,
            vo_ratio_compliant=vo_ratio_compliant,
            reinforcement_compliant=reinforcement_compliant,
            vulnerability_score=vulnerability_score,
            vulnerability_level=vulnerability_level,
            issues=issues,
            recommendations=recommendations
        )

    def analyze_column(
        self,
        dimensions: ElementDimensions,
        reinforcement_area: Optional[float] = None
    ) -> E060AnalysisResult:
        """Analiza una columna según E.060"""
        issues = []
        recommendations = []

        # Verificar dimensiones mínimas
        min_dimension = 0.20  # 20cm mínimo
        width_compliant = dimensions.width >= min_dimension
        depth_compliant = dimensions.height >= min_dimension

        if not width_compliant:
            issues.append(f"Ancho {dimensions.width*100:.0f}cm < {min_dimension*100:.0f}cm mínimo")
            recommendations.append(f"Aumentar ancho de columna a mínimo {min_dimension*100:.0f}cm")

        if not depth_compliant:
            issues.append(f"Profundidad {dimensions.height*100:.0f}cm < {min_dimension*100:.0f}cm mínimo")
            recommendations.append(f"Aumentar profundidad de columna a mínimo {min_dimension*100:.0f}cm")

        # Verificar refuerzo
        reinforcement_compliant = True
        if reinforcement_area:
            column_area = dimensions.width * dimensions.height
            min_reinforcement = column_area * 0.01  # 1% mínimo para columnas
            reinforcement_compliant = reinforcement_area >= min_reinforcement
            if not reinforcement_compliant:
                issues.append(f"Refuerzo insuficiente")
                recommendations.append(f"Aumentar refuerzo a mínimo {min_reinforcement*10000:.0f}cm²")

        # Vulnerabilidad
        all_compliant = width_compliant and depth_compliant and reinforcement_compliant
        vulnerability_score = 0 if all_compliant else 50
        vulnerability_level = VulnerabilityLevel.LOW if all_compliant else VulnerabilityLevel.HIGH

        return E060AnalysisResult(
            element_type=ElementType.COLUMN,
            element_id=dimensions.element_id,
            floor_level=dimensions.floor_level,
            measured_width=dimensions.width,
            measured_height=dimensions.height,
            measured_thickness=None,
            required_thickness=min_dimension,
            required_confinement_spacing=0,
            required_vo_ratio=0,
            thickness_compliant=width_compliant and depth_compliant,
            confinement_compliant=True,
            vo_ratio_compliant=True,
            reinforcement_compliant=reinforcement_compliant,
            vulnerability_score=vulnerability_score,
            vulnerability_level=vulnerability_level,
            issues=issues,
            recommendations=recommendations
        )

    def analyze_beam(
        self,
        dimensions: ElementDimensions,
        reinforcement_area: Optional[float] = None
    ) -> E060AnalysisResult:
        """Analiza una viga según E.060"""
        issues = []
        recommendations = []

        # Verificar dimensiones mínimas
        min_width = 0.20  # 20cm
        min_depth = dimensions.width * 1.5  # Relación altura/ancho mínima

        width_compliant = dimensions.width >= min_width
        depth_compliant = dimensions.height >= min_depth

        if not width_compliant:
            issues.append(f"Ancho {dimensions.width*100:.0f}cm < {min_width*100:.0f}cm mínimo")

        if not depth_compliant:
            issues.append(f"Altura {dimensions.height*100:.0f}cm < {min_depth*100:.0f}cm recomendada")

        # Verificar refuerzo
        reinforcement_compliant = True
        if reinforcement_area:
            beam_area = dimensions.width * dimensions.height
            min_reinforcement = beam_area * 0.005  # 0.5% mínimo
            reinforcement_compliant = reinforcement_area >= min_reinforcement
            if not reinforcement_compliant:
                issues.append("Refuerzo insuficiente")

        # Vulnerabilidad
        all_compliant = width_compliant and depth_compliant and reinforcement_compliant
        vulnerability_score = 0 if all_compliant else 40
        vulnerability_level = VulnerabilityLevel.LOW if all_compliant else VulnerabilityLevel.MEDIUM

        return E060AnalysisResult(
            element_type=ElementType.BEAM,
            element_id=dimensions.element_id,
            floor_level=dimensions.floor_level,
            measured_width=dimensions.width,
            measured_height=dimensions.height,
            measured_thickness=None,
            required_thickness=min_width,
            required_confinement_spacing=0,
            required_vo_ratio=0,
            thickness_compliant=width_compliant and depth_compliant,
            confinement_compliant=True,
            vo_ratio_compliant=True,
            reinforcement_compliant=reinforcement_compliant,
            vulnerability_score=vulnerability_score,
            vulnerability_level=vulnerability_level,
            issues=issues,
            recommendations=recommendations
        )


async def analyze_structure(
    inspection,
    detections: list,
    point_cloud_path: str
) -> List[Dict]:
    """
    Función principal para analizar la estructura de una inspección.
    Retorna lista de métricas estructurales.
    """
    analyzer = E060Analyzer()
    metrics = []

    # Agrupar detecciones por tipo
    walls = [d for d in detections if d.class_name in ["wall", "muro"]]
    columns = [d for d in detections if d.class_name in ["column", "columna"]]
    beams = [d for d in detections if d.class_name in ["beam", "viga"]]

    # Analizar muros
    for i, wall in enumerate(walls):
        # Estimar dimensiones desde bounding box
        # Esto es simplificado - en producción usaríamos la nube de puntos
        width = (wall.bbox_x2 - wall.bbox_x1) / 100  # Convertir píxeles a metros (aprox)
        height = (wall.bbox_y2 - wall.bbox_y1) / 100

        dimensions = ElementDimensions(
            element_type=ElementType.WALL,
            element_id=f"wall_{i}",
            floor_level=0,  # Determinar desde posición
            width=width,
            height=height,
            length=width * 3,  # Estimación
            thickness=0.15,  # Default
            position_x=wall.position_x or 0,
            position_y=wall.position_y or 0,
            position_z=wall.position_z or 0,
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
        width = (col.bbox_x2 - col.bbox_x1) / 100
        height = (col.bbox_y2 - col.bbox_y1) / 100

        dimensions = ElementDimensions(
            element_type=ElementType.COLUMN,
            element_id=f"column_{i}",
            floor_level=0,
            width=width,
            height=height,
            length=0,
            position_x=col.position_x or 0,
            position_y=col.position_y or 0,
            position_z=col.position_z or 0,
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
