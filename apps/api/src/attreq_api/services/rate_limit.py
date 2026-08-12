"""Redis-backed fixed-window limiting for public and costly endpoints.

Forwarded client-IP headers are ignored unless both proxy-header trust is
enabled and the immediate peer belongs to an explicit IP/CIDR allowlist. This
is important because ``X-Forwarded-For`` and ``CF-Connecting-IP`` are otherwise
client-controlled strings on a directly reachable service.
"""

from __future__ import annotations

import hashlib
import ipaddress
import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from fastapi import HTTPException, Request, status  # noqa: TC002 -- FastAPI inspects it at runtime
from redis.exceptions import RedisError

from attreq_api.config.settings import settings
from attreq_api.services.cache.redis_client import redis_cache

if TYPE_CHECKING:
    from uuid import UUID

logger = logging.getLogger(__name__)

RATE_LIMIT_DETAIL = "Rate limit exceeded. Try again later."

# INCRBY and expiry establishment/repair must be one Redis operation. The
# script also returns the current TTL so Retry-After reflects the actual reset.
_CONSUME_SCRIPT = """
local current = redis.call('INCRBY', KEYS[1], ARGV[1])
local ttl = redis.call('TTL', KEYS[1])
if current == tonumber(ARGV[1]) or ttl < 0 then
    redis.call('EXPIRE', KEYS[1], ARGV[2])
    ttl = tonumber(ARGV[2])
end
return {current, ttl}
"""


@dataclass(frozen=True)
class RateLimitResult:
    """Outcome of consuming capacity from one fixed-window bucket."""

    allowed: bool
    limit: int
    remaining: int
    retry_after: int
    enforced: bool = True


class RateLimiter:
    """Consume weighted capacity using the application's async Redis client."""

    async def consume(
        self,
        *,
        bucket: str,
        subject: str,
        limit: int,
        window_seconds: int,
        cost: int = 1,
    ) -> RateLimitResult:
        if cost < 1:
            raise ValueError("Rate-limit cost must be at least 1")
        if not settings.rate_limit_enabled:
            return RateLimitResult(True, limit, limit, 0, enforced=False)

        client = redis_cache.client
        if client is None:
            logger.warning(
                "Rate limiter unavailable; allowing request (bucket=%s, reason=no Redis client)",
                bucket,
            )
            return RateLimitResult(True, limit, limit, 0, enforced=False)

        key = _redis_key(bucket, subject)
        try:
            current, ttl = await client.eval(
                _CONSUME_SCRIPT,
                1,
                key,
                cost,
                window_seconds,
            )
        except RedisError as exc:
            logger.warning(
                "Rate limiter Redis failure; allowing request (bucket=%s, error=%s)",
                bucket,
                type(exc).__name__,
            )
            return RateLimitResult(True, limit, limit, 0, enforced=False)

        current = int(current)
        retry_after = max(1, int(ttl))
        return RateLimitResult(
            allowed=current <= limit,
            limit=limit,
            remaining=max(0, limit - current),
            retry_after=retry_after,
        )


rate_limiter = RateLimiter()


def get_client_ip(request: Request) -> str:
    """Return a validated client IP, trusting proxy headers only by policy."""
    peer = request.client.host if request.client else None
    if peer and _is_trusted_proxy(peer):
        forwarded = request.headers.get("cf-connecting-ip")
        if not forwarded:
            # The left-most XFF value is the originating client when the only
            # trusted immediate proxy is responsible for constructing the header.
            forwarded = request.headers.get("x-forwarded-for", "").split(",", 1)[0].strip()
        parsed = _parse_ip(forwarded)
        if parsed:
            return parsed

    return _parse_ip(peer) or "unknown"


async def enforce_client_rate_limit(request: Request) -> None:
    """FastAPI dependency for the shared login/register client-IP budget."""
    result = await rate_limiter.consume(
        bucket="auth",
        subject=get_client_ip(request),
        limit=settings.rate_limit_auth_attempts,
        window_seconds=settings.rate_limit_auth_window_seconds,
    )
    _raise_if_exceeded(result)


async def enforce_user_rate_limit(
    *,
    bucket: str,
    user_id: UUID,
    limit: int,
    window_seconds: int,
    cost: int = 1,
) -> None:
    """Consume capacity for an authenticated user or raise a stable 429."""
    result = await rate_limiter.consume(
        bucket=bucket,
        subject=str(user_id),
        limit=limit,
        window_seconds=window_seconds,
        cost=cost,
    )
    _raise_if_exceeded(result)


def _raise_if_exceeded(result: RateLimitResult) -> None:
    if not result.allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=RATE_LIMIT_DETAIL,
            headers={"Retry-After": str(result.retry_after)},
        )


def _redis_key(bucket: str, subject: str) -> str:
    # Hash subjects so raw client IPs and user IDs are not exposed in Redis key
    # listings or logs. Bucket names are internal constants, never user input.
    digest = hashlib.sha256(subject.encode("utf-8")).hexdigest()
    return f"attreq:rate-limit:{bucket}:{digest}"


def _is_trusted_proxy(peer: str) -> bool:
    if not settings.rate_limit_trust_proxy_headers:
        return False
    parsed_peer = _parse_ip(peer)
    if not parsed_peer:
        return False
    address = ipaddress.ip_address(parsed_peer)
    return any(
        address in ipaddress.ip_network(cidr, strict=False)
        for cidr in settings.rate_limit_trusted_proxy_cidrs
    )


def _parse_ip(value: str | None) -> str | None:
    if not value:
        return None
    try:
        return str(ipaddress.ip_address(value.strip()))
    except ValueError:
        return None
