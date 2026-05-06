from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List
import uuid
from datetime import datetime

from app.core.database import get_db
from app.models.project import (
    User, Project, Inspection, InspectionStatus,
    Detection, StructuralMetric, CaptureSource
)
from app.schemas.project import (
    InspectionCreate, InspectionResponse, InspectionDetail,
    DetectionResponse, StructuralMetricResponse, ProcessingStatus
)
from app.api.v1.auth import get_current_user
from app.services.storage import upload_file, get_presigned_url
from app.services.processing import start_processing

router = APIRouter(prefix="/inspections")


@router.get("/", response_model=List[InspectionResponse])
async def list_inspections(
    project_id: int = None,
    status_filter: InspectionStatus = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(Inspection).join(Project).where(Project.owner_id == current_user.id)
    if project_id:
        query = query.where(Inspection.project_id == project_id)
    if status_filter:
        query = query.where(Inspection.status == status_filter)
    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    return result.scalars().all()


@router.post("/", response_model=InspectionResponse, status_code=status.HTTP_201_CREATED)
async def create_inspection(
    inspection_data: InspectionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify project ownership
    result = await db.execute(
        select(Project).where(
            Project.id == inspection_data.project_id,
            Project.owner_id == current_user.id
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    inspection = Inspection(**inspection_data.model_dump())
    db.add(inspection)
    await db.commit()
    await db.refresh(inspection)
    return inspection


@router.get("/{inspection_id}", response_model=InspectionDetail)
async def get_inspection(
    inspection_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Inspection)
        .options(selectinload(Inspection.project))
        .join(Project)
        .where(
            Inspection.id == inspection_id,
            Project.owner_id == current_user.id
        )
    )
    inspection = result.scalar_one_or_none()
    if not inspection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inspection not found"
        )
    return inspection


@router.get("/{inspection_id}/status", response_model=ProcessingStatus)
async def get_processing_status(
    inspection_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Inspection)
        .join(Project)
        .where(
            Inspection.id == inspection_id,
            Project.owner_id == current_user.id
        )
    )
    inspection = result.scalar_one_or_none()
    if not inspection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inspection not found"
        )

    # Calculate progress based on status
    progress = 0
    current_step = None
    if inspection.status == InspectionStatus.PENDING:
        progress = 0
        current_step = "Waiting to start"
    elif inspection.status == InspectionStatus.PROCESSING:
        if inspection.frames_extracted > 0:
            progress = 25
            current_step = "Extracting frames"
        if inspection.point_cloud_path:
            progress = 50
            current_step = "Generating point cloud"
        if inspection.model_3dgs_path:
            progress = 75
            current_step = "Training 3DGS model"
    elif inspection.status == InspectionStatus.COMPLETED:
        progress = 100
        current_step = "Completed"
    elif inspection.status == InspectionStatus.FAILED:
        progress = 0
        current_step = "Failed"

    return ProcessingStatus(
        inspection_id=inspection.id,
        status=inspection.status,
        progress_percentage=progress,
        current_step=current_step,
        error_message=inspection.error_message
    )


@router.post("/{inspection_id}/upload/dron")
async def upload_dron_video(
    inspection_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify ownership
    result = await db.execute(
        select(Inspection)
        .join(Project)
        .where(
            Inspection.id == inspection_id,
            Project.owner_id == current_user.id
        )
    )
    inspection = result.scalar_one_or_none()
    if not inspection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inspection not found"
        )

    # Validate file type
    if not file.filename.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid video format"
        )

    # Upload to storage
    file_path = f"inspections/{inspection_id}/dron/{file.filename}"
    upload_result = await upload_file(file, file_path)

    # Update inspection
    inspection.dron_video_path = upload_result["file_path"]
    await db.commit()

    return {"message": "Video uploaded successfully", "file_path": file_path}


@router.post("/{inspection_id}/upload/mobile")
async def upload_mobile_captures(
    inspection_id: int,
    files: List[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify ownership
    result = await db.execute(
        select(Inspection)
        .join(Project)
        .where(
            Inspection.id == inspection_id,
            Project.owner_id == current_user.id
        )
    )
    inspection = result.scalar_one_or_none()
    if not inspection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inspection not found"
        )

    uploaded_files = []
    for file in files:
        if not file.filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            continue

        file_path = f"inspections/{inspection_id}/mobile/{file.filename}"
        upload_result = await upload_file(file, file_path)
        uploaded_files.append(upload_result["file_path"])

    inspection.mobile_capture_count = (inspection.mobile_capture_count or 0) + len(uploaded_files)
    await db.commit()

    return {
        "message": f"{len(uploaded_files)} files uploaded",
        "files": uploaded_files
    }


@router.post("/{inspection_id}/process")
async def trigger_processing(
    inspection_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify ownership
    result = await db.execute(
        select(Inspection)
        .join(Project)
        .where(
            Inspection.id == inspection_id,
            Project.owner_id == current_user.id
        )
    )
    inspection = result.scalar_one_or_none()
    if not inspection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inspection not found"
        )

    if inspection.status == InspectionStatus.PROCESSING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inspection is already processing"
        )

    # Start async processing
    await start_processing(inspection_id)

    inspection.status = InspectionStatus.PROCESSING
    inspection.processing_started_at = datetime.utcnow()
    await db.commit()

    return {"message": "Processing started", "inspection_id": inspection_id}


@router.get("/{inspection_id}/detections", response_model=List[DetectionResponse])
async def get_detections(
    inspection_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify ownership
    result = await db.execute(
        select(Inspection)
        .join(Project)
        .where(
            Inspection.id == inspection_id,
            Project.owner_id == current_user.id
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inspection not found"
        )

    result = await db.execute(
        select(Detection).where(Detection.inspection_id == inspection_id)
    )
    return result.scalars().all()


@router.get("/{inspection_id}/metrics", response_model=List[StructuralMetricResponse])
async def get_structural_metrics(
    inspection_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify ownership
    result = await db.execute(
        select(Inspection)
        .join(Project)
        .where(
            Inspection.id == inspection_id,
            Project.owner_id == current_user.id
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inspection not found"
        )

    result = await db.execute(
        select(StructuralMetric).where(StructuralMetric.inspection_id == inspection_id)
    )
    return result.scalars().all()
