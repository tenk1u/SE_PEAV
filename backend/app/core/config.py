from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    # API
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "SE-PEAV"
    VERSION: str = "2.0.0"
    DEBUG: bool = False

    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    ALGORITHM: str = "HS256"

    # Database (PostgreSQL)
    POSTGRES_USER: str = "se_peav"
    POSTGRES_PASSWORD: str = "se_peav_password"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "se_peav"

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def DATABASE_URL_SYNC(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # Celery
    CELERY_BROKER_URL: Optional[str] = None
    CELERY_RESULT_BACKEND: Optional[str] = None

    # Storage (MinIO/S3)
    S3_ENDPOINT: str = "localhost:9000"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"
    S3_BUCKET_NAME: str = "se-peav"
    S3_USE_SSL: bool = False

    # File limits
    MAX_UPLOAD_SIZE_MB: int = 500
    ALLOWED_VIDEO_EXTENSIONS: list[str] = [".mp4", ".avi", ".mov", ".mkv"]
    ALLOWED_IMAGE_EXTENSIONS: list[str] = [".jpg", ".jpeg", ".png"]

    # Processing
    FRAME_EXTRACTION_FPS: float = 0.5
    MAX_CONCURRENT_TASKS: int = 2

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()
