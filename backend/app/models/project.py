from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Text, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class ProjectStatus(str, enum.Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class InspectionStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class CaptureSource(str, enum.Enum):
    DRON = "dron"
    MOBILE = "mobile"
    COMBINED = "combined"


class VulnerabilityLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    phone = Column(String(50))
    is_active = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    projects = relationship("Project", back_populates="owner")


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    address = Column(Text)
    latitude = Column(Float)
    longitude = Column(Float)
    status = Column(SQLEnum(ProjectStatus), default=ProjectStatus.ACTIVE)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    owner = relationship("User", back_populates="projects")
    inspections = relationship("Inspection", back_populates="project")


class Inspection(Base):
    __tablename__ = "inspections"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    status = Column(SQLEnum(InspectionStatus), default=InspectionStatus.PENDING)
    capture_source = Column(SQLEnum(CaptureSource), nullable=False)

    # Dron capture info
    dron_video_path = Column(String(500))
    dron_gps_data = Column(JSON)  # GPS coordinates from DJI M4E
    dron_altitude = Column(Float)  # Flight altitude in meters

    # Mobile capture info
    mobile_device_info = Column(JSON)  # Device model, LiDAR availability
    mobile_capture_count = Column(Integer, default=0)

    # Processing results
    frames_extracted = Column(Integer, default=0)
    point_cloud_path = Column(String(500))
    model_3dgs_path = Column(String(500))

    # Analysis
    total_detections = Column(Integer, default=0)
    vulnerability_score = Column(Float)  # 0-100
    vulnerability_level = Column(SQLEnum(VulnerabilityLevel))

    # Metadata
    processing_started_at = Column(DateTime(timezone=True))
    processing_completed_at = Column(DateTime(timezone=True))
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    project = relationship("Project", back_populates="inspections")
    detections = relationship("Detection", back_populates="inspection")
    structural_metrics = relationship("StructuralMetric", back_populates="inspection")
    reports = relationship("Report", back_populates="inspection")


class Detection(Base):
    __tablename__ = "detections"

    id = Column(Integer, primary_key=True, index=True)
    inspection_id = Column(Integer, ForeignKey("inspections.id"), nullable=False)
    frame_file = Column(String(255), nullable=False)
    class_name = Column(String(100), nullable=False)
    confidence = Column(Float, nullable=False)

    # Bounding box
    bbox_x1 = Column(Float)
    bbox_y1 = Column(Float)
    bbox_x2 = Column(Float)
    bbox_y2 = Column(Float)

    # 3D position (if available from point cloud)
    position_x = Column(Float)
    position_y = Column(Float)
    position_z = Column(Float)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    inspection = relationship("Inspection", back_populates="detections")


class StructuralMetric(Base):
    __tablename__ = "structural_metrics"

    id = Column(Integer, primary_key=True, index=True)
    inspection_id = Column(Integer, ForeignKey("inspections.id"), nullable=False)

    # Element identification
    element_type = Column(String(100), nullable=False)  # column, beam, wall, slab
    element_id = Column(String(100))  # Unique identifier within inspection

    # Dimensions (measured from 3D model)
    width = Column(Float)  # meters
    height = Column(Float)  # meters
    length = Column(Float)  # meters
    thickness = Column(Float)  # meters (for walls, slabs)

    # Position
    floor_level = Column(Integer)  # 0=ground, 1=first floor, etc.
    position_x = Column(Float)
    position_y = Column(Float)
    position_z = Column(Float)

    # E.060 Analysis Results
    meets_minimum_thickness = Column(String(10))  # yes/no/na
    meets_confinement = Column(String(10))  # yes/no/na
    meets_vo_ratio = Column(String(10))  # yes/no/na
    meets_reinforcement = Column(String(10))  # yes/no/na

    # Vulnerability assessment
    vulnerability_score = Column(Float)  # 0-100
    vulnerability_level = Column(SQLEnum(VulnerabilityLevel))
    issues_found = Column(JSON)  # List of specific issues

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    inspection = relationship("Inspection", back_populates="structural_metrics")


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    inspection_id = Column(Integer, ForeignKey("inspections.id"), nullable=False)

    # Report content
    title = Column(String(255), nullable=False)
    summary = Column(Text)
    recommendations = Column(JSON)  # List of recommendations

    # Files
    pdf_path = Column(String(500))
    html_path = Column(String(500))
    model_viewer_url = Column(String(500))  # URL to 3D viewer

    # Scores
    overall_vulnerability_score = Column(Float)
    structural_score = Column(Float)
    confinement_score = Column(Float)
    connection_score = Column(Float)

    generated_at = Column(DateTime(timezone=True), server_default=func.now())

    inspection = relationship("Inspection", back_populates="reports")
