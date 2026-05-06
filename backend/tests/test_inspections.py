"""
Tests para endpoints de inspecciones.
"""
import pytest
from httpx import AsyncClient


@pytest.fixture
async def project_id(client: AsyncClient, auth_headers) -> int:
    """Create a test project and return its ID."""
    response = await client.post(
        "/api/v1/projects",
        headers=auth_headers,
        json={"name": "Test Project for Inspections"},
    )
    return response.json()["id"]


@pytest.mark.asyncio
async def test_create_inspection(client: AsyncClient, auth_headers, project_id):
    """Test inspection creation."""
    response = await client.post(
        "/api/v1/inspections",
        headers=auth_headers,
        json={
            "project_id": project_id,
            "capture_source": "dron",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["project_id"] == project_id
    assert data["capture_source"] == "dron"
    assert data["status"] == "pending"
    assert "id" in data


@pytest.mark.asyncio
async def test_create_inspection_mobile(client: AsyncClient, auth_headers, project_id):
    """Test inspection creation with mobile source."""
    response = await client.post(
        "/api/v1/inspections",
        headers=auth_headers,
        json={
            "project_id": project_id,
            "capture_source": "mobile",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["capture_source"] == "mobile"


@pytest.mark.asyncio
async def test_create_inspection_invalid_project(client: AsyncClient, auth_headers):
    """Test inspection creation with invalid project."""
    response = await client.post(
        "/api/v1/inspections",
        headers=auth_headers,
        json={
            "project_id": 999,
            "capture_source": "dron",
        },
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_inspections(client: AsyncClient, auth_headers, project_id):
    """Test listing inspections."""
    # Create inspections
    await client.post(
        "/api/v1/inspections",
        headers=auth_headers,
        json={"project_id": project_id, "capture_source": "dron"},
    )
    await client.post(
        "/api/v1/inspections",
        headers=auth_headers,
        json={"project_id": project_id, "capture_source": "mobile"},
    )

    # List inspections
    response = await client.get("/api/v1/inspections", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_list_inspections_by_project(client: AsyncClient, auth_headers, project_id):
    """Test listing inspections filtered by project."""
    # Create another project
    other_project_response = await client.post(
        "/api/v1/projects",
        headers=auth_headers,
        json={"name": "Other Project"},
    )
    other_project_id = other_project_response.json()["id"]

    # Create inspections for different projects
    await client.post(
        "/api/v1/inspections",
        headers=auth_headers,
        json={"project_id": project_id, "capture_source": "dron"},
    )
    await client.post(
        "/api/v1/inspections",
        headers=auth_headers,
        json={"project_id": other_project_id, "capture_source": "mobile"},
    )

    # List inspections for specific project
    response = await client.get(
        f"/api/v1/inspections?project_id={project_id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["project_id"] == project_id


@pytest.mark.asyncio
async def test_get_inspection(client: AsyncClient, auth_headers, project_id):
    """Test getting a specific inspection."""
    # Create an inspection
    create_response = await client.post(
        "/api/v1/inspections",
        headers=auth_headers,
        json={"project_id": project_id, "capture_source": "dron"},
    )
    inspection_id = create_response.json()["id"]

    # Get the inspection
    response = await client.get(
        f"/api/v1/inspections/{inspection_id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == inspection_id
    assert data["capture_source"] == "dron"


@pytest.mark.asyncio
async def test_get_inspection_status(client: AsyncClient, auth_headers, project_id):
    """Test getting inspection processing status."""
    # Create an inspection
    create_response = await client.post(
        "/api/v1/inspections",
        headers=auth_headers,
        json={"project_id": project_id, "capture_source": "dron"},
    )
    inspection_id = create_response.json()["id"]

    # Get status
    response = await client.get(
        f"/api/v1/inspections/{inspection_id}/status",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["inspection_id"] == inspection_id
    assert data["status"] == "pending"
    assert data["progress_percentage"] == 0


@pytest.mark.asyncio
async def test_get_nonexistent_inspection(client: AsyncClient, auth_headers):
    """Test getting a nonexistent inspection."""
    response = await client.get("/api/v1/inspections/999", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_trigger_processing(client: AsyncClient, auth_headers, project_id):
    """Test triggering inspection processing."""
    # Create an inspection
    create_response = await client.post(
        "/api/v1/inspections",
        headers=auth_headers,
        json={"project_id": project_id, "capture_source": "dron"},
    )
    inspection_id = create_response.json()["id"]

    # Trigger processing
    response = await client.post(
        f"/api/v1/inspections/{inspection_id}/process",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "processing started" in data["message"].lower()


@pytest.mark.asyncio
async def test_get_detections_empty(client: AsyncClient, auth_headers, project_id):
    """Test getting detections for an inspection with no detections."""
    # Create an inspection
    create_response = await client.post(
        "/api/v1/inspections",
        headers=auth_headers,
        json={"project_id": project_id, "capture_source": "dron"},
    )
    inspection_id = create_response.json()["id"]

    # Get detections
    response = await client.get(
        f"/api/v1/inspections/{inspection_id}/detections",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0


@pytest.mark.asyncio
async def test_get_metrics_empty(client: AsyncClient, auth_headers, project_id):
    """Test getting metrics for an inspection with no metrics."""
    # Create an inspection
    create_response = await client.post(
        "/api/v1/inspections",
        headers=auth_headers,
        json={"project_id": project_id, "capture_source": "dron"},
    )
    inspection_id = create_response.json()["id"]

    # Get metrics
    response = await client.get(
        f"/api/v1/inspections/{inspection_id}/metrics",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0
