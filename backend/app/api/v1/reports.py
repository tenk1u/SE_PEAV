from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List
from datetime import datetime

from app.core.database import get_db
from app.models.project import (
    User, Project, Inspection, Report,
    InspectionStatus, VulnerabilityLevel
)
from app.schemas.project import ReportResponse
from app.api.v1.auth import get_current_user
from app.services.storage import get_presigned_url

router = APIRouter(prefix="/reports")


@router.get("/", response_model=List[ReportResponse])
async def list_reports(
    inspection_id: int = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = (
        select(Report)
        .join(Inspection)
        .join(Project)
        .where(Project.owner_id == current_user.id)
    )
    if inspection_id:
        query = query.where(Report.inspection_id == inspection_id)
    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Report)
        .options(selectinload(Report.inspection).selectinload(Inspection.project))
        .where(Report.id == report_id)
    )
    report = result.scalar_one_or_none()

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )

    # Verify ownership
    if report.inspection.project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this report"
        )

    return report


@router.get("/{report_id}/download")
async def download_report(
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Report)
        .options(selectinload(Report.inspection).selectinload(Inspection.project))
        .where(Report.id == report_id)
    )
    report = result.scalar_one_or_none()

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )

    # Verify ownership
    if report.inspection.project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this report"
        )

    if not report.pdf_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report PDF not generated yet"
        )

    # Get presigned URL
    url = await get_presigned_url(report.pdf_path)
    if not url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate download URL"
        )

    return {"download_url": url}


@router.get("/{report_id}/viewer")
async def get_viewer_url(
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Report)
        .options(selectinload(Report.inspection).selectinload(Inspection.project))
        .where(Report.id == report_id)
    )
    report = result.scalar_one_or_none()

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )

    # Verify ownership
    if report.inspection.project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this report"
        )

    if not report.model_viewer_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="3D viewer not available for this report"
        )

    return {"viewer_url": report.model_viewer_url}


@router.post("/{inspection_id}/generate", response_model=ReportResponse)
async def generate_report(
    inspection_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify inspection ownership
    result = await db.execute(
        select(Inspection)
        .options(selectinload(Inspection.project))
        .where(Inspection.id == inspection_id)
    )
    inspection = result.scalar_one_or_none()

    if not inspection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inspection not found"
        )

    if inspection.project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to generate report for this inspection"
        )

    if inspection.status != InspectionStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inspection must be completed before generating report"
        )

    # Check if report already exists
    existing = await db.execute(
        select(Report).where(Report.inspection_id == inspection_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Report already exists for this inspection"
        )

    # Generate report
    # This will be integrated with existing 04_reporting_etl
    # For now, create placeholder
    report = Report(
        inspection_id=inspection_id,
        title=f"Informe de Inspección #{inspection_id}",
        summary="Análisis estructural completado",
        overall_vulnerability_score=inspection.vulnerability_score,
    )

    db.add(report)
    await db.commit()
    await db.refresh(report)

    return report
