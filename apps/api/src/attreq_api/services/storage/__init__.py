"""Storage backend factory and image-URL resolution."""

from attreq_api.config.settings import settings
from attreq_api.services.storage.base import StorageBackend

_storage: StorageBackend | None = None


def get_storage() -> StorageBackend:
    """Return the storage backend selected by STORAGE_BACKEND (cached singleton)."""
    global _storage
    if _storage is None:
        if settings.storage_backend == "s3":
            from attreq_api.services.storage.s3_storage import S3StorageService

            _storage = S3StorageService()
        else:
            from attreq_api.services.storage.file_handler import FileStorageService

            _storage = FileStorageService()
    return _storage


def resolve_image_url(value: str | None) -> str | None:
    """Convert a stored image reference into a client-usable URL.

    Local values (``/uploads/...``) and absolute URLs pass through unchanged;
    S3 object keys are presigned (24 h expiry). Apply this wherever image URLs
    enter API responses — never persist its output.
    """
    if not value or value.startswith("/uploads/") or value.startswith("http"):
        return value
    if settings.storage_backend == "s3":
        return get_storage().get_file_url(value)
    return value
