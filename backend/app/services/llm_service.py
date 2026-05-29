from __future__ import annotations

import hashlib
import json
from functools import lru_cache
from typing import Any, AsyncIterator, Dict, List, Optional

from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Mock responses for demo mode (no API key required)
# ---------------------------------------------------------------------------

_MOCK_SUMMARY = """
This collection of research papers explores cutting-edge developments across multiple life sciences domains including CRISPR gene editing for neurological diseases, mRNA vaccine platforms for cancer immunotherapy, single-cell RNA sequencing revealing novel cell populations, and AI-driven drug target discovery.

Key findings include: (1) CRISPR-Cas9 achieves 89% editing efficiency in iPSC-derived neurons with minimal off-target effects; (2) personalized mRNA vaccines show 78% tumor regression in clinical trials; (3) single-cell sequencing identifies 12 novel microglia sub-populations implicated in neuroinflammation; (4) graph neural networks outperform traditional approaches in protein-ligand binding prediction.

The convergence of these technologies represents a paradigm shift from population-based to precision medicine approaches, with AI serving as the critical enabler for managing biological complexity at scale.
""".strip()

_MOCK_HYPOTHESES = [
    {
        "id": "hyp_001",
        "hypothesis": "Combined CRISPR-mRNA therapeutic strategy can simultaneously correct genetic defects and prime immune response in neurodegenerative diseases",
        "rationale": "CRISPR demonstrates high efficiency in neurons while mRNA platforms enable transient immune modulation. Their combination could address both the genetic root cause and neuroinflammatory component of diseases like ALS and Parkinson's.",
        "experiments": [
            "Co-deliver CRISPR ribonucleoprotein + mRNA encoding anti-inflammatory cytokines in iPSC-derived motor neurons",
            "Assess editing efficiency, neuronal survival, and inflammatory marker expression at 7, 14, 30 days",
            "Validate in SOD1-mutant ALS mouse model using lipid nanoparticle delivery"
        ],
        "novelty_score": 0.92,
        "impact_area": "Neurodegeneration / Gene Therapy",
        "supporting_paper_ids": ["paper_001", "paper_002"]
    },
    {
        "id": "hyp_002",
        "hypothesis": "Single-cell transcriptomic signatures of reactive microglia can serve as early biomarkers predictive of Alzheimer's progression 5+ years before clinical symptoms",
        "rationale": "Newly identified microglia sub-populations show disease-state-specific gene expression patterns. Liquid biopsy capturing microglial extracellular vesicles may carry these signatures in cerebrospinal fluid.",
        "experiments": [
            "Longitudinal single-cell RNA-seq on CSF-derived microglia from presymptomatic APOE4 carriers",
            "Train ML classifier on transcriptomic signatures to predict disease progression",
            "Validate predictive power against 10-year clinical outcome data in biobank cohort"
        ],
        "novelty_score": 0.88,
        "impact_area": "Neurodegeneration / Biomarker Discovery",
        "supporting_paper_ids": ["paper_003", "paper_001"]
    },
    {
        "id": "hyp_003",
        "hypothesis": "Graph neural network models trained on multi-omics drug-target interaction data can identify repurposable FDA-approved drugs for rare pediatric cancers within 72 hours",
        "rationale": "GNN models capturing protein interaction networks outperform traditional docking in binding prediction. Rare cancers share molecular pathway dysregulations with common cancers where approved drugs exist.",
        "experiments": [
            "Build heterogeneous knowledge graph integrating protein-protein, drug-target, and disease-gene interactions",
            "Fine-tune GNN on pediatric cancer multi-omics datasets from PBTA and TARGET databases",
            "Prioritize top-10 repurposing candidates and validate top 3 in patient-derived organoids"
        ],
        "novelty_score": 0.85,
        "impact_area": "Oncology / Drug Discovery",
        "supporting_paper_ids": ["paper_004", "paper_006"]
    }
]


# ---------------------------------------------------------------------------
# LiteLLM router with fallback and caching
# ---------------------------------------------------------------------------

class LLMService:
    def __init__(self) -> None:
        self._router = None
        self._cache: Dict[str, str] = {}

    def _build_router(self):
        if self._router is not None:
            return

        import litellm
        from litellm import Router

        if settings.LITELLM_CACHE_ENABLED:
            try:
                from litellm import Cache
                litellm.cache = Cache(type="local", ttl=settings.LITELLM_CACHE_TTL)
            except Exception as cache_err:
                logger.warning("litellm_cache_init_failed", error=str(cache_err))

        model_list = []

        if settings.has_openai:
            model_list.append({
                "model_name": "primary",
                "litellm_params": {
                    "model": settings.LITELLM_PRIMARY_MODEL,
                    "api_key": settings.OPENAI_API_KEY,
                    "max_tokens": settings.LITELLM_MAX_TOKENS,
                    "temperature": settings.LITELLM_TEMPERATURE,
                }
            })
            model_list.append({
                "model_name": "reasoning",
                "litellm_params": {
                    "model": settings.LITELLM_REASONING_MODEL,
                    "api_key": settings.OPENAI_API_KEY,
                    "max_tokens": settings.LITELLM_MAX_TOKENS,
                    "temperature": 0.8,
                }
            })

        if settings.has_gemini:
            model_list.append({
                "model_name": "fallback",
                "litellm_params": {
                    "model": settings.LITELLM_FALLBACK_MODEL,
                    "api_key": settings.GEMINI_API_KEY,
                    "max_tokens": settings.LITELLM_MAX_TOKENS,
                    "temperature": settings.LITELLM_TEMPERATURE,
                }
            })

        if not model_list:
            logger.warning("no_llm_keys_configured", hint="Set OPENAI_API_KEY or GEMINI_API_KEY")
            return

        fallback_map = []
        if settings.has_openai and settings.has_gemini:
            fallback_map = [{"primary": ["fallback"]}, {"reasoning": ["fallback"]}]

        self._router = Router(
            model_list=model_list,
            fallbacks=fallback_map if fallback_map else [],
            num_retries=2,
            timeout=25,
        )
        logger.info("litellm_router_initialized",
                    primary=settings.LITELLM_PRIMARY_MODEL,
                    fallback=settings.LITELLM_FALLBACK_MODEL if settings.has_gemini else "none")

    def _cache_key(self, messages: List[Dict], model: str) -> str:
        payload = json.dumps({"model": model, "messages": messages}, sort_keys=True)
        return hashlib.sha256(payload.encode()).hexdigest()

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model_alias: str = "primary",
        use_cache: bool = True,
    ) -> str:
        if settings.MOCK_LLM_MODE or not settings.has_any_llm:
            return self._mock_response(messages)

        self._build_router()

        cache_key = self._cache_key(messages, model_alias)
        if use_cache and cache_key in self._cache:
            logger.info("llm_cache_hit", key=cache_key[:12])
            return self._cache[cache_key]

        try:
            response = await self._router.acompletion(  # type: ignore[union-attr]
                model=model_alias,
                messages=messages,
            )
            content: str = response.choices[0].message.content or ""
            if use_cache:
                self._cache[cache_key] = content
            return content
        except Exception as exc:
            logger.error("llm_call_failed", error=str(exc), model=model_alias)
            raise

    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        model_alias: str = "primary",
    ) -> AsyncIterator[str]:
        if settings.MOCK_LLM_MODE or not settings.has_any_llm:
            mock = self._mock_response(messages)
            for chunk in mock.split(" "):
                yield chunk + " "
            return

        self._build_router()

        try:
            async for chunk in await self._router.acompletion(  # type: ignore[union-attr]
                model=model_alias,
                messages=messages,
                stream=True,
            ):
                delta = chunk.choices[0].delta.content or ""
                if delta:
                    yield delta
        except Exception as exc:
            logger.error("llm_stream_failed", error=str(exc))
            raise

    def _mock_response(self, messages: List[Dict]) -> str:
        last = messages[-1]["content"].lower() if messages else ""
        if "hypothes" in last:
            return json.dumps(_MOCK_HYPOTHESES)
        if "rank" in last:
            return json.dumps([{"id": "paper_001", "score": 0.95}, {"id": "paper_002", "score": 0.88}])
        return _MOCK_SUMMARY


llm_service = LLMService()
