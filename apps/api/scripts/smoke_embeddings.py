"""Smoke test the real FashionCLIP embedding path (RI-6).

Unlike the unit tests (which mock torch/transformers), this actually loads
`patrickjohncyh/fashion-clip` and runs inference, to prove the embedding
pipeline works end-to-end in an environment where torch is installed.

Run (requires torch + transformers, and network for the first model download):

    cd apps/api
    PYTHONPATH=src ../../.venv/bin/python scripts/smoke_embeddings.py [IMAGE_PATH]

Exits non-zero if the model fails to load or produce a valid vector.
"""

import sys
from pathlib import Path

import numpy as np

from attreq_api.services.ai.fashion_embeddings import (
    EMBEDDING_DIM,
    fashion_embeddings_service as svc,
)


def main() -> int:
    default_img = (
        Path(__file__).resolve().parents[3]
        / "docs/04-research/llm-detection/wardrobe_image.jpg"
    )
    image_path = sys.argv[1] if len(sys.argv) > 1 else str(default_img)

    print(f"Loading FashionCLIP … (image: {image_path})")
    if not svc.is_available():
        print("FAIL: model did not load (see logs).")
        return 1
    print(f"Model loaded on device: {svc._device}")

    vec = svc.embed_image(image_path)
    if vec is None:
        print("FAIL: embed_image returned None.")
        return 1
    v = np.asarray(vec)
    norm = float(np.linalg.norm(v))
    print(f"image vector: dim={len(vec)} (expected {EMBEDDING_DIM}), L2-norm={norm:.4f}")
    if len(vec) != EMBEDDING_DIM or not (0.99 <= norm <= 1.01):
        print("FAIL: unexpected vector shape/norm.")
        return 1

    labels = [
        "a photo of a shirt",
        "a photo of blue jeans",
        "a photo of a red dress",
        "a photo of white sneakers",
    ]
    texts = svc.embed_texts(labels)
    if not texts or len(texts) != len(labels):
        print("FAIL: embed_texts did not return one vector per label.")
        return 1

    # Zero-shot sanity: cosine (== dot, vectors are L2-normalized) of the
    # image against each label. We only assert the machinery produces a
    # sensible ranking spread, not a specific winner (the sample is a full
    # wardrobe photo, not a single garment).
    sims = {lbl: float(np.dot(v, np.asarray(t))) for lbl, t in zip(labels, texts, strict=True)}
    print("image↔label cosine similarities:")
    for lbl, s in sorted(sims.items(), key=lambda kv: -kv[1]):
        print(f"  {s:+.4f}  {lbl}")

    spread = max(sims.values()) - min(sims.values())
    if spread < 1e-3:
        print("FAIL: all similarities identical — model likely not discriminating.")
        return 1

    print("\nPASS: real FashionCLIP inference produced valid, discriminating embeddings.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
