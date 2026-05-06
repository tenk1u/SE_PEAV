from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


# Enums
class ProjectStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class InspectionStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class CaptureSource(str, Enum):
    DRON = "dron"
    MOBILE = "mobile"
    COMBINED = "combined"


class VulnerabilityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# User schemas
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    phone: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserResponse(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    email: EmailStr
    password: str


# Token schemas
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenPayload(BaseModel):
    sub: int
    exp: datetime


# Project schemas
class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    address: Optional[str] = None
    status: Optional[ProjectStatus] = None


class ProjectResponse(ProjectBase):
    id: int
    owner_id: int
    status: ProjectStatus
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Inspection schemas
class InspectionBase(BaseModel):
    capture_source: CaptureSource


class InspectionCreate(InspectionBase):
    project_id: int


class InspectionResponse(InspectionBase):
    id: int
    project_id: int
    status: InspectionStatus
    frames_extracted: int
    total_detections: int
    vulnerability_score: Optional[float] = None
    vulnerability_level: Optional[VulnerabilityLevel] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class InspectionDetail(InspectionResponse):
    dron_video_path: Optional[str] = None
    dron_gps_data: Optional[dict] = None
    mobile_device_info: Optional[dict] = None
    point_cloud_path: Optional[str] = None
    model_3dgs_path: Optional[str] = None
    processing_started_at: Optional[datetime] = None
    processing_completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


# Detection schemas
class DetectionResponse(BaseModel):
    id: int
    inspection_id: int
    frame_file: str
    class_name: str
    confidence: float
    bbox_x1: Optional[float] = None
    bbox_y1: Optional[float] = None
    bbox_x2: Optional[float] = None
    bbox_y2: Optional[float] = None
    position_x: Optional[float] = None
    position_y: Optional[float] = None
    position_z: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Structural Metric schemas
class StructuralMetricResponse(BaseModel):
    id: int
    inspection_id: int
    element_type: str
    element_id: Optional[str] = None
    width: Optional[float] = None
    height: Optional[float] = None
    length: Optional[float] = None
    thickness: Optional[float] = None
    floor_level: Optional[int] = None
    meets_minimum_thickness: Optional[str] = None
    meets_confinement: Optional[str] = None
    meets_vo_ratio: Optional[str] = None
    meets_reinforcement: Optional[str] = None
    vulnerability_score: Optional[float] = None
    vulnerability_level: Optional[VulnerabilityLevel] = None
    issues_found: Optional[List[str]] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Report schemas
class ReportResponse(BaseModel):
    id: int
    inspection_id: int
    title: str
    summary: Optional[str] = None
    recommendations: Optional[List[str]] = None
    pdf_path: Optional[str] = None
    model_viewer_url: Optional[str] = None
    overall_vulnerability_score: Optional[float] = None
    structural_score: Optional[float] = None
    confinement_score: Optional[float] = None
    connection_score: Optional[float] = None
    generated_at: datetime

    class Config:
        from_attributes = True


# Upload schemas
class UploadResponse(BaseModel):
    file_path: str
    file_size: int
    content_type: str
    upload_id: str


class MobileCaptureUpload(BaseModel):
    device_model: str
    has_lidar: bool
    arkit_supported: bool
    arcore_supported: bool
    capture_timestamp: datetime
    gps_latitude: Optional[float] = None
    gps_longitude: Optional[float] = None


# Processing schemas
class ProcessingStatus(BaseModel):
    inspection_id: int
    status: InspectionStatus
    progress_percentage: float = Field(0, ge=0, le=100)
    current_step: Optional[str] = None
    estimated_time_remaining: Optional[int] = None  # seconds
    error_message: Optional[str] = None


# Analysis result schemas
class E060AnalysisResult(BaseModel):
    element_type: str
    element_id: str
    floor_level: int

    # Measured dimensions
    measured_width: float
    measured_height: float
    measured_thickness: Optional[float] = None

    # E.060 requirements
    required_thickness: float
    required_confinement_spacing: float
    required_vo_ratio: float

    # Compliance
    thickness_compliant: bool
    confinement_compliant: bool
    vo_ratio_compliant: bool
    reinforcement_compliant: bool

    # Vulnerability
    vulnerability_score: float  # 0-100
    vulnerability_level: VulnerabilityLevel
    issues: List[str]
    recommendations: List[str]
