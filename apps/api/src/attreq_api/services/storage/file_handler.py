"""Local-disk storage backend for handling uploads and file management."""

import asyncio
import os
import uuid
from pathlib import Path

import aiofiles
from fastapi import UploadFile

from attreq_api.config.settings import settings
from attreq_api.services.storage.base import (
    ALLOWED_EXTENSIONS,
    SUBDIRECTORIES,
    generate_filename,
    get_file_extension,
    make_thumbnail_bytes,
)


class FileStorageService:
    """Storage backend writing to the local filesystem under settings.upload_dir."""

    def __init__(self):
        """Initialize file storage service."""
        self.base_dir = Path(settings.upload_dir)
        self._dirs = {subdirectory: self.base_dir / subdirectory for subdirectory in SUBDIRECTORIES}

        # Create directories if they don't exist
        for directory in self._dirs.values():
            directory.mkdir(parents=True, exist_ok=True)

    def _target_dir(self, subdirectory: str) -> Path:
        if subdirectory not in self._dirs:
            raise ValueError(f"Invalid subdirectory: {subdirectory}")
        return self._dirs[subdirectory]

    async def save_upload_file(
        self, file: UploadFile, user_id: uuid.UUID, subdirectory: str = "originals"
    ) -> tuple[str, str]:
        """Save an uploaded file to storage.

        Returns:
            Tuple of (file_path, file_url)

        Raises:
            ValueError: If file type is not supported
        """
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
        """Save image bytes to storage.

        Returns:
            Tuple of (file_path, file_url)
        """
        filename = generate_filename(user_id, extension)
        file_path = self._target_dir(subdirectory) / filename

        async with aiofiles.open(file_path, "wb") as buffer:
            await buffer.write(image_bytes)

        return str(file_path), f"/uploads/{subdirectory}/{filename}"

    async def generate_thumbnail(
        self,
        image_bytes: bytes,
        user_id: uuid.UUID | str,
        size: int = 300,
        extension: str = "jpg",
    ) -> tuple[str, str]:
        """Generate and save a thumbnail from image bytes.

        Returns:
            Tuple of (thumbnail_path, thumbnail_url)

        Raises:
            ValueError: If image cannot be processed
        """
        thumbnail_bytes = await asyncio.to_thread(
            make_thumbnail_bytes, image_bytes, size, extension
        )
        return await self.save_image_from_bytes(thumbnail_bytes, user_id, "thumbnails", extension)

    async def get_file_bytes(self, ref: str) -> bytes:
        """Read a stored file's content by its path."""
        async with aiofiles.open(ref, "rb") as f:
            return await f.read()

    async def delete_file(self, ref: str) -> bool:
        """Delete a file from storage.

        Returns:
            True if file was deleted, False otherwise
        """

        def _delete() -> bool:
            if os.path.exists(ref):
                os.remove(ref)
                return True
            return False

        try:
            return await asyncio.to_thread(_delete)
        except Exception:
            return False

    def get_file_url(self, ref: str) -> str:
        """Generate a /uploads/... URL for a local file path."""
        path = Path(ref)

        parts = path.parts
        for subdirectory in SUBDIRECTORIES:
            if subdirectory in parts:
                idx = parts.index(subdirectory)
                return f"/uploads/{subdirectory}/{parts[idx + 1]}"

        # Fallback
        return f"/uploads/{path.name}"
