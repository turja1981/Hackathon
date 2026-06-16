from __future__ import annotations

from typing import List

import numpy as np

from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)

# Dimension lookup — strips provider prefix before matching
_MODEL_DIMS: dict[str, int] = {
    "genailab-maas-text-embedding-3-large": 3072,
    "text-embedding-3-large": 3072,
    "text-embedding-3-small": 1536,
    "text-embedding-ada-002": 1536,
    "all-MiniLM-L6-v2": 384,
    "all-MiniLM-L12-v2": 384,
    "all-mpnet-base-v2": 768,
}

_PROVIDER_PREFIXES = ("azure/", "azure_ai/", "openai/")


def _strip_prefix(name: str) -> str:
    for p in _PROVIDER_PREFIXES:
        if name.startswith(p):
            return name[len(p):]
    return name


class EmbeddingService:
    """Provider-aware embedding service.

    EMBEDDING_PROVIDER=genailab → LiteLLM → GenAI Lab MaaS (Azure-format or OpenAI-compatible)
    EMBEDDING_PROVIDER=openai   → LiteLLM → direct OpenAI
    EMBEDDING_PROVIDER=local    → sentence-transformers (no network call)
    """

    def __init__(self) -> None:
        self._local_model = None
        self._dim: int | None = None

    def _dim_from_model_name(self) -> int:
        return _MODEL_DIMS.get(_strip_prefix(settings.EMBEDDING_MODEL), 3072)

    @property
    def dim(self) -> int:
        if self._dim is not None:
            return self._dim
        if settings.EMBEDDING_PROVIDER.lower() == "local":
            self._load_local()
            self._dim = self._local_model.get_sentence_embedding_dimension()  # type: ignore[union-attr]
        else:
            self._dim = self._dim_from_model_name()
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
        if settings.EMBEDDING_PROVIDER.lower() == "local":
            self._load_local()
            return self._local_model.encode(  # type: ignore[union-attr]
                texts,
                normalize_embeddings=normalize,
                show_progress_bar=False,
                batch_size=32,
            )
        return self._encode_api(texts, normalize)

    def _encode_api(self, texts: List[str], normalize: bool = True) -> np.ndarray:
        provider = settings.EMBEDDING_PROVIDER.lower()

        import litellm

        if settings.DISABLE_SSL_VERIFY:
            litellm.ssl_verify = False

        kwargs: dict = {"model": settings.EMBEDDING_MODEL, "input": texts}

        if provider == "genailab":
            if not settings.GENAILAB_API_KEY:
                logger.warning("genailab_key_missing_using_mock_embeddings")
                return self._encode_mock(texts)
            kwargs.update({
                "api_key": settings.GENAILAB_API_KEY,
                "api_base": settings.GENAILAB_API_BASE,
            })
            # Azure-format and Azure AI models require api_version
            model = settings.EMBEDDING_MODEL
            if model.startswith("azure/") or model.startswith("azure_ai/"):
                kwargs["api_version"] = settings.LITELLM_API_VERSION

        elif provider == "openai":
            if not settings.OPENAI_API_KEY:
                logger.warning("openai_key_missing_using_mock_embeddings")
                return self._encode_mock(texts)
            kwargs["api_key"] = settings.OPENAI_API_KEY

        else:
            logger.warning("unknown_embedding_provider_using_mock", provider=provider)
            return self._encode_mock(texts)

        try:
            logger.info(
                "encoding_via_api",
                provider=provider,
                model=kwargs["model"],
                count=len(texts),
            )
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
            logger.error("api_embedding_failed_using_mock", provider=provider, error=str(exc))
            return self._encode_mock(texts)

    def _encode_mock(self, texts: List[str]) -> np.ndarray:
        """Deterministic mock embeddings — consistent across calls for the same text."""
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
