from __future__ import annotations

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")

    # -------------------------------------------------------------------------
    # TCS GenAI Lab MaaS (primary — overrides OpenAI/Gemini when set)
    # -------------------------------------------------------------------------
    GENAILAB_API_KEY: Optional[str] = None
    GENAILAB_API_BASE: str = "https://genailab.tcs.in/"

    # -------------------------------------------------------------------------
    # Standard API keys (used when GenAI Lab is NOT configured)
    # -------------------------------------------------------------------------
    OPENAI_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None

    # -------------------------------------------------------------------------
    # LiteLLM routing
    # Model names for GenAI Lab:   genailab-maas-gpt-4o, gemini-2.5-flash, etc.
    # Model names for OpenAI:      gpt-4o, gpt-4o-mini, etc.
    # Model names for Gemini:      gemini/gemini-1.5-pro, etc.
    # -------------------------------------------------------------------------
    LITELLM_PRIMARY_MODEL: str = "genailab-maas-gpt-4o"
    LITELLM_FALLBACK_MODEL: str = "gemini-2.5-flash"
    LITELLM_REASONING_MODEL: str = "genailab-maas-gpt-4o"
    LITELLM_CACHE_ENABLED: bool = True
    LITELLM_CACHE_TTL: int = 3600
    LITELLM_MAX_TOKENS: int = 2048
    LITELLM_TEMPERATURE: float = 0.7

    # -------------------------------------------------------------------------
    # Embeddings
    # Use "all-MiniLM-L6-v2" for local (no API key needed)
    # Use "azure/genailab-maas-text-embedding-3-large" for GenAI Lab embeddings
    # -------------------------------------------------------------------------
    EMBEDDING_MODEL: str = "azure/genailab-maas-text-embedding-3-large"
    EMBEDDING_DEVICE: str = "cpu"
    # Set to false to use local sentence-transformers instead of Azure OpenAI
    USE_API_EMBEDDINGS: bool = True

    # -------------------------------------------------------------------------
    # FAISS
    # -------------------------------------------------------------------------
    FAISS_INDEX_PATH: str = "./data/faiss_index"
    MAX_RETRIEVED_DOCS: int = 10
    RERANK_TOP_K: int = 5

    # -------------------------------------------------------------------------
    # Server
    # -------------------------------------------------------------------------
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    LOG_LEVEL: str = "info"

    # CORS
    FRONTEND_URL: str = "http://localhost:3000"

    # Feature flags
    MOCK_LLM_MODE: bool = False

    # -------------------------------------------------------------------------
    # Network / Corporate proxy
    # Set to true on corporate networks with SSL inspection (e.g. TCS)
    # Disables certificate verification for HuggingFace Hub downloads
    # -------------------------------------------------------------------------
    DISABLE_SSL_VERIFY: bool = False

    # -------------------------------------------------------------------------
    # Derived helpers
    # -------------------------------------------------------------------------
    @property
    def has_genailab(self) -> bool:
        return bool(self.GENAILAB_API_KEY)

    @property
    def has_openai(self) -> bool:
        return bool(self.OPENAI_API_KEY)

    @property
    def has_gemini(self) -> bool:
        return bool(self.GEMINI_API_KEY)

    @property
    def has_any_llm(self) -> bool:
        return self.has_genailab or self.has_openai or self.has_gemini


settings = Settings()
