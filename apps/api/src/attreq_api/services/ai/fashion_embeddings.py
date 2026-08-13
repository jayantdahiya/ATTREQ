"""FashionCLIP image/text embedding service (RI-6).

Lazy singleton, thread-safe, never raises. All heavy imports (`torch`,
`transformers`) live inside `_ensure_loaded()` only — importing this module
must stay free of any torch/transformers import so pytest collection and
every non-embedding code path never touches torch, even when it isn't
installed. Gated at the call sites by `settings.embeddings_enabled` (default
False — see config/settings.py); this class itself does not consult the
setting so it stays trivially unit-testable in isolation.

Design contract: every public method L2-normalizes its output vector before
returning it, so cosine similarity == plain dot product for the in-process
numpy math in `services/recommendation/similarity.py` (centroid scoring,
thumbs-propagation). The Weaviate `ClothingItemVector` collection also uses
COSINE distance (belt-and-braces, not load-bearing on its own).

Every method returns `None`/`[]` on any failure (missing file, model load
failure, inference exception) — never raises into the worker/upload path.
"""

import logging
import threading
from pathlib import Path

logger = logging.getLogger(__name__)

EMBEDDING_DIM = 512
_HF_MODEL = "patrickjohncyh/fashion-clip"


class FashionEmbeddingsService:
    """Lazy-loaded FashionCLIP wrapper with separate image/text processors."""

    def __init__(self) -> None:
        self._model = None
        self._image_processor = None
        self._tokenizer = None
        self._device = "cpu"
        # Guards both load AND inference — a torch forward pass is not
        # guaranteed reentrant across threads for a single shared model
        # instance, and this service is only ever used at wardrobe scale
        # (no throughput need to relax this).
        self._lock = threading.Lock()
        self._load_failed = False

    def _ensure_loaded(self) -> bool:
        if self._model is not None:
            return True
        if self._load_failed:
            return False
        with self._lock:
            if self._model is not None:
                return True
            try:
                import torch
                from transformers import CLIPImageProcessor, CLIPModel, CLIPTokenizerFast

                self._device = "mps" if torch.backends.mps.is_available() else "cpu"
                self._model = CLIPModel.from_pretrained(_HF_MODEL).to(self._device).eval()
                # The FashionCLIP repository's combined CLIPProcessor can route
                # an image-only call through its tokenizer with newer 4.x
                # Transformers releases. Keep the two modalities independent.
                self._image_processor = CLIPImageProcessor.from_pretrained(_HF_MODEL)
                self._tokenizer = CLIPTokenizerFast.from_pretrained(_HF_MODEL)
                logger.info(f"FashionCLIP loaded on {self._device}")
                return True
            except Exception as e:
                logger.error(f"FashionCLIP load failed: {e}")
                self._load_failed = True
                return False

    def is_available(self) -> bool:
        """True once the model is loaded (or loads successfully now)."""
        return self._ensure_loaded()

    def embed_image(self, image_path: str) -> list[float] | None:
        """Embed one image file to a 512-d, L2-normalized vector.

        Returns `None` on a missing file, a failed model load, or any
        inference error — never raises.
        """
        if not Path(image_path).exists():
            logger.error(f"Image not found for embedding: {image_path}")
            return None
        if not self._ensure_loaded():
            return None
        try:
            import torch
            from PIL import Image

            with self._lock:
                img = Image.open(image_path).convert("RGB")
                inputs = self._image_processor(images=img, return_tensors="pt").to(self._device)
                with torch.no_grad():
                    feats = self._model.get_image_features(**inputs)
                vec = feats[0].cpu().numpy()
            return self._normalize(vec).tolist()
        except Exception as e:
            logger.error(f"FashionCLIP image embed failed for {image_path}: {e}")
            return None

    def embed_texts(self, labels: list[str]) -> list[list[float]] | None:
        """Embed a batch of text labels to L2-normalized vectors.

        Returns `[]` for an empty input list, `None` on model-load/inference
        failure — never raises.
        """
        if not labels:
            return []
        if not self._ensure_loaded():
            return None
        try:
            import torch

            with self._lock:
                inputs = self._tokenizer(labels, return_tensors="pt", padding=True).to(self._device)
                with torch.no_grad():
                    feats = self._model.get_text_features(**inputs)
                arr = feats.cpu().numpy()
            return [self._normalize(v).tolist() for v in arr]
        except Exception as e:
            logger.error(f"FashionCLIP text embed failed: {e}")
            return None

    @staticmethod
    def _normalize(vec):
        import numpy as np

        v = np.asarray(vec, dtype=float)
        n = np.linalg.norm(v)
        return v / n if n > 0 else v


# Global lazy singleton — constructing this does no I/O and imports no torch;
# the model only loads on the first `embed_image`/`embed_texts`/`is_available` call.
fashion_embeddings_service = FashionEmbeddingsService()
