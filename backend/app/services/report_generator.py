"""
Servicio de reportes - Adaptado de 04_reporting_etl.

Este servicio genera reportes PDF con análisis estructural y vulnerabilidades.
"""
import asyncio
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ReportData:
    """Datos para generar un reporte."""
    inspection_id: int
    project_name: str
    address: str
    capture_date: datetime
    total_detections: int
    vulnerability_score: float
    vulnerability_level: str
    detections_by_class: Dict[str, int]
    structural_metrics: List[Dict[str, Any]]
    recommendations: List[str]
    images: List[str]  # Paths a imágenes del reporte


@dataclass
class GeneratedReport:
    """Resultado de la generación de un reporte."""
    pdf_path: str
    html_path: str
    report_id: int
    generated_at: datetime
    file_size_bytes: int


class ReportGenerator:
    """Generador de reportes PDF."""

    def __init__(self, output_dir: str, templates_dir: Optional[str] = None):
        """
        Args:
            output_dir: Directorio donde guardar los reportes
            templates_dir: Directorio con plantillas HTML
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Usar plantillas del proyecto existente si no se especifica
        if templates_dir:
            self.templates_dir = Path(templates_dir)
        else:
            self.templates_dir = Path("04_reporting_etl/templates")

    def generate_report(
        self,
        data: ReportData,
        include_images: bool = True,
        include_3d_viewer: bool = True
    ) -> GeneratedReport:
        """
        Genera un reporte PDF.

        Args:
            data: Datos del reporte
            include_images: Si incluir imágenes en el reporte
            include_3d_viewer: Si incluir enlace al visor 3D

        Returns:
            GeneratedReport con el path del PDF generado
        """
        import time
        start = time.time()

        # Preparar contexto para la plantilla
        context = self._prepare_context(data, include_images, include_3d_viewer)

        # Generar HTML
        html_content = self._render_html(context)

        # Guardar HTML
        html_filename = f"report_{data.inspection_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        html_path = self.output_dir / html_filename
        html_path.write_text(html_content, encoding="utf-8")

        # Convertir a PDF
        pdf_path = self._html_to_pdf(html_path)

        generation_time = (time.time() - start) * 1000

        return GeneratedReport(
            pdf_path=str(pdf_path),
            html_path=str(html_path),
            report_id=data.inspection_id,
            generated_at=datetime.now(),
            file_size_bytes=pdf_path.stat().st_size if pdf_path.exists() else 0
        )

    def _prepare_context(
        self,
        data: ReportData,
        include_images: bool,
        include_3d_viewer: bool
    ) -> Dict[str, Any]:
        """Prepara el contexto para la plantilla HTML."""
        # Determinar nivel de riesgo
        risk_level, risk_color, risk_description = self._get_risk_level(
            data.vulnerability_score
        )

        # Generar recomendaciones basadas en vulnerabilidades
        recommendations = self._generate_recommendations(data)

        return {
            "report": {
                "id": data.inspection_id,
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "project_name": data.project_name,
                "address": data.address,
                "capture_date": data.capture_date.strftime("%Y-%m-%d"),
            },
            "summary": {
                "total_detections": data.total_detections,
                "vulnerability_score": round(data.vulnerability_score, 1),
                "vulnerability_level": data.vulnerability_level,
                "risk_level": risk_level,
                "risk_color": risk_color,
                "risk_description": risk_description,
            },
            "detections": {
                "by_class": data.detections_by_class,
                "total": data.total_detections,
            },
            "structural_analysis": {
                "metrics": data.structural_metrics,
                "compliant_count": sum(
                    1 for m in data.structural_metrics
                    if m.get("meets_minimum_thickness") == "yes"
                ),
                "non_compliant_count": sum(
                    1 for m in data.structural_metrics
                    if m.get("meets_minimum_thickness") == "no"
                ),
            },
            "recommendations": recommendations,
            "images": data.images if include_images else [],
            "viewer_url": f"/viewer/{data.inspection_id}" if include_3d_viewer else None,
        }

    def _get_risk_level(self, score: float) -> tuple:
        """Determina el nivel de riesgo basado en el score."""
        if score >= 75:
            return "CRÍTICO", "#dc3545", "Intervención inmediata requerida"
        elif score >= 50:
            return "ALTO", "#fd7e14", "Reforzamiento recomendado"
        elif score >= 25:
            return "MEDIO", "#ffc107", "Monitoreo necesario"
        else:
            return "BAJO", "#28a745", "Estructura aceptable"

    def _generate_recommendations(self, data: ReportData) -> List[str]:
        """Genera recomendaciones basadas en los análisis."""
        recommendations = []

        # Recomendaciones basadas en score de vulnerabilidad
        if data.vulnerability_score >= 75:
            recommendations.extend([
                "Consultar con un ingeniero estructural profesional URGENTE",
                "Evaluar la necesidad de evacuación preventiva",
                "Realizar inspección detallada de todos los elementos estructurales",
            ])
        elif data.vulnerability_score >= 50:
            recommendations.extend([
                "Consultar con un ingeniero estructural profesional",
                "Planificar trabajos de reforzamiento estructural",
                "Monitorear grietas y deformaciones periódicamente",
            ])
        elif data.vulnerability_score >= 25:
            recommendations.extend([
                "Realizar inspecciones periódicas (cada 6 meses)",
                "Monitorear el desarrollo de grietas",
                "Mantener registros de cualquier cambio observado",
            ])

        # Recomendaciones basadas en métricas estructurales
        for metric in data.structural_metrics:
            if metric.get("meets_minimum_thickness") == "no":
                recommendations.append(
                    f"Aumentar espesor de {metric.get('element_type', 'elemento')} "
                    f"(actual: {metric.get('thickness', 'N/A')}m, "
                    f"mínimo: {metric.get('required_thickness', 'N/A')}m)"
                )

            if metric.get("meets_confinement") == "no":
                recommendations.append(
                    f"Agregar confinamiento en {metric.get('element_type', 'elemento')} "
                    f"cada máximo 4 metros"
                )

        # Eliminar duplicados manteniendo orden
        seen = set()
        unique_recommendations = []
        for rec in recommendations:
            if rec not in seen:
                seen.add(rec)
                unique_recommendations.append(rec)

        return unique_recommendations

    def _render_html(self, context: Dict[str, Any]) -> str:
        """Renderiza la plantilla HTML con Jinja2."""
        try:
            from jinja2 import Environment, FileSystemLoader, select_autoescape

            env = Environment(
                loader=FileSystemLoader(str(self.templates_dir)),
                autoescape=select_autoescape(["html"])
            )

            template = env.get_template("report_template.html")
            return template.render(**context)

        except ImportError:
            logger.warning("Jinja2 no está instalado. Generando HTML básico.")
            return self._generate_basic_html(context)

    def _generate_basic_html(self, context: Dict[str, Any]) -> str:
        """Genera un HTML básico sin Jinja2."""
        report = context["report"]
        summary = context["summary"]
        detections = context["detections"]
        recommendations = context["recommendations"]

        html = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reporte de Inspección #{report['id']}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .header {{ background: #f8f9fa; padding: 20px; border-radius: 8px; }}
        .risk-badge {{ 
            display: inline-block; 
            padding: 8px 16px; 
            border-radius: 4px; 
            color: white;
            background: {summary['risk_color']};
        }}
        .section {{ margin: 20px 0; }}
        .metric {{ display: flex; justify-content: space-between; padding: 10px; border-bottom: 1px solid #eee; }}
        .recommendation {{ padding: 10px; background: #fff3cd; margin: 5px 0; border-radius: 4px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Reporte de Inspección Estructural</h1>
        <p><strong>Proyecto:</strong> {report['project_name']}</p>
        <p><strong>Dirección:</strong> {report['address']}</p>
        <p><strong>Fecha:</strong> {report['capture_date']}</p>
    </div>

    <div class="section">
        <h2>Resumen</h2>
        <p><strong>Detecciones totales:</strong> {detections['total']}</p>
        <p><strong>Score de vulnerabilidad:</strong> {summary['vulnerability_score']}/100</p>
        <p><strong>Nivel de riesgo:</strong> <span class="risk-badge">{summary['risk_level']}</span></p>
        <p>{summary['risk_description']}</p>
    </div>

    <div class="section">
        <h2>Recomendaciones</h2>
        {''.join(f'<div class="recommendation">{rec}</div>' for rec in recommendations)}
    </div>

    <div class="section">
        <h2>Elementos Detectados</h2>
        {''.join(f'<div class="metric"><span>{cls}</span><span>{count}</span></div>' for cls, count in detections['by_class'].items())}
    </div>
</body>
</html>
"""
        return html

    def _html_to_pdf(self, html_path: Path) -> Path:
        """Convierte HTML a PDF usando WeasyPrint."""
        pdf_filename = html_path.stem + ".pdf"
        pdf_path = html_path.parent / pdf_filename

        try:
            from weasyprint import HTML
            HTML(filename=str(html_path)).write_pdf(str(pdf_path))
            logger.info(f"PDF generado: {pdf_path}")
        except ImportError:
            logger.warning("WeasyPrint no está instalado. Solo se generó HTML.")
            # Crear archivo vacío para que no falle
            pdf_path.touch()
        except Exception as e:
            logger.error(f"Error generando PDF: {e}")
            pdf_path.touch()

        return pdf_path


async def generate_inspection_report(
    inspection_id: int,
    project_name: str,
    address: str,
    detections: List[Dict[str, Any]],
    structural_metrics: List[Dict[str, Any]],
    output_dir: str
) -> GeneratedReport:
    """
    Función principal para generar un reporte de inspección.

    Args:
        inspection_id: ID de la inspección
        project_name: Nombre del proyecto
        address: Dirección del proyecto
        detections: Lista de detecciones
        structural_metrics: Métricas estructurales
        output_dir: Directorio de salida

    Returns:
        GeneratedReport con el reporte generado
    """
    # Calcular estadísticas
    total_detections = len(detections)
    detections_by_class = {}
    for det in detections:
        cls = det.get("class_name", "unknown")
        detections_by_class[cls] = detections_by_class.get(cls, 0) + 1

    # Calcular score de vulnerabilidad promedio
    vulnerability_scores = [
        m.get("vulnerability_score", 0)
        for m in structural_metrics
        if m.get("vulnerability_score") is not None
    ]
    avg_vulnerability = (
        sum(vulnerability_scores) / len(vulnerability_scores)
        if vulnerability_scores else 0
    )

    # Determinar nivel de vulnerabilidad
    if avg_vulnerability >= 75:
        vuln_level = "critical"
    elif avg_vulnerability >= 50:
        vuln_level = "high"
    elif avg_vulnerability >= 25:
        vuln_level = "medium"
    else:
        vuln_level = "low"

    # Preparar datos del reporte
    report_data = ReportData(
        inspection_id=inspection_id,
        project_name=project_name,
        address=address,
        capture_date=datetime.now(),
        total_detections=total_detections,
        vulnerability_score=avg_vulnerability,
        vulnerability_level=vuln_level,
        detections_by_class=detections_by_class,
        structural_metrics=structural_metrics,
        recommendations=[],
        images=[]
    )

    # Generar reporte
    generator = ReportGenerator(output_dir)
    return generator.generate_report(report_data)
