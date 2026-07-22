"""Tests for services/ai/fashion_embeddings.py (RI-6).

This sandbox genuinely does not have torch/transformers installed (see the
top-level RI-6 report: EMBEDDINGS_ENABLED stays False here, and the real
model was never exercised). Two kinds of coverage follow from that:

1. Tests that rely on the REAL (non-mocked) absence of torch/transformers to
   verify the "never raises" soft-fail contract — `_ensure_loaded` genuinely
   fails to import, and every public method degrades to `None`/`[]`/`False`
   rather than raising. This is honest coverage of the fallback path, not a
   simulation.
2. One test that fakes `torch`/`transformers` via `sys.modules` injection
   (never a real model) to exercise the "model loaded successfully" branch
   of `embed_image` end-to-end, asserting the output is unit-norm — this is
   the literal test the milestone plan asks for, done without requiring the
   real (heavy) dependencies to be installed.

Also asserts `fashion_embeddings.py` does not import torch/transformers at
module level — collection-time import must stay free of both.
"""

from __future__ import annotations

import ast
import contextlib
import sys
import types
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

from attreq_api.services.ai.fashion_embeddings import FashionEmbeddingsService

if TYPE_CHECKING:
    import pytest


def test_module_has_no_top_level_torch_or_transformers_import():
    """AST-based static check: `import torch` / `from transformers import ...`
    must only appear inside function bodies, never at module scope — this is
    what makes pytest collection safe without torch installed."""
    module_path = (
        Path(__file__).resolve().parent.parent
        / "src"
        / "attreq_api"
        / "services"
        / "ai"
        / "fashion_embeddings.py"
    )
    tree = ast.parse(module_path.read_text())

    top_level_imports = {
        alias.name
        for node in tree.body
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        node.module
        for node in tree.body
        if isinstance(node, ast.ImportFrom)
    }

    assert "torch" not in top_level_imports
    assert "transformers" not in top_level_imports


def test_is_available_false_and_load_failed_cached_when_model_cannot_load():
    """In this sandbox torch/transformers are genuinely not installed, so
    `_ensure_loaded` fails for real — `is_available()` returns False and
    stays False (cached `_load_failed`) without retrying every call."""
    service = FashionEmbeddingsService()

    assert service.is_available() is False
    assert service._load_failed is True
    assert service._model is None

    # Second call must short-circuit on `_load_failed`, not attempt to reload.
    assert service.is_available() is False


def test_embed_image_missing_file_returns_none_without_loading():
    service = FashionEmbeddingsService()
    result = service.embed_image("/nonexistent/path/does-not-exist.png")
    assert result is None
    # Missing-file check happens before `_ensure_loaded` — model was never touched.
    assert service._model is None


def test_embed_image_returns_none_when_model_load_fails(tmp_path):
    from PIL import Image

    image_path = tmp_path / "item.png"
    Image.new("RGB", (16, 16), color=(10, 20, 30)).save(image_path)

    service = FashionEmbeddingsService()
    assert service.embed_image(str(image_path)) is None


def test_embed_texts_empty_list_returns_empty_without_loading():
    service = FashionEmbeddingsService()
    assert service.embed_texts([]) == []
    assert service._model is None


def test_embed_texts_returns_none_when_model_load_fails():
    service = FashionEmbeddingsService()
    assert service.embed_texts(["a photo of a shirt"]) is None


def test_normalize_produces_unit_vector():
    vec = FashionEmbeddingsService._normalize([3.0, 4.0])
    assert np.isclose(np.linalg.norm(vec), 1.0)


def test_normalize_zero_vector_returns_zero_vector_without_dividing_by_zero():
    vec = FashionEmbeddingsService._normalize([0.0, 0.0, 0.0])
    assert list(vec) == [0.0, 0.0, 0.0]


# ---------------------------------------------------------------------------
# Fake torch/transformers — exercises the "model loaded" branch of
# embed_image end-to-end without requiring the real (heavy) packages.
# ---------------------------------------------------------------------------


class _FakeTensor:
    """Minimal stand-in for a torch.Tensor: only the subset of the API
    fashion_embeddings.py actually calls (`[]`, `.cpu()`, `.numpy()`)."""

    def __init__(self, arr: np.ndarray):
        self._arr = np.asarray(arr, dtype=float)

    def __getitem__(self, idx):
        return _FakeTensor(self._arr[idx])

    def __iter__(self):
        return iter(_FakeTensor(row) for row in self._arr)

    def cpu(self):
        return self

    def numpy(self):
        return self._arr


class _FakeBatchInputs(dict):
    def to(self, device):
        return self


class _FakeProcessor:
    def __call__(self, images=None, text=None, return_tensors=None, padding=None):
        n = 1 if images is not None else len(text or [])
        return _FakeBatchInputs(_n=n)

    @classmethod
    def from_pretrained(cls, name):
        return cls()


class _FakeModel:
    @classmethod
    def from_pretrained(cls, name):
        return cls()

    def to(self, device):
        return self

    def eval(self):
        return self

    def get_image_features(self, **kwargs):
        return _FakeTensor(np.array([[3.0, 4.0] + [0.0] * 510]))

    def get_text_features(self, **kwargs):
        n = kwargs.get("_n", 1)
        return _FakeTensor(np.tile(np.array([[1.0, 1.0] + [0.0] * 510]), (n, 1)))


def _install_fake_torch_and_transformers(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_torch = types.ModuleType("torch")
    fake_torch.no_grad = lambda: contextlib.nullcontext()
    fake_torch.backends = types.SimpleNamespace(
        mps=types.SimpleNamespace(is_available=lambda: False)
    )
    monkeypatch.setitem(sys.modules, "torch", fake_torch)

    fake_transformers = types.ModuleType("transformers")
    fake_transformers.CLIPModel = _FakeModel
    fake_transformers.CLIPProcessor = _FakeProcessor
    monkeypatch.setitem(sys.modules, "transformers", fake_transformers)


def test_embed_image_output_is_unit_norm_with_faked_model(monkeypatch, tmp_path):
    """Fakes torch/transformers via sys.modules (never a real model) to
    exercise the full "model loaded" branch of embed_image — output must be
    L2-normalized (unit norm)."""
    _install_fake_torch_and_transformers(monkeypatch)
    from PIL import Image

    image_path = tmp_path / "item.png"
    Image.new("RGB", (16, 16), color=(10, 20, 30)).save(image_path)

    service = FashionEmbeddingsService()
    vector = service.embed_image(str(image_path))

    assert vector is not None
    assert len(vector) == 512
    assert np.isclose(np.linalg.norm(np.asarray(vector)), 1.0)


def test_embed_texts_output_is_unit_norm_per_row_with_faked_model(monkeypatch):
    _install_fake_torch_and_transformers(monkeypatch)

    service = FashionEmbeddingsService()
    vectors = service.embed_texts(["a photo of a shirt", "a photo of jeans"])

    assert vectors is not None
    assert len(vectors) == 2
    for vec in vectors:
        assert np.isclose(np.linalg.norm(np.asarray(vec)), 1.0)
