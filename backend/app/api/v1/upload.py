from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import uuid

from app.core.database import get_db
from app.models.project import User
from app.schemas.project import UploadResponse, MobileCaptureUpload
from app.api.v1.auth import get_current_user
from app.services.storage import upload_file, upload_bytes

router = APIRouter(prefix="/upload")


@router.post("/video", response_model=UploadResponse)
async def upload_video(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Upload a video file (dron capture)."""
    # Validate file type
    allowed_extensions = ['.mp4', '.avi', '.mov', '.mkv']
    if not any(file.filename.lower().endswith(ext) for ext in allowed_extensions):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid video format. Allowed: {', '.join(allowed_extensions)}"
        )

    # Generate unique path
    file_ext = file.filename.split('.')[-1]
    unique_id = str(uuid.uuid4())[:8]
    path = f"uploads/{current_user.id}/videos/{unique_id}_{file.filename}"

    # Upload
    result = await upload_file(file, path)

    return UploadResponse(**result)


@router.post("/images", response_model=List[UploadResponse])
async def upload_images(
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user)
):
    """Upload multiple image files (mobile captures)."""
    results = []

    for file in files:
        # Validate file type
        allowed_extensions = ['.jpg', '.jpeg', '.png']
        if not any(file.filename.lower().endswith(ext) for ext in allowed_extensions):
            continue

        # Generate unique path
        file_ext = file.filename.split('.')[-1]
        unique_id = str(uuid.uuid4())[:8]
        path = f"uploads/{current_user.id}/images/{unique_id}_{file.filename}"

        # Upload
        result = await upload_file(file, path)
        results.append(UploadResponse(**result))

    if not results:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid image files uploaded"
        )

    return results


@router.post("/lidar", response_model=UploadResponse)
async def upload_lidar_data(
    file: UploadFile = File(...),
    metadata: MobileCaptureUpload = Depends(),
    current_user: User = Depends(get_current_user)
):
    """Upload LiDAR scan data from iPhone Pro."""
    # Validate file type
    allowed_extensions = ['.ply', '.pcd', '.obj', '.usdz']
    if not any(file.filename.lower().endswith(ext) for ext in allowed_extensions):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid 3D format. Allowed: {', '.join(allowed_extensions)}"
        )

    # Generate unique path
    file_ext = file.filename.split('.')[-1]
    unique_id = str(uuid.uuid4())[:8]
    path = f"uploads/{current_user.id}/lidar/{unique_id}_{file.filename}"

    # Upload
    result = await upload_file(file, path)

    return UploadResponse(**result)


@router.post("/point-cloud", response_model=UploadResponse)
async def upload_point_cloud(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Upload a processed point cloud file."""
    # Validate file type
    allowed_extensions = ['.ply', '.pcd', '.xyz', '.las', '.laz']
    if not any(file.filename.lower().endswith(ext) for ext in allowed_extensions):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid point cloud format. Allowed: {', '.join(allowed_extensions)}"
        )

    # Generate unique path
    file_ext = file.filename.split('.')[-1]
    unique_id = str(uuid.uuid4())[:8]
    path = f"uploads/{current_user.id}/point_clouds/{unique_id}_{file.filename}"

    # Upload
    result = await upload_file(file, path)

    return UploadResponse(**result)
