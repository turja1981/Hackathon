from __future__ import annotations

from typing import List

import numpy as np

from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)

# Dimension lookup by model suffix (strips azure/ or openai/ prefix)
_MODEL_DIMS: dict[str, int] = {
    "text-embedding-3-large": 3072,
    "genailab-maas-text-embedding-3-large": 3072,
    "text-embedding-3-small": 1536,
    "text-embedding-ada-002": 1536,
    "all-MiniLM-L6-v2": 384,
    "all-MiniLM-L12-v2": 384,
    "all-mpnet-base-v2": 768,
}


class EmbeddingService:
    """Embedding service.

    USE_API_EMBEDDINGS=true  → LiteLLM / Azure OpenAI (default, no HuggingFace)
    USE_API_EMBEDDINGS=false → local sentence-transformers
    """

    def __init__(self) -> None:
        self._local_model = None
        self._dim: int | None = None

    def _dim_from_model_name(self) -> int:
        # Strip provider prefix (azure/, openai/, etc.)
        name = settings.EMBEDDING_MODEL.split("/")[-1]
        return _MODEL_DIMS.get(name, 1536)

    @property
    def dim(self) -> int:
        if self._dim is not None:
            return self._dim
        if settings.USE_API_EMBEDDINGS:
            self._dim = self._dim_from_model_name()
        else:
            self._load_local()
            self._dim = self._local_model.get_sentence_embedding_dimension()  # type: ignore[union-attr]
        return self._dim

    def _load_local(self) -> None:
        if self._local_model is not None:
            return
        try:
            from sentence_transformers import SentenceTransformer

            logger.info("loading_local_embedding_model", model=settings.EMBEDDING_MODEL)
            self._local_model = SentenceTransformer(
                settings.EMBEDDING_MODEL, device=settings.EMBEDDING_DEVICE
            )
            logger.info("local_embedding_model_loaded")
        except Exception as exc:
            logger.error("local_embedding_model_failed", error=str(exc))
            raise

    def encode(self, texts: List[str], normalize: bool = True) -> np.ndarray:
        if settings.USE_API_EMBEDDINGS:
            return self._encode_api(texts, normalize)
        self._load_local()
        return self._local_model.encode(  # type: ignore[union-attr]
            texts,
            normalize_embeddings=normalize,
            show_progress_bar=False,
            batch_size=32,
        )

    def _encode_api(self, texts: List[str], normalize: bool = True) -> np.ndarray:
        if not settings.has_any_llm:
            logger.warning("no_api_key_using_mock_embeddings")
            return self._encode_mock(texts)

        import litellm

        try:
            kwargs: dict = {"model": settings.EMBEDDING_MODEL, "input": texts}
            if settings.GENAILAB_API_KEY:
                kwargs["api_key"] = settings.GENAILAB_API_KEY
                kwargs["api_base"] = settings.GENAILAB_API_BASE
            elif settings.OPENAI_API_KEY:
                kwargs["api_key"] = settings.OPENAI_API_KEY

            if settings.DISABLE_SSL_VERIFY:
                litellm.ssl_verify = False

            logger.info("encoding_via_api", model=settings.EMBEDDING_MODEL, count=len(texts))
            response = litellm.embedding(**kwargs)
            vectors = np.array(
                [item.embedding for item in response.data], dtype=np.float32
            )

            if normalize:
                norms = np.linalg.norm(vectors, axis=1, keepdims=True)
                norms = np.where(norms == 0, 1.0, norms)
                vectors = vectors / norms

            self._dim = vectors.shape[1]
            return vectors
        except Exception as exc:
            logger.error("api_embedding_failed", error=str(exc))
            raise

    def _encode_mock(self, texts: List[str]) -> np.ndarray:
        """Deterministic mock embeddings (used in MOCK_LLM_MODE with no API key)."""
        dim = self._dim_from_model_name()
        vectors = []
        for text in texts:
            seed = abs(hash(text)) % (2**31)
            rng = np.random.default_rng(seed)
            v = rng.random(dim).astype(np.float32)
            norm = np.linalg.norm(v)
            vectors.append(v / norm if norm > 0 else v)
        self._dim = dim
        return np.array(vectors)


embedding_service = EmbeddingService()
