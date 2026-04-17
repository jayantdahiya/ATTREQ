"""File storage service for handling uploads and file management."""

import os
import uuid
from pathlib import Path

import aiofiles
from fastapi import UploadFile
from PIL import Image

from attreq_api.config.settings import settings


class FileStorageService:
    """Service for managing file uploads and storage."""

    def __init__(self):
        """Initialize file storage service."""
        self.base_dir = Path(settings.upload_dir)
        self.originals_dir = self.base_dir / "originals"
        self.processed_dir = self.base_dir / "processed"
        self.thumbnails_dir = self.base_dir / "thumbnails"

        # Create directories if they don't exist
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Ensure all required directories exist."""
        for directory in [self.originals_dir, self.processed_dir, self.thumbnails_dir]:
            directory.mkdir(parents=True, exist_ok=True)

    def _generate_filename(self, user_id: uuid.UUID, extension: str) -> str:
        """Generate a unique filename for the upload.

        Args:
            user_id: UUID of the user
            extension: File extension (e.g., 'jpg', 'png')

        Returns:
            Generated filename
        """
        unique_id = uuid.uuid4()
        return f"{user_id}_{unique_id}.{extension}"

    def _get_file_extension(self, filename: str) -> str:
        """Extract file extension from filename.

        Args:
            filename: Original filename

        Returns:
            File extension without dot
        """
        return filename.rsplit(".", 1)[-1].lower() if "." in filename else "jpg"

    async def save_upload_file(
        self, file: UploadFile, user_id: uuid.UUID, subdirectory: str = "originals"
    ) -> tuple[str, str]:
        """Save an uploaded file to storage.

        Args:
            file: Uploaded file from FastAPI
            user_id: UUID of the user uploading the file
            subdirectory: Target subdirectory (originals, processed, thumbnails)

        Returns:
            Tuple of (file_path, file_url)

        Raises:
            ValueError: If file type is not supported
        """
        # Get file extension
        extension = self._get_file_extension(file.filename or "image.jpg")

        # Validate file extension
        if extension not in ["jpg", "jpeg", "png"]:
            raise ValueError(f"Unsupported file type: {extension}")

        # Generate unique filename
        filename = self._generate_filename(user_id, extension)

        # Determine target directory
        if subdirectory == "originals":
            target_dir = self.originals_dir
        elif subdirectory == "processed":
            target_dir = self.processed_dir
        elif subdirectory == "thumbnails":
            target_dir = self.thumbnails_dir
        else:
            raise ValueError(f"Invalid subdirectory: {subdirectory}")

        # Full file path
        file_path = target_dir / filename

        # Save file using async file I/O
        content = await file.read()
        async with aiofiles.open(file_path, "wb") as buffer:
            await buffer.write(content)

        # Generate URL (relative path for now)
        file_url = f"/uploads/{subdirectory}/{filename}"

        return str(file_path), file_url

    def save_image_from_bytes(
        self, image_bytes: bytes, user_id: uuid.UUID, subdirectory: str, extension: str = "png"
    ) -> tuple[str, str]:
        """Save image bytes to storage.

        Args:
            image_bytes: Image data as bytes
            user_id: UUID of the user
            subdirectory: Target subdirectory
            extension: File extension

        Returns:
            Tuple of (file_path, file_url)
        """
        # Generate unique filename
        filename = self._generate_filename(user_id, extension)

        # Determine target directory
        if subdirectory == "originals":
            target_dir = self.originals_dir
        elif subdirectory == "processed":
            target_dir = self.processed_dir
        elif subdirectory == "thumbnails":
            target_dir = self.thumbnails_dir
        else:
            raise ValueError(f"Invalid subdirectory: {subdirectory}")

        # Full file path
        file_path = target_dir / filename

        # Save file
        with open(file_path, "wb") as buffer:
            buffer.write(image_bytes)

        # Generate URL
        file_url = f"/uploads/{subdirectory}/{filename}"

        return str(file_path), file_url

    def generate_thumbnail(
        self, source_path: str, user_id: uuid.UUID, size: int = 300
    ) -> tuple[str, str]:
        """Generate a thumbnail from an image.

        Args:
            source_path: Path to the source image
            user_id: UUID of the user
            size: Thumbnail size (square)

        Returns:
            Tuple of (thumbnail_path, thumbnail_url)

        Raises:
            FileNotFoundError: If source image doesn't exist
            ValueError: If image cannot be processed
        """
        if not os.path.exists(source_path):
            raise FileNotFoundError(f"Source image not found: {source_path}")

        try:
            # Open and resize image
            with Image.open(source_path) as img:
                # Convert RGBA to RGB if necessary
                if img.mode == "RGBA":
                    # Create white background
                    background = Image.new("RGB", img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[3])  # Use alpha channel as mask
                    img = background

                # Calculate resize dimensions maintaining aspect ratio
                img.thumbnail((size, size), Image.Resampling.LANCZOS)

                # Generate thumbnail filename
                extension = Path(source_path).suffix[1:]  # Remove dot
                filename = self._generate_filename(user_id, extension)
                thumbnail_path = self.thumbnails_dir / filename

                # Save thumbnail
                img.save(thumbnail_path, quality=85, optimize=True)

                # Generate URL
                thumbnail_url = f"/uploads/thumbnails/{filename}"

                return str(thumbnail_path), thumbnail_url

        except Exception as e:
            raise ValueError(f"Failed to generate thumbnail: {str(e)}") from e

    def delete_file(self, file_path: str) -> bool:
        """Delete a file from storage.

        Args:
            file_path: Path to the file to delete

        Returns:
            True if file was deleted, False otherwise
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception:
            return False

    def get_file_url(self, file_path: str) -> str:
        """Generate a URL for a file.

        Args:
            file_path: Full path to the file

        Returns:
            URL path for the file
        """
        # Extract relative path from uploads directory
        path = Path(file_path)

        # Find the subdirectory and filename
        parts = path.parts
        if "originals" in parts:
            idx = parts.index("originals")
            return f"/uploads/originals/{parts[idx + 1]}"
        if "processed" in parts:
            idx = parts.index("processed")
            return f"/uploads/processed/{parts[idx + 1]}"
        if "thumbnails" in parts:
            idx = parts.index("thumbnails")
            return f"/uploads/thumbnails/{parts[idx + 1]}"

        # Fallback
        return f"/uploads/{path.name}"


# Global instance
file_storage = FileStorageService()
