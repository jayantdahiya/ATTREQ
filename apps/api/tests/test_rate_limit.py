"""Focused BR-03 tests for public/costly endpoint rate limiting."""

from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi import HTTPException
from redis.exceptions import ConnectionError
from starlette.requests import Request

from attreq_api.api.v1 import deps
from attreq_api.api.v1.endpoints import recommendations
from attreq_api.config.database import get_db
from attreq_api.config.settings import settings
from attreq_api.main import app
from attreq_api.services import rate_limit
from attreq_api.services.rate_limit import RateLimiter, RateLimitResult
from tests.conftest import build_user


class FakeRedis:
    """Small eval-compatible fake implementing the limiter script's semantics."""

    def __init__(self) -> None:
        self.counts: dict[str, int] = {}
        self.calls: list[tuple[str, int, int]] = []

    async def eval(self, script, number_of_keys, key, cost, window):
        assert "INCRBY" in script
        assert "EXPIRE" in script
        assert number_of_keys == 1
        cost = int(cost)
        window = int(window)
        self.calls.append((key, cost, window))
        self.counts[key] = self.counts.get(key, 0) + cost
        return [self.counts[key], window]


@pytest.mark.asyncio
async def test_limiter_allows_then_rejects_with_stable_retry_after(monkeypatch):
    fake_redis = FakeRedis()
    monkeypatch.setattr(settings, "rate_limit_enabled", True)
    monkeypatch.setattr(rate_limit.redis_cache, "client", fake_redis)

    limiter = RateLimiter()
    first = await limiter.consume(
        bucket="auth", subject="198.51.100.7", limit=2, window_seconds=60
    )
    second = await limiter.consume(
        bucket="auth", subject="198.51.100.7", limit=2, window_seconds=60
    )
    exceeded = await limiter.consume(
        bucket="auth", subject="198.51.100.7", limit=2, window_seconds=60
    )

    assert first.allowed is True
    assert second.allowed is True
    assert exceeded == RateLimitResult(
        allowed=False, limit=2, remaining=0, retry_after=60
    )
    with pytest.raises(HTTPException) as exc_info:
        rate_limit._raise_if_exceeded(exceeded)
    assert exc_info.value.status_code == 429
    assert exc_info.value.detail == rate_limit.RATE_LIMIT_DETAIL
    assert exc_info.value.headers == {"Retry-After": "60"}


@pytest.mark.asyncio
async def test_limiter_fails_open_and_logs_redis_outage(monkeypatch, caplog):
    class BrokenRedis:
        async def eval(self, *args):
            raise ConnectionError("Redis unavailable")

    monkeypatch.setattr(settings, "rate_limit_enabled", True)
    monkeypatch.setattr(rate_limit.redis_cache, "client", BrokenRedis())

    result = await RateLimiter().consume(
        bucket="wardrobe-images", subject=str(uuid4()), limit=20, window_seconds=3600
    )

    assert result.allowed is True
    assert result.enforced is False
    assert "Rate limiter Redis failure; allowing request" in caplog.text
    assert "Redis unavailable" not in caplog.text


def _request(*, peer: str, headers: list[tuple[bytes, bytes]]) -> Request:
    return Request(
        {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "method": "POST",
            "scheme": "https",
            "path": "/api/v1/auth/login",
            "raw_path": b"/api/v1/auth/login",
            "query_string": b"",
            "headers": headers,
            "client": (peer, 54321),
            "server": ("api.example.test", 443),
        }
    )


def test_client_key_ignores_untrusted_forwarded_headers(monkeypatch):
    request = _request(
        peer="203.0.113.9",
        headers=[
            (b"cf-connecting-ip", b"198.51.100.8"),
            (b"x-forwarded-for", b"198.51.100.10"),
        ],
    )
    monkeypatch.setattr(settings, "rate_limit_trust_proxy_headers", False)
    assert rate_limit.get_client_ip(request) == "203.0.113.9"

    monkeypatch.setattr(settings, "rate_limit_trust_proxy_headers", True)
    monkeypatch.setattr(settings, "rate_limit_trusted_proxy_cidrs", ["10.42.0.0/24"])
    assert rate_limit.get_client_ip(request) == "203.0.113.9"


def test_client_key_accepts_cloudflare_header_only_from_allowlisted_proxy(monkeypatch):
    request = _request(
        peer="10.42.0.4",
        headers=[(b"cf-connecting-ip", b"2001:db8::17")],
    )
    monkeypatch.setattr(settings, "rate_limit_trust_proxy_headers", True)
    monkeypatch.setattr(settings, "rate_limit_trusted_proxy_cidrs", ["10.42.0.0/24"])
    assert rate_limit.get_client_ip(request) == "2001:db8::17"


@pytest.mark.asyncio
async def test_login_endpoint_returns_stable_429_before_authentication(monkeypatch, client):
    async def exceeded(**kwargs):
        return RateLimitResult(False, 10, 0, 37)

    monkeypatch.setattr(rate_limit.rate_limiter, "consume", exceeded)

    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "test@example.com", "password": "Password123"},
    )

    assert response.status_code == 429
    assert response.json() == {"detail": rate_limit.RATE_LIMIT_DETAIL}
    assert response.headers["retry-after"] == "37"


@pytest.mark.asyncio
async def test_batch_upload_charges_actual_image_count(monkeypatch, client, dummy_db):
    user = build_user()
    calls: list[dict] = []

    async def override_get_db():
        yield dummy_db

    async def capture_limit(**kwargs):
        calls.append(kwargs)
        raise HTTPException(
            status_code=429,
            detail=rate_limit.RATE_LIMIT_DETAIL,
            headers={"Retry-After": "3600"},
        )

    from attreq_api.api.v1.endpoints import wardrobe

    monkeypatch.setattr(wardrobe, "enforce_user_rate_limit", capture_limit)
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[deps.get_current_active_user] = lambda: user
    try:
        response = await client.post(
            "/api/v1/wardrobe/batch-upload",
            files=[
                ("files", (f"item-{index}.jpg", b"image", "image/jpeg"))
                for index in range(3)
            ],
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 429
    assert calls == [
        {
            "bucket": "wardrobe-images",
            "user_id": user.id,
            "limit": settings.rate_limit_wardrobe_images,
            "window_seconds": settings.rate_limit_wardrobe_window_seconds,
            "cost": 3,
        }
    ]


@pytest.mark.asyncio
async def test_recommendation_cache_reads_are_free_but_force_refresh_is_charged(
    monkeypatch,
):
    user_id = uuid4()
    calls: list[dict] = []

    async def capture_limit(**kwargs):
        calls.append(kwargs)

    monkeypatch.setattr(recommendations, "enforce_user_rate_limit", capture_limit)

    await recommendations._enforce_force_refresh_rate_limit(False, user_id)
    assert calls == []

    await recommendations._enforce_force_refresh_rate_limit(True, user_id)
    assert calls == [
        {
            "bucket": "recommendation-refreshes",
            "user_id": user_id,
            "limit": settings.rate_limit_recommendation_refreshes,
            "window_seconds": settings.rate_limit_recommendation_window_seconds,
        }
    ]
