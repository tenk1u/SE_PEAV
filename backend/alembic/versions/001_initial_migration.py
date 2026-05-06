Initial migration - Create all tables

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('is_active', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)

    # Create projects table
    op.create_table('projects',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('status', sa.Enum('ACTIVE', 'ARCHIVED', name='projectstatus'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_projects_id'), 'projects', ['id'], unique=False)

    # Create inspections table
    op.create_table('inspections',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', name='inspectionstatus'), nullable=True),
        sa.Column('capture_source', sa.Enum('DRON', 'MOBILE', 'COMBINED', name='capturesource'), nullable=False),
        sa.Column('dron_video_path', sa.String(length=500), nullable=True),
        sa.Column('dron_gps_data', sa.JSON(), nullable=True),
        sa.Column('dron_altitude', sa.Float(), nullable=True),
        sa.Column('mobile_device_info', sa.JSON(), nullable=True),
        sa.Column('mobile_capture_count', sa.Integer(), nullable=True),
        sa.Column('frames_extracted', sa.Integer(), nullable=True),
        sa.Column('point_cloud_path', sa.String(length=500), nullable=True),
        sa.Column('model_3dgs_path', sa.String(length=500), nullable=True),
        sa.Column('total_detections', sa.Integer(), nullable=True),
        sa.Column('vulnerability_score', sa.Float(), nullable=True),
        sa.Column('vulnerability_level', sa.Enum('LOW', 'MEDIUM', 'HIGH', 'CRITICAL', name='vulnerabilitylevel'), nullable=True),
        sa.Column('processing_started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('processing_completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_inspections_id'), 'inspections', ['id'], unique=False)

    # Create detections table
    op.create_table('detections',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('inspection_id', sa.Integer(), nullable=False),
        sa.Column('frame_file', sa.String(length=255), nullable=False),
        sa.Column('class_name', sa.String(length=100), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('bbox_x1', sa.Float(), nullable=True),
        sa.Column('bbox_y1', sa.Float(), nullable=True),
        sa.Column('bbox_x2', sa.Float(), nullable=True),
        sa.Column('bbox_y2', sa.Float(), nullable=True),
        sa.Column('position_x', sa.Float(), nullable=True),
        sa.Column('position_y', sa.Float(), nullable=True),
        sa.Column('position_z', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['inspection_id'], ['inspections.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_detections_id'), 'detections', ['id'], unique=False)

    # Create structural_metrics table
    op.create_table('structural_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('inspection_id', sa.Integer(), nullable=False),
        sa.Column('element_type', sa.String(length=100), nullable=False),
        sa.Column('element_id', sa.String(length=100), nullable=True),
        sa.Column('width', sa.Float(), nullable=True),
        sa.Column('height', sa.Float(), nullable=True),
        sa.Column('length', sa.Float(), nullable=True),
        sa.Column('thickness', sa.Float(), nullable=True),
        sa.Column('floor_level', sa.Integer(), nullable=True),
        sa.Column('position_x', sa.Float(), nullable=True),
        sa.Column('position_y', sa.Float(), nullable=True),
        sa.Column('position_z', sa.Float(), nullable=True),
        sa.Column('meets_minimum_thickness', sa.String(length=10), nullable=True),
        sa.Column('meets_confinement', sa.String(length=10), nullable=True),
        sa.Column('meets_vo_ratio', sa.String(length=10), nullable=True),
        sa.Column('meets_reinforcement', sa.String(length=10), nullable=True),
        sa.Column('vulnerability_score', sa.Float(), nullable=True),
        sa.Column('vulnerability_level', sa.Enum('LOW', 'MEDIUM', 'HIGH', 'CRITICAL', name='vulnerabilitylevel'), nullable=True),
        sa.Column('issues_found', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['inspection_id'], ['inspections.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_structural_metrics_id'), 'structural_metrics', ['id'], unique=False)

    # Create reports table
    op.create_table('reports',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('inspection_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('recommendations', sa.JSON(), nullable=True),
        sa.Column('pdf_path', sa.String(length=500), nullable=True),
        sa.Column('html_path', sa.String(length=500), nullable=True),
        sa.Column('model_viewer_url', sa.String(length=500), nullable=True),
        sa.Column('overall_vulnerability_score', sa.Float(), nullable=True),
        sa.Column('structural_score', sa.Float(), nullable=True),
        sa.Column('confinement_score', sa.Float(), nullable=True),
        sa.Column('connection_score', sa.Float(), nullable=True),
        sa.Column('generated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['inspection_id'], ['inspections.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_reports_id'), 'reports', ['id'], unique=False)


def downgrade() -> None:
    op.drop_table('reports')
    op.drop_table('structural_metrics')
    op.drop_table('detections')
    op.drop_table('inspections')
    op.drop_table('projects')
    op.drop_table('users')
