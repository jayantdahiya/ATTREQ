"""Redis cache service for ATTREQ backend."""

import json
import logging
from typing import Any

import redis.asyncio as redis

from app.core.config import settings

logger = logging.getLogger(__name__)


class RedisCacheService:
    """Service for managing Redis cache operations."""

    def __init__(self):
        """Initialize Redis client."""
        self.client: redis.Redis | None = None
        self._connect()

    def _connect(self) -> None:
        """Connect to Redis instance."""
        try:
            # Create Redis client with connection pooling
            self.client = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                password=settings.redis_password if settings.redis_password else None,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_keepalive=True,
            )
            logger.info(f"Redis client configured for {settings.redis_host}:{settings.redis_port}")
        except Exception as e:
            logger.error(f"Failed to configure Redis client: {str(e)}")
            self.client = None

    async def is_connected(self) -> bool:
        """Check if Redis client is connected.

        Returns:
            True if connected, False otherwise
        """
        if not self.client:
            return False

        try:
            await self.client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis connection check failed: {str(e)}")
            return False

    async def get(self, key: str) -> Any | None:
        """Retrieve a value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value (deserialized from JSON) or None if not found
        """
        if not self.client:
            logger.warning("Redis client not available, skipping cache get")
            return None

        try:
            value = await self.client.get(key)
            if value:
                # Deserialize JSON
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Failed to get cache key '{key}': {str(e)}")
            return None

    async def set(self, key: str, value: Any, ttl: int | None = None) -> bool:
        """Store a value in cache.

        Args:
            key: Cache key
            value: Value to cache (will be serialized to JSON)
            ttl: Time to live in seconds (optional)

        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            logger.warning("Redis client not available, skipping cache set")
            return False

        try:
            # Serialize to JSON
            serialized = json.dumps(value)

            if ttl:
                await self.client.setex(key, ttl, serialized)
            else:
                await self.client.set(key, serialized)

            logger.debug(f"Cached key '{key}' with TTL {ttl}s")
            return True
        except Exception as e:
            logger.error(f"Failed to set cache key '{key}': {str(e)}")
            return False

    async def delete(self, key: str) -> bool:
        """Remove a value from cache.

        Args:
            key: Cache key

        Returns:
            True if key was deleted, False otherwise
        """
        if not self.client:
            logger.warning("Redis client not available, skipping cache delete")
            return False

        try:
            result = await self.client.delete(key)
            logger.debug(f"Deleted cache key '{key}'")
            return result > 0
        except Exception as e:
            logger.error(f"Failed to delete cache key '{key}': {str(e)}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if a key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if key exists, False otherwise
        """
        if not self.client:
            logger.warning("Redis client not available, skipping cache exists check")
            return False

        try:
            result = await self.client.exists(key)
            return result > 0
        except Exception as e:
            logger.error(f"Failed to check cache key '{key}': {str(e)}")
            return False

    async def close(self) -> None:
        """Close Redis client connection."""
        if self.client:
            await self.client.aclose()
            logger.info("Redis connection closed")


# Global instance
redis_cache = RedisCacheService()

