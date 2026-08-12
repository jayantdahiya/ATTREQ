"""Focused regression tests for the BR-01 reliability patch."""

from __future__ import annotations

import json
import uuid
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest
from fastapi import HTTPException, UploadFile

from attreq_api.api.v1.endpoints import recommendations
from attreq_api.services.ai import groq_classifier
from attreq_api.services.ai.groq_classifier import (
    MAX_BACKOFF_SECONDS,
    MAX_RETRIES,
    GroqClassifierService,
)
from attreq_api.services.style_dna import style_dna_service


def _user(**overrides):
    values = {
        "id": uuid.uuid4(),
        "saved_latitude": 19.076,
        "saved_longitude": 72.8777,
        "saved_city": "Mumbai",
        "onboarding_completed": False,
        "onboarding_step": "style_dna_upload",
    }
    values.update(overrides)
    return SimpleNamespace(**values)


@pytest.mark.asyncio
async def test_weather_resolution_prefers_explicit_coordinates(monkeypatch):
    get_current = AsyncMock(return_value={"temperature": 28})
    get_by_city = AsyncMock()
    monkeypatch.setattr(recommendations.weather_service, "get_current_weather", get_current)
    monkeypatch.setattr(recommendations.weather_service, "get_weather_by_city", get_by_city)

    result = await recommendations._resolve_weather(_user(), 12.9716, 77.5946)

    assert result == {"temperature": 28}
    get_current.assert_awaited_once_with(12.9716, 77.5946)
    get_by_city.assert_not_awaited()


@pytest.mark.asyncio
async def test_weather_resolution_prefers_saved_coordinates_over_city(monkeypatch):
    get_current = AsyncMock(return_value={"temperature": 31})
    get_by_city = AsyncMock()
    monkeypatch.setattr(recommendations.weather_service, "get_current_weather", get_current)
    monkeypatch.setattr(recommendations.weather_service, "get_weather_by_city", get_by_city)

    result = await recommendations._resolve_weather(_user(), None, None)

    assert result == {"temperature": 31}
    get_current.assert_awaited_once_with(19.076, 72.8777)
    get_by_city.assert_not_awaited()


@pytest.mark.asyncio
async def test_weather_resolution_falls_back_to_saved_city(monkeypatch):
    get_current = AsyncMock()
    get_by_city = AsyncMock(return_value={"temperature": 26})
    monkeypatch.setattr(recommendations.weather_service, "get_current_weather", get_current)
    monkeypatch.setattr(recommendations.weather_service, "get_weather_by_city", get_by_city)

    result = await recommendations._resolve_weather(
        _user(saved_latitude=None, saved_longitude=None), None, None
    )

    assert result == {"temperature": 26}
    get_by_city.assert_awaited_once_with("Mumbai")
    get_current.assert_not_awaited()


@pytest.mark.asyncio
async def test_weather_resolution_rejects_user_without_location(monkeypatch):
    get_current = AsyncMock()
    get_by_city = AsyncMock()
    monkeypatch.setattr(recommendations.weather_service, "get_current_weather", get_current)
    monkeypatch.setattr(recommendations.weather_service, "get_weather_by_city", get_by_city)

    with pytest.raises(HTTPException) as exc_info:
        await recommendations._resolve_weather(
            _user(saved_latitude=None, saved_longitude=None, saved_city=None),
            None,
            None,
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == (
        "No location available. Please provide coordinates or set your location in profile."
    )
    get_current.assert_not_awaited()
    get_by_city.assert_not_awaited()


def _groq_response(
    status_code: int,
    *,
    headers: dict[str, str] | None = None,
) -> httpx.Response:
    return httpx.Response(
        status_code,
        headers=headers,
        json={"choices": [{"message": {"content": "{}"}}]},
        request=httpx.Request("POST", GroqClassifierService.BASE_URL),
    )


class _SequenceClient:
    def __init__(self, responses: list[httpx.Response]):
        self.responses = responses
        self.calls = 0

    async def post(self, *args, **kwargs) -> httpx.Response:
        del args, kwargs
        response = self.responses[self.calls]
        self.calls += 1
        return response


@pytest.mark.parametrize("status_code", [429, 502, 503, 504])
@pytest.mark.asyncio
async def test_groq_retries_only_documented_retryable_statuses(
    monkeypatch, status_code: int
):
    client = _SequenceClient([_groq_response(status_code), _groq_response(200)])
    sleep = AsyncMock()
    monkeypatch.setattr(groq_classifier.asyncio, "sleep", sleep)

    result = await GroqClassifierService()._post_with_retry(client, {}, {})

    assert result == {"choices": [{"message": {"content": "{}"}}]}
    assert client.calls == 2
    sleep.assert_awaited_once_with(1.5)


@pytest.mark.parametrize("status_code", [400, 401, 500])
@pytest.mark.asyncio
async def test_groq_does_not_retry_other_http_errors(monkeypatch, status_code: int):
    client = _SequenceClient([_groq_response(status_code)])
    sleep = AsyncMock()
    monkeypatch.setattr(groq_classifier.asyncio, "sleep", sleep)

    with pytest.raises(httpx.HTTPStatusError):
        await GroqClassifierService()._post_with_retry(client, {}, {})

    assert client.calls == 1
    sleep.assert_not_awaited()


@pytest.mark.asyncio
async def test_groq_stops_after_bounded_retry_budget(monkeypatch):
    client = _SequenceClient([_groq_response(503) for _ in range(MAX_RETRIES + 1)])
    sleep = AsyncMock()
    monkeypatch.setattr(groq_classifier.asyncio, "sleep", sleep)

    with pytest.raises(httpx.HTTPStatusError):
        await GroqClassifierService()._post_with_retry(client, {}, {})

    assert client.calls == MAX_RETRIES + 1
    assert [call.args[0] for call in sleep.await_args_list] == [1.5, 3.0, 6.0, 12.0]


@pytest.mark.asyncio
async def test_groq_caps_retry_after_and_falls_back_when_invalid(monkeypatch):
    client = _SequenceClient(
        [
            _groq_response(429, headers={"retry-after": "60"}),
            _groq_response(429, headers={"retry-after": "not-a-number"}),
            _groq_response(200),
        ]
    )
    sleep = AsyncMock()
    monkeypatch.setattr(groq_classifier.asyncio, "sleep", sleep)

    await GroqClassifierService()._post_with_retry(client, {}, {})

    assert [call.args[0] for call in sleep.await_args_list] == [MAX_BACKOFF_SECONDS, 3.0]


@pytest.mark.parametrize(
    ("model_name", "expected_reasoning_effort"),
    [
        ("qwen/qwen3.6-27b", "none"),
        ("openai/gpt-oss-120b", None),
        ("meta-llama/llama-4-scout-17b-16e-instruct", None),
    ],
)
def test_groq_reasoning_effort_is_only_sent_to_supported_model(
    model_name: str, expected_reasoning_effort: str | None
):
    service = GroqClassifierService()
    service.model_name = model_name

    payload = service._base_payload()

    assert payload.get("reasoning_effort") == expected_reasoning_effort


class _StyleDnaStorage:
    async def save_image_from_bytes(self, content, user_id, category, extension):
        del content, user_id
        return f"{category}/photo.{extension}", f"/uploads/{category}/photo.{extension}"


def _photos() -> list[UploadFile]:
    return [
        UploadFile(BytesIO(f"photo-{i}".encode()), filename=f"photo-{i}.jpg")
        for i in range(3)
    ]


async def _created_photo(**kwargs):
    return SimpleNamespace(**kwargs)


@pytest.mark.asyncio
async def test_style_dna_reports_provider_failure_separately(monkeypatch):
    request = httpx.Request("POST", GroqClassifierService.BASE_URL)
    provider_error = httpx.HTTPStatusError(
        "Service unavailable",
        request=request,
        response=httpx.Response(503, request=request),
    )
    classifier = SimpleNamespace(
        analyze_image=AsyncMock(side_effect=provider_error),
        analyze_text=AsyncMock(),
    )
    create_photo = AsyncMock(side_effect=_created_photo)
    monkeypatch.setattr(style_dna_service, "get_classifier", lambda: classifier)
    monkeypatch.setattr(style_dna_service, "get_storage", _StyleDnaStorage)
    monkeypatch.setattr(style_dna_service.style_dna_crud, "create_photo", create_photo)
    monkeypatch.setattr(style_dna_service.asyncio, "sleep", AsyncMock())

    with pytest.raises(HTTPException) as exc_info:
        await style_dna_service.process_style_photos(
            db=SimpleNamespace(), user=_user(), photo_files=_photos()
        )

    assert exc_info.value.status_code == 422
    assert exc_info.value.detail == (
        "Our photo analysis service is temporarily unavailable — "
        "please wait a minute and try again."
    )
    assert all(
        call.kwargs["quality_reason"]
        == "Photo analysis service temporarily unavailable"
        for call in create_photo.await_args_list
    )
    classifier.analyze_text.assert_not_awaited()


@pytest.mark.asyncio
async def test_style_dna_treats_malformed_provider_output_as_service_failure(monkeypatch):
    malformed_output = json.JSONDecodeError("Invalid provider JSON", "not-json", 0)
    classifier = SimpleNamespace(
        analyze_image=AsyncMock(side_effect=malformed_output),
        analyze_text=AsyncMock(),
    )
    create_photo = AsyncMock(side_effect=_created_photo)
    monkeypatch.setattr(style_dna_service, "get_classifier", lambda: classifier)
    monkeypatch.setattr(style_dna_service, "get_storage", _StyleDnaStorage)
    monkeypatch.setattr(style_dna_service.style_dna_crud, "create_photo", create_photo)
    monkeypatch.setattr(style_dna_service.asyncio, "sleep", AsyncMock())

    with pytest.raises(HTTPException) as exc_info:
        await style_dna_service.process_style_photos(
            db=SimpleNamespace(), user=_user(), photo_files=_photos()
        )

    assert exc_info.value.status_code == 422
    assert "temporarily unavailable" in exc_info.value.detail
    assert all(
        call.kwargs["quality_reason"]
        == "Photo analysis service temporarily unavailable"
        for call in create_photo.await_args_list
    )
    classifier.analyze_text.assert_not_awaited()


@pytest.mark.asyncio
async def test_style_dna_reports_unusable_photos_without_provider_message(monkeypatch):
    classifier = SimpleNamespace(
        analyze_image=AsyncMock(
            return_value={"usable": False, "quality_reason": "Outfit is too blurry"}
        ),
        analyze_text=AsyncMock(),
    )
    create_photo = AsyncMock(side_effect=_created_photo)
    monkeypatch.setattr(style_dna_service, "get_classifier", lambda: classifier)
    monkeypatch.setattr(style_dna_service, "get_storage", _StyleDnaStorage)
    monkeypatch.setattr(style_dna_service.style_dna_crud, "create_photo", create_photo)
    monkeypatch.setattr(style_dna_service.asyncio, "sleep", AsyncMock())

    with pytest.raises(HTTPException) as exc_info:
        await style_dna_service.process_style_photos(
            db=SimpleNamespace(), user=_user(), photo_files=_photos()
        )

    assert exc_info.value.status_code == 422
    assert "Please upload clearer outfit photos" in exc_info.value.detail
    assert "temporarily unavailable" not in exc_info.value.detail
    classifier.analyze_text.assert_not_awaited()
