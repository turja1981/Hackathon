from __future__ import annotations

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")

    # LLM API keys
    OPENAI_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None

    # LiteLLM routing
    LITELLM_PRIMARY_MODEL: str = "gpt-4o"
    LITELLM_FALLBACK_MODEL: str = "gemini/gemini-1.5-pro"
    LITELLM_REASONING_MODEL: str = "gpt-4o"
    LITELLM_CACHE_ENABLED: bool = True
    LITELLM_CACHE_TTL: int = 3600
    LITELLM_MAX_TOKENS: int = 2048
    LITELLM_TEMPERATURE: float = 0.7

    # Embeddings
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_DEVICE: str = "cpu"

    # FAISS
    FAISS_INDEX_PATH: str = "./data/faiss_index"
    MAX_RETRIEVED_DOCS: int = 10
    RERANK_TOP_K: int = 5

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    LOG_LEVEL: str = "info"

    # CORS
    FRONTEND_URL: str = "http://localhost:3000"

    # Feature flags
    MOCK_LLM_MODE: bool = False

    @property
    def has_openai(self) -> bool:
        return bool(self.OPENAI_API_KEY)

    @property
    def has_gemini(self) -> bool:
        return bool(self.GEMINI_API_KEY)

    @property
    def has_any_llm(self) -> bool:
        return self.has_openai or self.has_gemini


settings = Settings()
