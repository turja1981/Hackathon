from __future__ import annotations

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")

    # -------------------------------------------------------------------------
    # Provider selection  (set exactly ONE; only that provider's key is needed)
    # -------------------------------------------------------------------------
    LLM_PROVIDER: str = "genailab"        # genailab | openai | gemini | mock
    EMBEDDING_PROVIDER: str = "genailab"  # genailab | openai | local

    # -------------------------------------------------------------------------
    # TCS GenAI Lab MaaS
    # -------------------------------------------------------------------------
    GENAILAB_API_KEY: Optional[str] = None
    GENAILAB_API_BASE: str = "https://genailab.tcs.in/"

    # -------------------------------------------------------------------------
    # Standard API keys (used only when LLM_PROVIDER / EMBEDDING_PROVIDER match)
    # -------------------------------------------------------------------------
    OPENAI_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None

    # -------------------------------------------------------------------------
    # LiteLLM models
    # GenAI Lab OpenAI-compatible (no prefix): genailab-maas-gpt-4o,
    #   genailab-maas-DeepSeek-V3-0324, gemini-2.5-flash, gemini-2.5-pro …
    # GenAI Lab Azure-format (keep azure/ prefix): azure/genailab-maas-gpt-5-mini,
    #   azure/genailab-maas-gpt-4.1, azure/genailab-maas-gpt-4.1-mini …
    # GenAI Lab Azure AI (keep azure_ai/ prefix): azure_ai/genailab-maas-DeepSeek-R1,
    #   azure_ai/genailab-maas-Llama-4-Maverick-17B-128E-Instruct-FP8 …
    # OpenAI: gpt-4o, gpt-4o-mini, gpt-4.1 …
    # Gemini: gemini/gemini-2.5-pro, gemini/gemini-2.5-flash …
    # -------------------------------------------------------------------------
    LITELLM_PRIMARY_MODEL: str = "genailab-maas-gpt-4o"
    LITELLM_REASONING_MODEL: str = "genailab-maas-gpt-4o"
    # Azure-format fallback (used when primary/reasoning fail)
    LITELLM_AZURE_FALLBACK_MODEL: str = "azure/genailab-maas-gpt-5-mini"
    # api-version required for azure/ and azure_ai/ prefixed model calls
    LITELLM_API_VERSION: str = "2024-06-01"

    LITELLM_CACHE_ENABLED: bool = True
    LITELLM_CACHE_TTL: int = 3600
    LITELLM_MAX_TOKENS: int = 2048
    LITELLM_TEMPERATURE: float = 0.7

    # -------------------------------------------------------------------------
    # Embeddings
    # genailab (azure-format): azure/genailab-maas-text-embedding-3-large
    # openai:                   text-embedding-3-large
    # local (no API key):       all-MiniLM-L6-v2
    # -------------------------------------------------------------------------
    EMBEDDING_MODEL: str = "azure/genailab-maas-text-embedding-3-large"
    EMBEDDING_DEVICE: str = "cpu"

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

    FRONTEND_URL: str = "http://localhost:3000"

    MOCK_LLM_MODE: bool = False

    # -------------------------------------------------------------------------
    # PubMed / NCBI E-utilities
    # PUBMED_API_KEY is optional — without it rate limit is 3 req/s (fine for demos)
    # Register free at https://www.ncbi.nlm.nih.gov/account/ for 10 req/s
    # -------------------------------------------------------------------------
    PUBMED_ENABLED: bool = True
    PUBMED_API_KEY: Optional[str] = None
    PUBMED_MAX_RESULTS: int = 20   # papers fetched per query from PubMed

    # -------------------------------------------------------------------------
    # Network
    # Set DISABLE_SSL_VERIFY=true on corporate networks with SSL inspection
    # -------------------------------------------------------------------------
    DISABLE_SSL_VERIFY: bool = False

    # -------------------------------------------------------------------------
    # Derived helpers
    # -------------------------------------------------------------------------
    @property
    def has_genailab(self) -> bool:
        return self.LLM_PROVIDER == "genailab" and bool(self.GENAILAB_API_KEY)

    @property
    def has_openai(self) -> bool:
        return self.LLM_PROVIDER == "openai" and bool(self.OPENAI_API_KEY)

    @property
    def has_gemini(self) -> bool:
        return self.LLM_PROVIDER == "gemini" and bool(self.GEMINI_API_KEY)

    @property
    def has_any_llm(self) -> bool:
        return self.has_genailab or self.has_openai or self.has_gemini

    @property
    def has_embedding_api(self) -> bool:
        p = self.EMBEDDING_PROVIDER.lower()
        if p == "genailab":
            return bool(self.GENAILAB_API_KEY)
        if p == "openai":
            return bool(self.OPENAI_API_KEY)
        return False  # local needs no key


settings = Settings()
