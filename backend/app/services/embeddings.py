from __future__ import annotations

from typing import List
import numpy as np

from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)


class EmbeddingService:
    """Wraps sentence-transformers for local embeddings."""

    def __init__(self) -> None:
        self._model = None

    def _load(self) -> None:
        if self._model is not None:
            return
        try:
            from sentence_transformers import SentenceTransformer
            logger.info("loading_embedding_model", model=settings.EMBEDDING_MODEL)
            self._model = SentenceTransformer(
                settings.EMBEDDING_MODEL,
                device=settings.EMBEDDING_DEVICE,
            )
            logger.info("embedding_model_loaded")
        except Exception as exc:
            logger.error("embedding_model_load_failed", error=str(exc))
            raise

    @property
    def dim(self) -> int:
        self._load()
        return self._model.get_sentence_embedding_dimension()  # type: ignore[union-attr]

    def encode(self, texts: List[str], normalize: bool = True) -> np.ndarray:
        self._load()
        return self._model.encode(  # type: ignore[union-attr]
            texts,
            normalize_embeddings=normalize,
            show_progress_bar=False,
            batch_size=32,
        )


embedding_service = EmbeddingService()
