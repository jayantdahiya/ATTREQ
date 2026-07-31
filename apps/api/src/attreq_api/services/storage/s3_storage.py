"""S3-compatible storage backend (Cloudflare R2).

Images live in a private bucket and are served via presigned GET URLs
generated at response-serialization time. The database stores object keys,
never URLs.
"""

import asyncio
import logging
import uuid

import aioboto3
import boto3
from fastapi import UploadFile

from attreq_api.config.settings import settings
from attreq_api.services.storage.base import (
    ALLOWED_EXTENSIONS,
    CONTENT_TYPES,
    generate_filename,
    get_file_extension,
    make_thumbnail_bytes,
)

logger = logging.getLogger(__name__)

PRESIGNED_URL_EXPIRY_SECONDS = 86400  # 24 hours


class S3StorageService:
    """Storage backend for S3-compatible object stores (Cloudflare R2)."""

    def __init__(self):
        self.bucket = settings.s3_bucket
        self._client_kwargs = {
            "service_name": "s3",
            "endpoint_url": settings.s3_endpoint_url,
            "aws_access_key_id": settings.s3_access_key_id,
            "aws_secret_access_key": settings.s3_secret_access_key,
            "region_name": "auto",
        }
        self._session = aioboto3.Session()
        # Presigning is pure local computation (no network I/O), so a sync
        # boto3 client is safe to call from async request handlers.
        self._presign_client = boto3.client(**self._client_kwargs)

    async def save_upload_file(
        self, file: UploadFile, user_id: uuid.UUID, subdirectory: str = "originals"
    ) -> tuple[str, str]:
        extension = get_file_extension(file.filename or "image.jpg")
        if extension not in ALLOWED_EXTENSIONS:
            raise ValueError(f"Unsupported file type: {extension}")

        content = await file.read()
        return await self.save_image_from_bytes(content, user_id, subdirectory, extension)

    async def save_image_from_bytes(
        self,
        image_bytes: bytes,
        user_id: uuid.UUID | str,
        subdirectory: str,
        extension: str = "png",
    ) -> tuple[str, str]:
        key = f"{subdirectory}/{generate_filename(user_id, extension)}"

        async with self._session.client(**self._client_kwargs) as client:
            await client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=image_bytes,
                ContentType=CONTENT_TYPES.get(extension, "application/octet-stream"),
            )

        return key, key

    async def generate_thumbnail(
        self,
        image_bytes: bytes,
        user_id: uuid.UUID | str,
        size: int = 300,
        extension: str = "jpg",
    ) -> tuple[str, str]:
        thumbnail_bytes = await asyncio.to_thread(
            make_thumbnail_bytes, image_bytes, size, extension
        )
        return await self.save_image_from_bytes(thumbnail_bytes, user_id, "thumbnails", extension)

    async def get_file_bytes(self, ref: str) -> bytes:
        async with self._session.client(**self._client_kwargs) as client:
            response = await client.get_object(Bucket=self.bucket, Key=ref)
            return await response["Body"].read()

    async def delete_file(self, ref: str) -> bool:
        try:
            async with self._session.client(**self._client_kwargs) as client:
                await client.delete_object(Bucket=self.bucket, Key=ref)
            return True
        except Exception:
            logger.warning(f"Failed to delete object {ref}", exc_info=True)
            return False

    def get_file_url(self, ref: str) -> str:
        """Return a presigned GET URL (24 h expiry) for an object key."""
        return self._presign_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": ref},
            ExpiresIn=PRESIGNED_URL_EXPIRY_SECONDS,
        )
