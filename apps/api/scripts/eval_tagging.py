#!/usr/bin/env python
"""RI-1 classifier tagging benchmark against DeepFashion-MultiModal.

Runs a configured classifier backend (groq | claude | openai | gemini) over a
sampled, stratified set of DeepFashion-MultiModal images via the existing
`classifier_factory` (the same code path production upload uses) and reports
per-field accuracy against real ground truth.

IMPORTANT correction vs. the milestone doc / RI-1 plan (verified against the
dataset's own README, https://github.com/yumingj/DeepFashion-MultiModal):
DeepFashion-MultiModal has NO season/occasion labels (confirmed in the plan) AND,
beyond what the plan flagged, its file literally named "color annotations" does
NOT contain color hues (red/blue/...) at all — its 8 classes are
`floral, graphic, striped, pure color, lattice, other, color block, NA`, i.e. a
PATTERN taxonomy mislabeled "color" by the dataset authors. There is no true
color_primary ground truth anywhere in this dataset.

Consequently this benchmark scores only:
  - `pattern`   — sourced from the dataset's "color annotation" file (mapped into
                  our classifier's pattern vocabulary; see PATTERN_MAP below).
  - `category`  — sourced from the per-pixel human-parsing masks (which of
                  top/outer/skirt/dress/pants/leggings/rompers is present; see
                  CATEGORY_MAP below), NOT from the "shape annotation" file (that
                  file encodes garment silhouette details like sleeve length /
                  neckline, not a top-level category label).
  - `color_primary`, `season`, `occasion` are explicitly EXCLUDED — do not report
    fabricated accuracy for fields this dataset has no ground truth for. A future
    milestone should source a differently-labeled dataset if color/season/occasion
    accuracy is needed.

Image + label acquisition is semi-manual (Google-Drive-hosted, per the dataset
README): this script prefers a manifest CSV checked into the repo
(tests/fixtures/eval/deepfashion_sample_manifest.csv) so sample selection is
reproducible regardless of who fetches the bytes; if that manifest is missing it
attempts a best-effort `gdown` fetch of the raw dataset files, and falls back to a
clear, actionable manual-download message if that fails.

Usage:
    python scripts/eval_tagging.py --backend groq --limit 25
    python scripts/eval_tagging.py --backend claude --images-dir /path/to/deepfashion/images
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

logger = logging.getLogger("eval_tagging")

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "eval"
MANIFEST_PATH = FIXTURES_DIR / "deepfashion_sample_manifest.csv"
RESULTS_DIR = Path(__file__).resolve().parent.parent / "eval_results"

# Fields with real ground truth in this dataset. season/occasion/color_primary are
# deliberately excluded — see module docstring.
GROUND_TRUTH_FIELDS = ["category", "pattern"]

# Dataset's "color annotation" file classes -> our classifier's pattern vocabulary.
# Source: https://github.com/yumingj/DeepFashion-MultiModal#color-annotations
#   0 floral, 1 graphic, 2 striped, 3 pure color, 4 lattice, 5 other, 6 color block, 7 NA
PATTERN_MAP = {
    "floral": "floral",
    "graphic": "printed",
    "striped": "striped",
    "pure color": "solid",
    "lattice": "plaid",  # closest match to a grid/lattice texture in our vocabulary
    "color block": "abstract",  # approximation — documented, not exact
    "other": "other",
    "NA": None,
}

# Dataset's human-parsing labels (coarse garment presence) -> our classifier's
# category vocabulary. Source: https://github.com/yumingj/DeepFashion-MultiModal#human-parsing-label
# Only garment-relevant classes are mapped; body-part/background classes are ignored.
CATEGORY_MAP = {
    "top": "shirt",
    "outer": "jacket",
    "skirt": "skirt",
    "dress": "dress",
    "pants": "pants",
    "leggings": "leggings",
    "rompers": "jumpsuit",
}


def download_and_cache_sample(
    n: int = 500,
    seed: int = 42,
    cache_dir: Path | None = None,
    images_dir: Path | None = None,
) -> tuple[list[Path], pd.DataFrame]:
    """Resolve the stratified sample of (image_path, ground_truth) for this run.

    Resolution order:
      1. `images_dir` provided -> pair it with the checked-in manifest (manual
         download path — the primary, recommended path per the RI-1 plan).
      2. Manifest exists in the repo but no `images_dir` -> same, using
         `cache_dir` (default: FIXTURES_DIR / "deepfashion_images") as the image
         root; images are expected to already be there.
      3. No manifest at all -> attempt a best-effort `gdown` fetch of the raw
         dataset files and build the manifest from them (rebuild path — see
         `_build_manifest_from_raw`). On failure, raises with clear manual-setup
         instructions.

    Returns:
        (image_paths, ground_truth_df) — ground_truth_df has columns
        [id, filename, category, pattern], aligned index-for-index with
        image_paths.
    """
    cache_dir = cache_dir or (FIXTURES_DIR / "deepfashion_images")
    image_root = images_dir or cache_dir

    if not MANIFEST_PATH.exists():
        logger.warning(
            "No ground-truth manifest found at %s — attempting to build one from the raw "
            "dataset (requires gdown + Google Drive access to the files listed at "
            "https://github.com/yumingj/DeepFashion-MultiModal#download-links).",
            MANIFEST_PATH,
        )
        _build_manifest_from_raw(n=n, seed=seed, cache_dir=cache_dir)

    manifest = pd.read_csv(MANIFEST_PATH)
    if n < len(manifest):
        manifest = manifest.sample(n=n, random_state=seed).reset_index(drop=True)

    image_paths = [image_root / row["filename"] for _, row in manifest.iterrows()]
    missing = [p for p in image_paths if not p.exists()]
    if missing:
        raise FileNotFoundError(
            f"{len(missing)} of {len(image_paths)} sampled images are missing under {image_root}.\n"
            "Manual setup: download 'image.zip' from "
            "https://drive.google.com/file/d/1U2PljA7NE57jcSSzPs21ZurdIPXdYZtN/view "
            f"(see repo README link table), extract it, and pass --images-dir pointing at it.\n"
            f"First missing file: {missing[0]}"
        )

    return image_paths, manifest[["id", "filename", *GROUND_TRUTH_FIELDS]]


def _build_manifest_from_raw(n: int, seed: int, cache_dir: Path) -> None:
    """Best-effort fetch + build of the ground-truth manifest from raw dataset files.

    Requires `gdown` and network access to Google Drive; not exercised in CI or in
    sandboxed environments without Drive access. Raises a clear, actionable error on
    any failure rather than silently producing an empty/garbage manifest.
    """
    try:
        import gdown  # noqa: F401
    except ImportError as e:
        raise RuntimeError(
            "gdown is required to auto-fetch DeepFashion-MultiModal but is not installed. "
            "Install it (`pip install gdown`) or download manually — see "
            "https://github.com/yumingj/DeepFashion-MultiModal#download-links and pass "
            "--images-dir plus a hand-built manifest at "
            f"{MANIFEST_PATH}."
        ) from e

    raise RuntimeError(
        "Automatic DeepFashion-MultiModal download is not implemented in this sandbox: the "
        "dataset's `labels` and `image` archives are Google-Drive-hosted files that require "
        "interactive Drive authentication/consent, which is not available in an automated "
        "environment. Manual setup:\n"
        "  1. Download 'labels' (contains shape/fabric/color annotation .txt files) and "
        "'image' from https://github.com/yumingj/DeepFashion-MultiModal#download-links\n"
        "  2. Extract the color-annotation file and the human-parsing masks\n"
        "  3. Build a manifest CSV with columns [id, filename, category, pattern] using "
        "CATEGORY_MAP / PATTERN_MAP in this script, sampled with seed="
        f"{seed} for n={n}\n"
        f"  4. Save it to {MANIFEST_PATH} (checked into the repo so the sample is "
        "reproducible for everyone) and re-run this script."
    )


async def run_classifier(backend: str, images: list[Path]) -> list[dict[str, Any]]:
    """Run the given classifier backend over a list of image paths.

    Uses `classifier_factory.get_classifier()` -> `classify_single_image` per image —
    the same path production upload uses (`services/style_dna/style_dna_service.py`,
    `services/ai/clothing_detection.py`). Failures for individual images are captured
    (not raised) so one bad image doesn't sink the whole benchmark run.
    """
    from attreq_api.config.settings import settings
    from attreq_api.services.ai.classifier_factory import get_classifier

    settings.classifier_provider = backend
    classifier = get_classifier()

    semaphore = asyncio.Semaphore(4)

    async def classify_one(path: Path) -> dict[str, Any]:
        async with semaphore:
            try:
                return await classifier.classify_single_image(str(path))
            except Exception as e:
                logger.warning("Classification failed for %s: %s", path, e)
                return {"category": None, "pattern": None, "_error": str(e)}

    return list(await asyncio.gather(*[classify_one(p) for p in images]))


def score(predictions: list[dict[str, Any]], ground_truth: list[dict[str, Any]]) -> dict[str, Any]:
    """Per-field accuracy, exact-match rate, and confusion summaries.

    Only scores `GROUND_TRUTH_FIELDS` (category, pattern) — see module docstring
    for why color_primary/season/occasion are excluded. Rows where the ground
    truth value for a field is missing/NA are skipped for that field.
    """
    result: dict[str, Any] = {}

    for field in GROUND_TRUTH_FIELDS:
        correct = 0
        counted = 0
        confusion: dict[tuple[Any, Any], int] = {}

        for pred, gt in zip(predictions, ground_truth):
            gt_val = gt.get(field)
            if gt_val is None or gt_val == "NA" or (isinstance(gt_val, float) and pd.isna(gt_val)):
                continue
            counted += 1
            pred_val = pred.get(field)
            if pred_val == gt_val:
                correct += 1
            else:
                confusion[(gt_val, pred_val)] = confusion.get((gt_val, pred_val), 0) + 1

        top_confusions = sorted(confusion.items(), key=lambda kv: -kv[1])[:5]
        result[field] = {
            "accuracy": (correct / counted) if counted else None,
            "n": counted,
            "top_confusions": [
                {"ground_truth": gt_val, "predicted": pred_val, "count": count}
                for (gt_val, pred_val), count in top_confusions
            ],
        }

    exact_matches = 0
    exact_n = 0
    for pred, gt in zip(predictions, ground_truth):
        gt_values = {f: gt.get(f) for f in GROUND_TRUTH_FIELDS}
        if any(v is None or v == "NA" for v in gt_values.values()):
            continue
        exact_n += 1
        if all(pred.get(f) == v for f, v in gt_values.items()):
            exact_matches += 1

    result["exact_match"] = {
        "rate": (exact_matches / exact_n) if exact_n else None,
        "n": exact_n,
    }
    result["fields_scored"] = GROUND_TRUTH_FIELDS
    result["fields_excluded_no_ground_truth"] = ["color_primary", "season", "occasion"]

    return result


async def _main_async(args: argparse.Namespace) -> None:
    image_paths, ground_truth_df = download_and_cache_sample(
        n=args.limit,
        seed=args.seed,
        images_dir=Path(args.images_dir) if args.images_dir else None,
    )

    predictions = await run_classifier(args.backend, image_paths)
    ground_truth = ground_truth_df.to_dict(orient="records")

    results = score(predictions, ground_truth)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = RESULTS_DIR / f"tagging_{args.backend}_{timestamp}.json"
    out_path.write_text(
        json.dumps(
            {
                "backend": args.backend,
                "seed": args.seed,
                "n_images": len(image_paths),
                "results": results,
            },
            indent=2,
            default=str,
        )
    )

    print(f"Scored {len(image_paths)} images with backend={args.backend}")
    for field in GROUND_TRUTH_FIELDS:
        acc = results[field]["accuracy"]
        print(f"  {field}: accuracy={acc if acc is None else f'{acc:.3f}'} (n={results[field]['n']})")
    print(f"  exact_match: rate={results['exact_match']['rate']} (n={results['exact_match']['n']})")
    print(f"Results written to {out_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="RI-1 classifier tagging benchmark")
    parser.add_argument(
        "--backend", choices=["groq", "claude", "openai", "gemini"], default="groq"
    )
    parser.add_argument("--limit", type=int, default=500, help="Number of sampled images to score")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--images-dir",
        default=None,
        help="Path to a manually-downloaded copy of the DeepFashion-MultiModal images",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    asyncio.run(_main_async(args))


if __name__ == "__main__":
    main()
