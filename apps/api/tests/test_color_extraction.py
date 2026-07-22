"""Tests for `services/ai/color_extraction.py` (RI-2).

All test images are synthetic (`PIL.Image.new`) — no binary fixtures.
"""

from __future__ import annotations

import numpy as np
import pytest
from PIL import Image

from attreq_api.services.ai.color_extraction import (
    EmptyForegroundError,
    extract_palette,
    srgb_to_lab,
)


def _write_rgba_png(path, rgb: tuple[int, int, int], size=(40, 40), alpha=255):
    img = Image.new("RGBA", size, (*rgb, alpha))
    img.save(path)


class TestSrgbToLabReferenceValues:
    def test_white(self):
        lab = srgb_to_lab(np.array([255.0, 255.0, 255.0]))
        assert lab[0] == pytest.approx(100.0, abs=0.5)
        assert lab[1] == pytest.approx(0.0, abs=0.5)
        assert lab[2] == pytest.approx(0.0, abs=0.5)

    def test_black(self):
        lab = srgb_to_lab(np.array([0.0, 0.0, 0.0]))
        assert lab[0] == pytest.approx(0.0, abs=0.5)

    def test_red(self):
        lab = srgb_to_lab(np.array([255.0, 0.0, 0.0]))
        assert lab[0] == pytest.approx(53.24, abs=0.5)
        assert lab[1] == pytest.approx(80.09, abs=0.5)
        assert lab[2] == pytest.approx(67.20, abs=0.5)


class TestNeutralFlag:
    """C* = sqrt(a*^2 + b*^2) < 15 is a perceptual-achromatic test — black,
    white, and gray pass; navy (a *fashion* neutral, but chromatic at
    C* ~= 80) and saturated red do NOT."""

    def _extract_single_color(self, tmp_path, rgb):
        path = tmp_path / "swatch.png"
        _write_rgba_png(path, rgb)
        palette = extract_palette(str(path), k=1)
        return palette.colors[0]

    def test_black_is_neutral(self, tmp_path):
        assert self._extract_single_color(tmp_path, (0, 0, 0)).is_neutral is True

    def test_white_is_neutral(self, tmp_path):
        assert self._extract_single_color(tmp_path, (255, 255, 255)).is_neutral is True

    def test_gray_is_neutral(self, tmp_path):
        assert self._extract_single_color(tmp_path, (128, 128, 128)).is_neutral is True

    def test_navy_is_not_neutral(self, tmp_path):
        color = self._extract_single_color(tmp_path, (0, 0, 128))
        assert color.is_neutral is False
        assert color.name == "navy"

    def test_saturated_red_is_not_neutral(self, tmp_path):
        assert self._extract_single_color(tmp_path, (255, 0, 0)).is_neutral is False


class TestKMeansDeterminism:
    def test_same_seed_produces_same_palette(self, tmp_path):
        path = tmp_path / "multi.png"
        img = Image.new("RGBA", (60, 30), (0, 0, 0, 0))
        pixels = img.load()
        for x in range(30):
            for y in range(30):
                pixels[x, y] = (200, 30, 30, 255)
        for x in range(30, 60):
            for y in range(30):
                pixels[x, y] = (30, 30, 200, 255)
        img.save(path)

        palette_a = extract_palette(str(path), k=2, seed=42)
        palette_b = extract_palette(str(path), k=2, seed=42)

        assert [c.hex for c in palette_a.colors] == [c.hex for c in palette_b.colors]
        assert [c.share for c in palette_a.colors] == [c.share for c in palette_b.colors]

    def test_dominant_color_sorted_first(self, tmp_path):
        path = tmp_path / "dominant.png"
        img = Image.new("RGBA", (10, 10), (200, 30, 30, 255))
        pixels = img.load()
        # A small minority of blue pixels.
        for x in range(2):
            for y in range(2):
                pixels[x, y] = (30, 30, 200, 255)
        img.save(path)

        palette = extract_palette(str(path), k=2, seed=42)
        assert palette.colors[0].share >= palette.colors[-1].share


class TestEmptyForeground:
    def test_fully_transparent_image_raises(self, tmp_path):
        path = tmp_path / "empty.png"
        _write_rgba_png(path, (255, 0, 0), alpha=0)

        with pytest.raises(EmptyForegroundError):
            extract_palette(str(path))


class TestPaletteShape:
    def test_source_is_pixel(self, tmp_path):
        path = tmp_path / "solid.png"
        _write_rgba_png(path, (10, 200, 10))
        palette = extract_palette(str(path), k=1)
        assert palette.source == "pixel"
        assert len(palette.colors) == 1
        assert palette.colors[0].hex.startswith("#")
