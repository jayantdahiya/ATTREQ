"""Storage backend protocol and shared image helpers.

Backends return ``(ref, stored_url)`` tuples:
- ``ref`` is the backend-native reference used to read the file back
  (absolute path for local disk, object key for S3).
- ``stored_url`` is the value persisted in the database (``/uploads/...``
  for local disk, the object key for S3). Object keys are converted to
  presigned URLs at response-serialization time via ``resolve_image_url``.
"""

import io
import uuid
from typing import Protocol

from fastapi import UploadFile
from PIL import Image

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}
SUBDIRECTORIES = ("originals", "processed", "thumbnails", "style-dna")

PIL_FORMATS = {"jpg": "JPEG", "jpeg": "JPEG", "png": "PNG"}
CONTENT_TYPES = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png"}


def get_file_extension(filename: str) -> str:
    """Extract the lowercase file extension, defaulting to jpg."""
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else "jpg"


def generate_filename(user_id: uuid.UUID | str, extension: str) -> str:
    """Generate a unique filename for an upload."""
    return f"{user_id}_{uuid.uuid4()}.{extension}"


def make_thumbnail_bytes(image_bytes: bytes, size: int = 300, extension: str = "jpg") -> bytes:
    """Resize image bytes to a square-bounded thumbnail, preserving aspect ratio.

    RGBA images are flattened onto a white background.

    Raises:
        ValueError: If the image cannot be processed
    """
    try:
        with Image.open(io.BytesIO(image_bytes)) as img:
            if img.mode == "RGBA":
                background = Image.new("RGB", img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[3])  # Use alpha channel as mask
                img = background

            img.thumbnail((size, size), Image.Resampling.LANCZOS)

            buffer = io.BytesIO()
            img.save(buffer, format=PIL_FORMATS.get(extension, "PNG"), quality=85, optimize=True)
            return buffer.getvalue()
    except Exception as e:
        raise ValueError(f"Failed to generate thumbnail: {str(e)}") from e


class StorageBackend(Protocol):
    """Interface implemented by local-disk and S3 storage backends."""

    async def save_upload_file(
        self, file: UploadFile, user_id: uuid.UUID, subdirectory: str = "originals"
    ) -> tuple[str, str]:
        """Save an uploaded file. Returns (ref, stored_url)."""
        ...

    async def save_image_from_bytes(
        self,
        image_bytes: bytes,
        user_id: uuid.UUID | str,
        subdirectory: str,
        extension: str = "png",
    ) -> tuple[str, str]:
        """Save image bytes. Returns (ref, stored_url)."""
        ...

    async def generate_thumbnail(
        self,
        image_bytes: bytes,
        user_id: uuid.UUID | str,
        size: int = 300,
        extension: str = "jpg",
    ) -> tuple[str, str]:
        """Create and save a thumbnail from image bytes. Returns (ref, stored_url)."""
        ...

    async def get_file_bytes(self, ref: str) -> bytes:
        """Read a stored file's content by its backend-native reference."""
        ...

    async def delete_file(self, ref: str) -> bool:
        """Delete a stored file. Returns True on success."""
        ...

    def get_file_url(self, ref: str) -> str:
        """Return a client-usable URL for a stored file."""
        ...
