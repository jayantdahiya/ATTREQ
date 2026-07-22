"""Deterministic CIELAB color palette extraction (RI-2).

Color is the least reliable classifier attribute (LLM-judged named colors).
This module extracts a K-means palette in CIELAB space directly from the
background-removed garment pixels — illumination-invariant, deterministic
under a fixed seed, and independent of any LLM.

Precedence (documented once, here, as the single source of truth): the
`color_palette` JSONB column is always pixel-Lab when extraction succeeds.
The classifier's `color_primary`/`color_secondary` (LLM-judged) remain a
human-readable descriptor and the fallback display string when either
background removal or pixel extraction fails (`color_extraction_source =
"llm_fallback"`). `services/ai/clothing_detection.py`'s `_fallback_detection`
RGB K-means is a *third*, unrelated path that only fires when the classifier
API itself is unconfigured/erroring — it only ever feeds `color_primary`, never
`color_palette`.

sRGB<->CIELAB (D65) is hand-rolled on vectorized numpy rather than adding
`scikit-image`/`colormath` — two ~20-line conversions, numpy is already a
dependency, and the reference-value test below guards correctness.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

import numpy as np
from PIL import Image
from sklearn.cluster import KMeans

logger = logging.getLogger(__name__)

# Foreground pixels above this count are randomly (seeded) downsampled before
# K-means, purely for speed — doesn't affect determinism.
_MAX_SAMPLE_PIXELS = 20_000
_DEFAULT_SEED = 42
_NEUTRAL_CHROMA_THRESHOLD = 15.0  # C* = sqrt(a*^2 + b*^2); perceptual-achromatic
# cutoff (black/white/gray only) — NOT "fashion neutrals" (navy, e.g., has
# C* ~ 80 despite being a wardrobe-neutral color; see test_color_extraction.py).

# D65 reference white (CIE standard observer, 2 degree).
_D65_XN = 0.95047
_D65_YN = 1.00000
_D65_ZN = 1.08883

# sRGB (linear) <-> XYZ, D65. Standard IEC 61966-2-1 matrices.
_RGB_TO_XYZ = np.array(
    [
        [0.4124564, 0.3575761, 0.1804375],
        [0.2126729, 0.7151522, 0.0721750],
        [0.0193339, 0.1191920, 0.9503041],
    ]
)
_XYZ_TO_RGB = np.array(
    [
        [3.2404542, -1.5371385, -0.4985314],
        [-0.9692660, 1.8760108, 0.0415560],
        [0.0556434, -0.2040259, 1.0572252],
    ]
)

# Named-color reference table (Lab), built once at import from the SAME
# 16-color vocabulary the classifier prompt uses (`prompt_text.py`'s
# color_primary options) — NOT `clothing_detection.COLOR_NAMES` (a different,
# pure-primaries table missing tan/cream), so pixel-vs-LLM color comparisons
# in the eval gate compare apples to apples.
_NAMED_COLOR_RGB: dict[str, tuple[int, int, int]] = {
    "black": (0, 0, 0),
    "white": (255, 255, 255),
    "blue": (0, 0, 255),
    "red": (255, 0, 0),
    "green": (0, 128, 0),
    "brown": (139, 69, 19),
    "beige": (245, 245, 220),
    "gray": (128, 128, 128),
    "navy": (0, 0, 128),
    "maroon": (128, 0, 0),
    "pink": (255, 192, 203),
    "purple": (128, 0, 128),
    "yellow": (255, 255, 0),
    "orange": (255, 165, 0),
    "tan": (210, 180, 140),
    "cream": (255, 253, 208),
}


class EmptyForegroundError(Exception):
    """Raised when an image has zero foreground (alpha > 127) pixels."""


@dataclass(frozen=True)
class PaletteColor:
    """One cluster in an extracted palette."""

    lab: tuple[float, float, float]
    hex: str
    share: float
    is_neutral: bool
    name: str


@dataclass(frozen=True)
class ColorPalette:
    """A full extracted palette, dominant color first."""

    colors: list[PaletteColor]
    source: str  # "pixel"


def _srgb_to_linear(c: np.ndarray) -> np.ndarray:
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def _linear_to_srgb(c: np.ndarray) -> np.ndarray:
    c = np.clip(c, 0.0, 1.0)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * (c ** (1 / 2.4)) - 0.055)


def _f_lab(t: np.ndarray) -> np.ndarray:
    delta = 6 / 29
    return np.where(t > delta**3, np.cbrt(t), t / (3 * delta**2) + 4 / 29)


def _f_lab_inv(t: np.ndarray) -> np.ndarray:
    delta = 6 / 29
    return np.where(t > delta, t**3, 3 * delta**2 * (t - 4 / 29))


def srgb_to_lab(rgb: np.ndarray) -> np.ndarray:
    """Vectorized sRGB (0-255, `(..., 3)`) -> CIELAB (D65).

    Accepts any leading shape; the last axis must be length-3 RGB.
    """
    rgb01 = np.asarray(rgb, dtype=np.float64) / 255.0
    linear = _srgb_to_linear(rgb01)
    xyz = linear @ _RGB_TO_XYZ.T

    x = xyz[..., 0] / _D65_XN
    y = xyz[..., 1] / _D65_YN
    z = xyz[..., 2] / _D65_ZN

    fx, fy, fz = _f_lab(x), _f_lab(y), _f_lab(z)

    l_star = 116 * fy - 16
    a_star = 500 * (fx - fy)
    b_star = 200 * (fy - fz)

    return np.stack([l_star, a_star, b_star], axis=-1)


def lab_to_srgb(lab: np.ndarray) -> np.ndarray:
    """Vectorized CIELAB (D65) -> sRGB (0-255, clipped, uint8-range floats)."""
    lab = np.asarray(lab, dtype=np.float64)
    l_star, a_star, b_star = lab[..., 0], lab[..., 1], lab[..., 2]

    fy = (l_star + 16) / 116
    fx = fy + a_star / 500
    fz = fy - b_star / 200

    x = _D65_XN * _f_lab_inv(fx)
    y = _D65_YN * _f_lab_inv(fy)
    z = _D65_ZN * _f_lab_inv(fz)

    xyz = np.stack([x, y, z], axis=-1)
    linear = xyz @ _XYZ_TO_RGB.T
    srgb = _linear_to_srgb(linear)
    return srgb * 255.0


def _lab_to_hex(lab: tuple[float, float, float]) -> str:
    rgb = lab_to_srgb(np.array(lab))
    r, g, b = (int(round(v)) for v in np.clip(rgb, 0, 255))
    return f"#{r:02x}{g:02x}{b:02x}"


def _nearest_color_name(lab: tuple[float, float, float]) -> str:
    target = np.array(lab)
    best_name, best_dist = "unknown", float("inf")
    for name, ref_lab in _NAMED_COLOR_LAB.items():
        dist = float(np.linalg.norm(target - ref_lab))
        if dist < best_dist:
            best_dist, best_name = dist, name
    return best_name


# Built once at module load — converts the reference RGB table above to Lab.
_NAMED_COLOR_LAB: dict[str, np.ndarray] = {
    name: srgb_to_lab(np.array(rgb, dtype=np.float64))
    for name, rgb in _NAMED_COLOR_RGB.items()
}


def extract_palette(image_path: str, k: int = 3, seed: int = _DEFAULT_SEED) -> ColorPalette:
    """Extract a k-color CIELAB palette from a background-removed RGBA image.

    Args:
        image_path: Path to a background-removed PNG (must have an alpha
            channel — pass `processed_tmp` from
            `background_removal.generate_processed_and_thumbnail`, never
            `classification_path`/`original_tmp`, which is what
            `classification_path` becomes on bg-removal failure).
        k: Number of clusters to request (fewer are used if there are fewer
            unique foreground pixels than `k`).
        seed: Random seed for both pixel sampling and K-means — extraction is
            fully deterministic under a fixed seed.

    Returns:
        `ColorPalette` sorted by `share` descending (dominant color first).

    Raises:
        EmptyForegroundError: If the image has zero pixels with alpha > 127.
    """
    image = Image.open(image_path).convert("RGBA")
    pixels = np.array(image).reshape(-1, 4)

    foreground = pixels[pixels[:, 3] > 127]
    if foreground.shape[0] == 0:
        raise EmptyForegroundError(f"No foreground pixels (alpha > 127) in {image_path}")

    rgb_pixels = foreground[:, :3].astype(np.float64)

    rng = np.random.default_rng(seed)
    if rgb_pixels.shape[0] > _MAX_SAMPLE_PIXELS:
        indices = rng.choice(rgb_pixels.shape[0], size=_MAX_SAMPLE_PIXELS, replace=False)
        rgb_pixels = rgb_pixels[indices]

    lab_pixels = srgb_to_lab(rgb_pixels)

    n_unique = len(np.unique(rgb_pixels, axis=0))
    n_clusters = min(k, n_unique)

    kmeans = KMeans(n_clusters=n_clusters, random_state=seed, n_init=10)
    labels = kmeans.fit_predict(lab_pixels)
    centroids = kmeans.cluster_centers_

    total = len(labels)
    colors: list[PaletteColor] = []
    for cluster_idx in range(n_clusters):
        count = int(np.sum(labels == cluster_idx))
        share = count / total
        lab = tuple(float(v) for v in centroids[cluster_idx])
        chroma = float(np.sqrt(lab[1] ** 2 + lab[2] ** 2))
        colors.append(
            PaletteColor(
                lab=lab,
                hex=_lab_to_hex(lab),
                share=share,
                is_neutral=chroma < _NEUTRAL_CHROMA_THRESHOLD,
                name=_nearest_color_name(lab),
            )
        )

    colors.sort(key=lambda c: c.share, reverse=True)
    return ColorPalette(colors=colors, source="pixel")


async def extract_palette_safe(
    processed_tmp: str | None, log_ref: object = None
) -> tuple[ColorPalette | None, str]:
    """Async, never-raising wrapper around `extract_palette` for the image
    workers (`workers/image_processor.py`, `workers/batch_image_processor.py`).

    Degrades to `(None, "llm_fallback")` when `processed_tmp` is `None`
    (background removal itself failed — see call sites, which only pass a
    real path when bg removal succeeded) or when extraction raises for any
    reason (empty foreground, corrupt file, etc.). Runs the CPU-bound
    K-means/Lab-conversion work in a thread so it doesn't block the event
    loop, and is safe to run concurrently (via `asyncio.gather`) alongside
    classification.
    """
    if processed_tmp is None:
        return None, "llm_fallback"
    try:
        palette = await asyncio.to_thread(extract_palette, processed_tmp)
        return palette, "pixel"
    except Exception as e:
        logger.warning(f"Pixel color extraction failed for {log_ref}: {str(e)}")
        return None, "llm_fallback"
