"""
Script para inicializar la base de datos y crear datos iniciales.

Uso:
    python -m scripts.init_db
"""
import asyncio
import sys
from pathlib import Path

# Add the backend directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import get_settings
from app.core.database import engine, AsyncSessionLocal, Base
from app.models.project import User, Project
from app.api.v1.auth import get_password_hash


async def init_database():
    """Initialize database tables."""
    print("Creating database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables created successfully!")


async def create_admin_user():
    """Create default admin user if not exists."""
    from sqlalchemy import select

    settings = get_settings()
    async with AsyncSessionLocal() as db:
        # Check if admin exists
        result = await db.execute(
            select(User).where(User.email == "admin@se-peav.com")
        )
        if result.scalar_one_or_none():
            print("Admin user already exists.")
            return

        # Create admin user
        admin = User(
            email="admin@se-peav.com",
            hashed_password=get_password_hash("admin123"),
            full_name="Administrador",
            phone="+51999999999",
        )
        db.add(admin)
        await db.commit()
        print("Admin user created successfully!")
        print("Email: admin@se-peav.com")
        print("Password: admin123")


async def create_sample_project():
    """Create a sample project for testing."""
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        # Get admin user
        result = await db.execute(
            select(User).where(User.email == "admin@se-peav.com")
        )
        admin = result.scalar_one_or_none()
        if not admin:
            print("Admin user not found. Skipping sample project creation.")
            return

        # Check if sample project exists
        result = await db.execute(
            select(Project).where(Project.name == "Proyecto de Prueba")
        )
        if result.scalar_one_or_none():
            print("Sample project already exists.")
            return

        # Create sample project
        project = Project(
            owner_id=admin.id,
            name="Proyecto de Prueba",
            description="Proyecto de ejemplo para pruebas del sistema",
            address="Av. Arequipa 1234, Lima, Perú",
            latitude=-12.0464,
            longitude=-77.0428,
        )
        db.add(project)
        await db.commit()
        print("Sample project created successfully!")


async def main():
    """Main initialization function."""
    print("=" * 50)
    print("SE-PEAV Database Initialization")
    print("=" * 50)

    await init_database()
    await create_admin_user()
    await create_sample_project()

    print("=" * 50)
    print("Initialization complete!")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
