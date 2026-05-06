"""
Tests para endpoints de proyectos.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_project(client: AsyncClient, auth_headers):
    """Test project creation."""
    response = await client.post(
        "/api/v1/projects",
        headers=auth_headers,
        json={
            "name": "Mi Casa",
            "description": "Proyecto de prueba",
            "address": "Av. Arequipa 1234, Lima",
            "latitude": -12.0464,
            "longitude": -77.0428,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Mi Casa"
    assert data["address"] == "Av. Arequipa 1234, Lima"
    assert data["latitude"] == -12.0464
    assert "id" in data


@pytest.mark.asyncio
async def test_list_projects(client: AsyncClient, auth_headers):
    """Test listing projects."""
    # Create a project first
    await client.post(
        "/api/v1/projects",
        headers=auth_headers,
        json={"name": "Project 1"},
    )
    await client.post(
        "/api/v1/projects",
        headers=auth_headers,
        json={"name": "Project 2"},
    )

    # List projects
    response = await client.get("/api/v1/projects", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["name"] == "Project 1"
    assert data[1]["name"] == "Project 2"


@pytest.mark.asyncio
async def test_get_project(client: AsyncClient, auth_headers):
    """Test getting a specific project."""
    # Create a project
    create_response = await client.post(
        "/api/v1/projects",
        headers=auth_headers,
        json={"name": "Test Project", "description": "Test description"},
    )
    project_id = create_response.json()["id"]

    # Get the project
    response = await client.get(
        f"/api/v1/projects/{project_id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Project"
    assert data["description"] == "Test description"


@pytest.mark.asyncio
async def test_get_nonexistent_project(client: AsyncClient, auth_headers):
    """Test getting a nonexistent project."""
    response = await client.get("/api/v1/projects/999", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_project(client: AsyncClient, auth_headers):
    """Test updating a project."""
    # Create a project
    create_response = await client.post(
        "/api/v1/projects",
        headers=auth_headers,
        json={"name": "Old Name"},
    )
    project_id = create_response.json()["id"]

    # Update the project
    response = await client.patch(
        f"/api/v1/projects/{project_id}",
        headers=auth_headers,
        json={"name": "New Name", "description": "Updated description"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "New Name"
    assert data["description"] == "Updated description"


@pytest.mark.asyncio
async def test_delete_project(client: AsyncClient, auth_headers):
    """Test deleting a project."""
    # Create a project
    create_response = await client.post(
        "/api/v1/projects",
        headers=auth_headers,
        json={"name": "To Delete"},
    )
    project_id = create_response.json()["id"]

    # Delete the project
    response = await client.delete(
        f"/api/v1/projects/{project_id}",
        headers=auth_headers,
    )
    assert response.status_code == 204

    # Verify it's deleted
    response = await client.get(
        f"/api/v1/projects/{project_id}",
        headers=auth_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_project_not_found_other_user(client: AsyncClient, auth_headers, db_session):
    """Test that users cannot access other users' projects."""
    from app.models.project import User
    from app.api.v1.auth import get_password_hash

    # Create another user
    other_user = User(
        email="other@example.com",
        hashed_password=get_password_hash("otherpassword123"),
        full_name="Other User",
    )
    db_session.add(other_user)
    await db_session.commit()

    # Login as other user
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "other@example.com", "password": "otherpassword123"},
    )
    other_headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}

    # Create a project as test_user
    create_response = await client.post(
        "/api/v1/projects",
        headers=auth_headers,
        json={"name": "Private Project"},
    )
    project_id = create_response.json()["id"]

    # Try to access as other user
    response = await client.get(
        f"/api/v1/projects/{project_id}",
        headers=other_headers,
    )
    assert response.status_code == 404
