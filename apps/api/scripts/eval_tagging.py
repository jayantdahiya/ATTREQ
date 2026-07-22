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

RI-2 v1-vs-v2 merge gate (task 2.4/§5 of the RI-2 plan): `--schema v1` sends the
frozen pre-RI-2 prompt (`CLASSIFICATION_PROMPT_V1`) and scores only the fields it
asks for; `--schema v2` sends the new 12-attribute prompt (`CLASSIFICATION_PROMPT`)
and additionally scores the two DeepFashion shape dimensions that cleanly map into
our v2 vocabulary (sleeve_length, neckline — see SLEEVE_LENGTH_SHAPE_MAP /
NECKLINE_SHAPE_MAP below). `--gate` runs BOTH prompts on the same sampled images
(same seed) and exits nonzero if v2 regresses category/pattern accuracy by more
than 2 percentage points vs v1 — this is the actual merge gate, not just a
same-output rescore (scoring one output under two field sets can never show a
regression; two DIFFERENT prompts must actually be sent — see RI-2 plan finding #2).

Usage:
    python scripts/eval_tagging.py --backend groq --limit 25
    python scripts/eval_tagging.py --backend claude --images-dir /path/to/deepfashion/images
    python scripts/eval_tagging.py --backend groq --schema v2 --limit 25
    python scripts/eval_tagging.py --backend groq --gate --limit 500
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

# RI-2 (task 2.4/§5): DeepFashion-MultiModal's `shape_anno_all.txt` has 12 integer
# shape dimensions per image (`<img_name> <shape_0> ... <shape_11>`). Source:
# https://github.com/yumingj/DeepFashion-MultiModal#shape-annotations
#
#   0  sleeve length:  0 sleeveless, 1 short-sleeve, 2 medium-sleeve, 3 long-sleeve,
#                      4 not long-sleeve, 5 NA
#   1  lower clothing length, 2 socks, 3 hat, 4 glasses, 5 neckwear, 6 wrist wearing,
#      7 ring, 8 waist accessories, 10 cardigan, 11 navel coverage — NOT mapped: none
#      of these describe texture/silhouette/neckline/sleeve as our vocabulary defines
#      them (accessories/hat/glasses/etc. are out of scope; "lower clothing length" is
#      a bottoms-length fact, not our `silhouette` fit/cut concept).
#   9  neckline:       0 V-shape, 1 square, 2 round, 3 standing, 4 lapel,
#                      5 suspenders, 6 NA
#
# Only dims 0 (sleeve length) and 9 (neckline) map onto our v2 vocabulary — and
# even then, imperfectly (see per-code comments). No dim describes garment
# fit/cut, so `silhouette` has NO ground truth in this dataset and is
# deliberately never scored here (a wrong mapping is worse than none — RI-2
# plan finding #2). A manifest built from the real annotation file needs
# `shape_0`/`shape_9` integer columns for the two derived fields below to be
# populated; the checked-in manifest predates RI-2 and has neither, so v2
# scoring on sleeve_length/neckline reports `n=0`/`accuracy=None` until the
# manifest is regenerated against the real dataset.
SLEEVE_LENGTH_SHAPE_MAP: dict[int, str | None] = {
    0: "sleeveless",
    1: "short",
    2: "three_quarter",  # "medium-sleeve" — closest of our 4 sleeve lengths
    3: "long",
    4: None,  # "not long-sleeve" is ambiguous (could be short OR sleeveless) — SKIP
    5: None,  # NA — SKIP
}
NECKLINE_SHAPE_MAP: dict[int, str | None] = {
    0: "v_neck",
    1: "square",
    2: "crew",  # "round" — closest of our vocabulary's round necklines
    3: "turtleneck",  # "standing" (collar stands up around the neck)
    4: "collared",  # "lapel"
    5: None,  # "suspenders" isn't a neckline shape at all — SKIP
    6: None,  # NA — SKIP
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

    # RI-2: derive sleeve_length/neckline ground truth from the raw DeepFashion
    # shape codes (`shape_0`, `shape_9`) IF the manifest has them — the manifest
    # checked in for RI-1 predates RI-2 and has neither column, so this is a
    # no-op (those two fields simply won't be present in the returned records,
    # and `score()` reports them as `n=0`/`accuracy=None` rather than fabricating
    # ground truth). See SLEEVE_LENGTH_SHAPE_MAP / NECKLINE_SHAPE_MAP above for
    # the source mapping and which codes are unmapped (SKIP).
    extra_columns: list[str] = []
    if "shape_0" in manifest.columns:
        manifest["sleeve_length"] = manifest["shape_0"].map(SLEEVE_LENGTH_SHAPE_MAP)
        extra_columns.append("sleeve_length")
    if "shape_9" in manifest.columns:
        manifest["neckline"] = manifest["shape_9"].map(NECKLINE_SHAPE_MAP)
        extra_columns.append("neckline")

    return image_paths, manifest[["id", "filename", *GROUND_TRUTH_FIELDS, *extra_columns]]


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


async def run_classifier(
    backend: str, images: list[Path], schema: str = "v2"
) -> list[dict[str, Any]]:
    """Run the given classifier backend over a list of image paths.

    `schema="v1"` sends the frozen pre-RI-2 prompt (`CLASSIFICATION_PROMPT_V1`);
    `schema="v2"` sends the current production prompt (`CLASSIFICATION_PROMPT`,
    the 12-attribute v2 shape). Both go through `classifier.analyze_image` (a
    raw-JSON, custom-prompt call every backend already exposes) rather than
    `classify_single_image` — the latter is hardcoded to always send the
    CURRENT production prompt, which would make `--schema v1` silently send v2
    anyway (the exact bug the RI-2 plan's finding #2 calls out: scoring the
    same output under two field sets is not a valid regression gate; two
    DIFFERENT prompts must actually be sent to the model).

    v2 responses are additionally run through the schema mapper's enum
    coercion for `sleeve_length`/`neckline` so eval scoring is lenient to
    the same case/whitespace variance production tolerates.

    Failures for individual images are captured (not raised) so one bad image
    doesn't sink the whole benchmark run.
    """
    from attreq_api.config.settings import settings
    from attreq_api.schemas.wardrobe_enums import Neckline, SleeveLength, coerce_enum
    from attreq_api.services.ai.classifier_factory import get_classifier
    from attreq_api.services.ai.prompt_text import CLASSIFICATION_PROMPT, CLASSIFICATION_PROMPT_V1

    settings.classifier_provider = backend
    classifier = get_classifier()
    prompt = CLASSIFICATION_PROMPT_V1 if schema == "v1" else CLASSIFICATION_PROMPT

    semaphore = asyncio.Semaphore(4)

    async def classify_one(path: Path) -> dict[str, Any]:
        async with semaphore:
            try:
                raw = await classifier.analyze_image(str(path), prompt)
                if schema == "v2":
                    if "sleeve_length" in raw:
                        raw["sleeve_length"] = coerce_enum(
                            raw.get("sleeve_length"), SleeveLength, SleeveLength.N_A
                        ).value
                    if "neckline" in raw:
                        raw["neckline"] = coerce_enum(
                            raw.get("neckline"), Neckline, Neckline.N_A
                        ).value
                return raw
            except Exception as e:
                logger.warning("Classification failed for %s: %s", path, e)
                return {"category": None, "pattern": None, "_error": str(e)}

    return list(await asyncio.gather(*[classify_one(p) for p in images]))


def score(
    predictions: list[dict[str, Any]],
    ground_truth: list[dict[str, Any]],
    fields: list[str] | None = None,
) -> dict[str, Any]:
    """Per-field accuracy, exact-match rate, and confusion summaries.

    Scores `fields` (default `GROUND_TRUTH_FIELDS` — category, pattern; see
    module docstring for why color_primary/season/occasion are excluded).
    `--schema v2` scoring additionally passes `sleeve_length`/`neckline` (see
    SLEEVE_LENGTH_SHAPE_MAP/NECKLINE_SHAPE_MAP). Rows where the ground truth
    value for a field is missing/NA — including when the manifest doesn't
    have the column at all — are skipped for that field (`n=0`,
    `accuracy=None`), never fabricated.
    """
    fields = fields if fields is not None else GROUND_TRUTH_FIELDS
    result: dict[str, Any] = {}

    for field in fields:
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
        gt_values = {f: gt.get(f) for f in fields}
        if any(v is None or v == "NA" for v in gt_values.values()):
            continue
        exact_n += 1
        if all(pred.get(f) == v for f, v in gt_values.items()):
            exact_matches += 1

    result["exact_match"] = {
        "rate": (exact_matches / exact_n) if exact_n else None,
        "n": exact_n,
    }
    result["fields_scored"] = fields
    result["fields_excluded_no_ground_truth"] = ["color_primary", "season", "occasion"]

    return result


# Regression tolerance for the `--gate` merge check (RI-2 plan §5.3): if v2
# accuracy on any base (dataset-supported) field drops more than this many
# percentage points vs v1, the gate fails (exits nonzero).
_GATE_REGRESSION_TOLERANCE_PP = 0.02


def _fields_for_schema(schema: str, ground_truth: list[dict[str, Any]]) -> list[str]:
    """Which fields to score for a given `--schema` value.

    v1 only ever scores the base dataset-supported fields (category, pattern —
    the only ones its 8-field prompt shares with the dataset's real ground
    truth). v2 additionally scores sleeve_length/neckline WHEN the sampled
    ground truth actually has those columns (see `download_and_cache_sample` —
    absent unless the manifest was built from the real shape annotation file).
    """
    fields = list(GROUND_TRUTH_FIELDS)
    if schema == "v2" and ground_truth and "sleeve_length" in ground_truth[0]:
        fields.append("sleeve_length")
    if schema == "v2" and ground_truth and "neckline" in ground_truth[0]:
        fields.append("neckline")
    return fields


def _print_and_save(
    backend: str, schema: str, seed: int, n_images: int, results: dict[str, Any]
) -> Path:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = RESULTS_DIR / f"tagging_{backend}_{schema}_{timestamp}.json"
    out_path.write_text(
        json.dumps(
            {
                "backend": backend,
                "schema": schema,
                "seed": seed,
                "n_images": n_images,
                "results": results,
            },
            indent=2,
            default=str,
        )
    )

    print(f"Scored {n_images} images with backend={backend} schema={schema}")
    for field in results["fields_scored"]:
        acc = results[field]["accuracy"]
        print(f"  {field}: accuracy={acc if acc is None else f'{acc:.3f}'} (n={results[field]['n']})")
    print(f"  exact_match: rate={results['exact_match']['rate']} (n={results['exact_match']['n']})")
    print(f"Results written to {out_path}")
    return out_path


async def _run_gate(args: argparse.Namespace) -> int:
    """RI-2 merge gate: send BOTH the v1 and v2 prompts to the same sampled
    images (same seed) and diff per-field accuracy on the fields v1 can
    produce. Exits nonzero (returns a nonzero exit code) if v2 regresses any
    shared field by more than `_GATE_REGRESSION_TOLERANCE_PP`.
    """
    image_paths, ground_truth_df = download_and_cache_sample(
        n=args.limit,
        seed=args.seed,
        images_dir=Path(args.images_dir) if args.images_dir else None,
    )
    ground_truth = ground_truth_df.to_dict(orient="records")

    v1_predictions = await run_classifier(args.backend, image_paths, schema="v1")
    v2_predictions = await run_classifier(args.backend, image_paths, schema="v2")

    # Both scored on the SAME base fields — the only ones v1's prompt can
    # produce at all — so the diff is a genuine regression signal, not an
    # artifact of scoring different field sets (RI-2 plan finding #2).
    v1_results = score(v1_predictions, ground_truth, fields=GROUND_TRUTH_FIELDS)
    v2_results = score(v2_predictions, ground_truth, fields=GROUND_TRUTH_FIELDS)

    _print_and_save(args.backend, "v1", args.seed, len(image_paths), v1_results)
    _print_and_save(args.backend, "v2", args.seed, len(image_paths), v2_results)

    print("\n--- RI-2 merge gate: v1 vs v2 ---")
    regressed = False
    for field in GROUND_TRUTH_FIELDS:
        v1_acc = v1_results[field]["accuracy"]
        v2_acc = v2_results[field]["accuracy"]
        if v1_acc is None or v2_acc is None:
            print(f"  {field}: SKIP (no ground truth for this field/backend run)")
            continue
        delta = v2_acc - v1_acc
        status = "OK"
        if delta < -_GATE_REGRESSION_TOLERANCE_PP:
            regressed = True
            status = "REGRESSION"
        print(f"  {field}: v1={v1_acc:.3f} v2={v2_acc:.3f} delta={delta:+.3f} [{status}]")

    if regressed:
        print(
            f"\nGATE FAILED: v2 regressed one or more fields by more than "
            f"{_GATE_REGRESSION_TOLERANCE_PP:.0%}."
        )
        return 1

    print("\nGATE PASSED: no field regressed beyond tolerance.")
    return 0


async def _main_async(args: argparse.Namespace) -> int:
    if args.gate:
        return await _run_gate(args)

    image_paths, ground_truth_df = download_and_cache_sample(
        n=args.limit,
        seed=args.seed,
        images_dir=Path(args.images_dir) if args.images_dir else None,
    )

    predictions = await run_classifier(args.backend, image_paths, schema=args.schema)
    ground_truth = ground_truth_df.to_dict(orient="records")
    fields = _fields_for_schema(args.schema, ground_truth)

    results = score(predictions, ground_truth, fields=fields)
    _print_and_save(args.backend, args.schema, args.seed, len(image_paths), results)
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="RI-1/RI-2 classifier tagging benchmark")
    parser.add_argument(
        "--backend", choices=["groq", "claude", "openai", "gemini"], default="groq"
    )
    parser.add_argument(
        "--schema",
        choices=["v1", "v2"],
        default="v2",
        help="Which classifier prompt to send: v1 (frozen pre-RI-2) or v2 (current production)",
    )
    parser.add_argument(
        "--gate",
        action="store_true",
        help="RI-2 merge gate: run BOTH v1 and v2 on the same sample and exit "
        "nonzero if v2 regresses a shared field beyond tolerance (ignores --schema)",
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
    exit_code = asyncio.run(_main_async(args))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
