from __future__ import annotations

import hashlib
import json
from typing import Any, AsyncIterator, Dict, List, Optional

from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Mock responses for demo / no-key mode
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
        "supporting_paper_ids": ["paper_001", "paper_002"],
        "reasoning_path": [
            {"paper_id": "paper_001", "paper_title": "CRISPR-Cas9 Gene Editing in iPSC-Derived Neurons", "finding": "89% editing efficiency in motor neurons with minimal off-target effects", "relevance": "Establishes feasibility of CRISPR in neuronal context"},
            {"paper_id": "paper_002", "paper_title": "mRNA Vaccine Platform for Cancer Immunotherapy", "finding": "mRNA delivery achieves transient immune modulation without genomic integration", "relevance": "Provides complementary immune priming mechanism"}
        ],
        "agreement_score": 0.82
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
        "supporting_paper_ids": ["paper_003", "paper_001"],
        "reasoning_path": [
            {"paper_id": "paper_003", "paper_title": "Single-Cell RNA Sequencing Reveals Novel Microglia Subtypes", "finding": "12 distinct microglia sub-populations identified with disease-stage-specific markers", "relevance": "Provides the transcriptomic signatures that could serve as biomarkers"},
            {"paper_id": "paper_001", "paper_title": "CRISPR-Cas9 Gene Editing in iPSC-Derived Neurons", "finding": "APOE4 variant shows elevated neuroinflammatory gene expression", "relevance": "Links genetic risk to microglial activation patterns"}
        ],
        "agreement_score": 0.78
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
        "supporting_paper_ids": ["paper_004", "paper_006"],
        "reasoning_path": [
            {"paper_id": "paper_004", "paper_title": "Graph Neural Networks for Drug-Target Interaction Prediction", "finding": "GNN achieves 94% AUC on protein-ligand binding prediction", "relevance": "Demonstrates GNN superiority for drug repurposing tasks"},
            {"paper_id": "paper_006", "paper_title": "Pancreatic Cancer Stroma Reprogramming", "finding": "Shared KRAS-MAPK pathway dysregulation between pediatric and adult cancers", "relevance": "Establishes molecular basis for cross-cancer drug repurposing"}
        ],
        "agreement_score": 0.75
    }
]

_MOCK_GAPS = [
    {
        "id": "gap_001",
        "gap_description": "No studies examine combined CRISPR + mRNA therapeutic delivery for simultaneous gene correction and immune priming in ALS motor neurons",
        "area": "Gene Therapy / Neurodegeneration",
        "opportunity_level": "High",
        "missing_connections": ["CRISPR delivery in motor neurons", "mRNA immune modulation in CNS", "ALS therapeutic combinations"],
        "suggested_experiments": ["Co-delivery lipid nanoparticle formulation study", "iPSC motor neuron combined therapy assay"],
        "novelty_score": 0.91,
        "related_paper_ids": ["paper_001", "paper_002", "paper_009"]
    },
    {
        "id": "gap_002",
        "gap_description": "The relationship between gut microbiome composition and CAR-T cell therapy efficacy in hematological malignancies remains unexplored",
        "area": "Immunotherapy / Microbiome",
        "opportunity_level": "High",
        "missing_connections": ["Microbiome-immune axis modulation", "CAR-T exhaustion mechanisms", "Pre-treatment microbiome profiling"],
        "suggested_experiments": ["Longitudinal microbiome profiling in CAR-T patients", "Germ-free mouse model with CAR-T transfer"],
        "novelty_score": 0.88,
        "related_paper_ids": ["paper_007", "paper_002"]
    },
    {
        "id": "gap_003",
        "gap_description": "Spatial transcriptomics has not been applied to map microglial activation gradients in early-stage Alzheimer's disease tissue at sub-cellular resolution",
        "area": "Neuroscience / Spatial Genomics",
        "opportunity_level": "Medium",
        "missing_connections": ["Spatial resolution of neuroinflammation", "Single-cell Alzheimer's atlas integration", "Microglial polarity mapping"],
        "suggested_experiments": ["10x Visium HD on Alzheimer's brain slices", "Integration with single-nucleus RNA-seq data"],
        "novelty_score": 0.79,
        "related_paper_ids": ["paper_001", "paper_003", "paper_010"]
    },
    {
        "id": "gap_004",
        "gap_description": "No benchmark exists comparing graph neural networks vs. molecular dynamics for predicting allosteric drug binding sites in IDH-mutant cancers",
        "area": "Computational Chemistry / Oncology",
        "opportunity_level": "Medium",
        "missing_connections": ["Allosteric site prediction benchmarks", "GNN-MD hybrid approaches", "IDH mutant cancer therapeutic targets"],
        "suggested_experiments": ["Build standardized allosteric site benchmark dataset", "Head-to-head GNN vs MD comparison on IDH1/2 mutants"],
        "novelty_score": 0.76,
        "related_paper_ids": ["paper_004", "paper_006"]
    },
    {
        "id": "gap_005",
        "gap_description": "Lipid nanoparticle formulations optimized for pancreatic stellate cell targeting to enable stroma remodeling prior to chemotherapy have not been characterized",
        "area": "Drug Delivery / Pancreatic Cancer",
        "opportunity_level": "High",
        "missing_connections": ["LNP tropism for stellate cells", "Stroma-targeting delivery strategies", "Pre-conditioning for chemotherapy"],
        "suggested_experiments": ["LNP surface modification screen for stellate cell uptake", "In vivo stroma remodeling + gemcitabine combination study"],
        "novelty_score": 0.85,
        "related_paper_ids": ["paper_006", "paper_009"]
    }
]


# ---------------------------------------------------------------------------
# LiteLLM router — supports GenAI Lab, OpenAI, Gemini with fallback chain
# ---------------------------------------------------------------------------

class LLMService:
    def __init__(self) -> None:
        self._router = None
        self._cache: Dict[str, str] = {}

    def _build_router(self) -> None:
        if self._router is not None:
            return

        import litellm
        from litellm import Router

        if settings.DISABLE_SSL_VERIFY:
            litellm.ssl_verify = False

        if settings.LITELLM_CACHE_ENABLED:
            try:
                from litellm import Cache
                litellm.cache = Cache(type="local", ttl=settings.LITELLM_CACHE_TTL)
            except Exception as e:
                logger.warning("litellm_cache_init_failed", error=str(e))

        model_list: List[Dict] = []
        provider = settings.LLM_PROVIDER.lower()
        _common = {
            "max_tokens": settings.LITELLM_MAX_TOKENS,
            "temperature": settings.LITELLM_TEMPERATURE,
        }

        # ------------------------------------------------------------------
        # GenAI Lab MaaS
        # Primary / reasoning: OpenAI-compatible endpoint (openai/ prefix)
        # Azure fallback:       Azure-format deployment (azure/ prefix + api_version)
        # ------------------------------------------------------------------
        if provider == "genailab":
            _openai_base = {
                **_common,
                "api_key": settings.GENAILAB_API_KEY,
                "api_base": settings.GENAILAB_API_BASE,
            }
            _azure_base = {
                **_openai_base,
                "api_version": settings.LITELLM_API_VERSION,
            }

            model_list = [
                {
                    "model_name": "primary",
                    "litellm_params": {
                        "model": f"openai/{settings.LITELLM_PRIMARY_MODEL}",
                        **_openai_base,
                    },
                },
                {
                    "model_name": "reasoning",
                    "litellm_params": {
                        "model": f"openai/{settings.LITELLM_REASONING_MODEL}",
                        **_openai_base,
                        "temperature": 0.8,
                    },
                },
                # Azure-format fallback (azure/ or azure_ai/ prefixed model)
                {
                    "model_name": "fallback",
                    "litellm_params": {
                        "model": settings.LITELLM_AZURE_FALLBACK_MODEL,
                        **_azure_base,
                    },
                },
            ]
            logger.info(
                "litellm_provider_genailab",
                primary=settings.LITELLM_PRIMARY_MODEL,
                azure_fallback=settings.LITELLM_AZURE_FALLBACK_MODEL,
                base=settings.GENAILAB_API_BASE,
            )

        # ------------------------------------------------------------------
        # Direct OpenAI
        # ------------------------------------------------------------------
        elif provider == "openai":
            _base = {**_common, "api_key": settings.OPENAI_API_KEY}
            model_list = [
                {
                    "model_name": "primary",
                    "litellm_params": {"model": settings.LITELLM_PRIMARY_MODEL, **_base},
                },
                {
                    "model_name": "reasoning",
                    "litellm_params": {
                        "model": settings.LITELLM_REASONING_MODEL,
                        **_base,
                        "temperature": 0.8,
                    },
                },
            ]
            logger.info("litellm_provider_openai", primary=settings.LITELLM_PRIMARY_MODEL)

        # ------------------------------------------------------------------
        # Direct Gemini
        # ------------------------------------------------------------------
        elif provider == "gemini":
            _base = {**_common, "api_key": settings.GEMINI_API_KEY}
            model_list = [
                {
                    "model_name": "primary",
                    "litellm_params": {
                        "model": f"gemini/{settings.LITELLM_PRIMARY_MODEL}",
                        **_base,
                    },
                },
                {
                    "model_name": "reasoning",
                    "litellm_params": {
                        "model": f"gemini/{settings.LITELLM_REASONING_MODEL}",
                        **_base,
                        "temperature": 0.8,
                    },
                },
            ]
            logger.info("litellm_provider_gemini", primary=settings.LITELLM_PRIMARY_MODEL)

        if not model_list:
            logger.warning("no_llm_configured", provider=provider,
                           hint="Check LLM_PROVIDER and the matching API key")
            return

        has_fallback = any(m["model_name"] == "fallback" for m in model_list)
        fallback_map = [{"primary": ["fallback"]}, {"reasoning": ["fallback"]}] if has_fallback else []

        self._router = Router(
            model_list=model_list,
            fallbacks=fallback_map,
            num_retries=2,
            timeout=25,
        )

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
            for chunk in self._mock_response(messages).split(" "):
                yield chunk + " "
            return

        self._build_router()

        try:
            stream = await self._router.acompletion(  # type: ignore[union-attr]
                model=model_alias,
                messages=messages,
                stream=True,
            )
            async for chunk in stream:
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
        if "gap" in last or "unexplored" in last or "missing_connections" in last:
            return json.dumps(_MOCK_GAPS)
        if "critic" in last or "counter-argument" in last or "critique" in last:
            return json.dumps({h["id"]: "The proposed mechanism requires direct experimental validation; correlation in the cited studies does not confirm causation in the target cell type." for h in _MOCK_HYPOTHESES})
        if "rank" in last:
            return json.dumps([{"id": "paper_001", "score": 0.95}, {"id": "paper_002", "score": 0.88}])
        return _MOCK_SUMMARY


llm_service = LLMService()
