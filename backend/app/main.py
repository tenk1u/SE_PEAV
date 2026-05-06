from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import get_settings
from app.core.database import init_db
from app.api.v1 import auth, projects, inspections, reports, upload


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    yield
    # Shutdown


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix=settings.API_V1_PREFIX, tags=["auth"])
app.include_router(projects.router, prefix=settings.API_V1_PREFIX, tags=["projects"])
app.include_router(inspections.router, prefix=settings.API_V1_PREFIX, tags=["inspections"])
app.include_router(reports.router, prefix=settings.API_V1_PREFIX, tags=["reports"])
app.include_router(upload.router, prefix=settings.API_V1_PREFIX, tags=["upload"])


@app.get("/")
async def root():
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
