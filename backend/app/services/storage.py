import boto3
from fastapi import UploadFile
from typing import Optional
import uuid
from datetime import datetime

from app.core.config import get_settings

settings = get_settings()

# Initialize S3 client
s3_client = boto3.client(
    "s3",
    endpoint_url=f"http://{settings.S3_ENDPOINT}" if not settings.S3_USE_SSL else f"https://{settings.S3_ENDPOINT}",
    aws_access_key_id=settings.S3_ACCESS_KEY,
    aws_secret_access_key=settings.S3_SECRET_KEY,
)


async def ensure_bucket():
    """Ensure the bucket exists."""
    try:
        s3_client.head_bucket(Bucket=settings.S3_BUCKET_NAME)
    except Exception:
        s3_client.create_bucket(Bucket=settings.S3_BUCKET_NAME)


async def upload_file(file: UploadFile, path: str) -> dict:
    """Upload a file to S3/MinIO."""
    await ensure_bucket()

    # Generate unique filename
    file_ext = path.split(".")[-1]
    unique_filename = f"{path.rsplit('.', 1)[0]}_{uuid.uuid4().hex[:8]}.{file_ext}"

    # Upload file
    content = await file.read()
    s3_client.put_object(
        Bucket=settings.S3_BUCKET_NAME,
        Key=unique_filename,
        Body=content,
        ContentType=file.content_type,
    )

    return {
        "file_path": unique_filename,
        "file_size": len(content),
        "content_type": file.content_type,
        "upload_id": str(uuid.uuid4()),
    }


async def upload_bytes(content: bytes, path: str, content_type: str) -> dict:
    """Upload bytes to S3/MinIO."""
    await ensure_bucket()

    s3_client.put_object(
        Bucket=settings.S3_BUCKET_NAME,
        Key=path,
        Body=content,
        ContentType=content_type,
    )

    return {
        "file_path": path,
        "file_size": len(content),
        "content_type": content_type,
    }


async def get_presigned_url(path: str, expires_in: int = 3600) -> str:
    """Generate a presigned URL for a file."""
    try:
        url = s3_client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": settings.S3_BUCKET_NAME,
                "Key": path,
            },
            ExpiresIn=expires_in,
        )
        return url
    except Exception:
        return None


async def download_file(path: str) -> bytes:
    """Download a file from S3/MinIO."""
    response = s3_client.get_object(
        Bucket=settings.S3_BUCKET_NAME,
        Key=path,
    )
    return response["Body"].read()


async def delete_file(path: str) -> bool:
    """Delete a file from S3/MinIO."""
    try:
        s3_client.delete_object(
            Bucket=settings.S3_BUCKET_NAME,
            Key=path,
        )
        return True
    except Exception:
        return False
