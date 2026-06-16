from __future__ import annotations
import json
import re
from typing import Dict, List
from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)

_STOP_WORDS = {"the", "a", "an", "of", "in", "for", "and", "or", "with", "to",
               "is", "are", "was", "were", "be", "by", "at", "on", "as", "it",
               "this", "that", "its", "from", "into", "has", "have", "had"}

_EVAL_PROMPT = """You are a RAG quality evaluator for a life sciences research platform.
Evaluate the following retrieval-augmented generation output on a 0.0 to 1.0 scale.

Query: {query}

Retrieved Context (top papers):
{context}

Generated Answer:
{answer}

Score these three metrics and return ONLY valid JSON with no markdown:
{{
  "faithfulness": <0.0-1.0 — every factual claim in the answer is grounded in the retrieved context>,
  "answer_relevancy": <0.0-1.0 — the answer directly addresses what the query asked>,
  "context_precision": <0.0-1.0 — the retrieved papers are genuinely relevant to the query>,
  "rationale": {{
    "faithfulness": "<one sentence explanation>",
    "answer_relevancy": "<one sentence explanation>",
    "context_precision": "<one sentence explanation>"
  }}
}}"""


# ---------------------------------------------------------------------------
# Heuristic scorers (always run — give real signal without an LLM call)
# ---------------------------------------------------------------------------

def _query_terms(query: str) -> set[str]:
    words = re.sub(r'[^\w\s]', ' ', query.lower()).split()
    return {w for w in words if len(w) > 2 and w not in _STOP_WORDS}


def _context_precision(query: str, papers: List[Dict]) -> float:
    """Fraction of retrieved papers that visibly relate to the query."""
    terms = _query_terms(query)
    if not terms or not papers:
        return 0.75
    hits = []
    for p in papers[:5]:
        text = " ".join([
            p.get("title", ""),
            p.get("abstract", "")[:400],
            " ".join(p.get("keywords", [])),
        ]).lower()
        matched = sum(1 for t in terms if t in text)
        hits.append(matched / len(terms))
    return round(min(sum(hits) / len(hits), 1.0), 3)


def _answer_relevancy(query: str, answer: str) -> float:
    """Fraction of query terms addressed in the answer."""
    if not answer:
        return 0.75
    terms = _query_terms(query)
    if not terms:
        return 0.80
    answer_lower = answer.lower()
    matched = sum(1 for t in terms if t in answer_lower)
    # Normalise: even 60% term coverage counts as ~0.85+
    ratio = matched / len(terms)
    return round(min(0.55 + ratio * 0.45, 1.0), 3)


def _faithfulness(answer: str, papers: List[Dict]) -> float:
    """Proxy: does the answer reference or echo paper content?"""
    if not answer or not papers:
        return 0.75
    answer_lower = answer.lower()
    refs = 0
    for p in papers[:5]:
        pid = p.get("id", "")
        title_tokens = [w for w in p.get("title", "").lower().split() if len(w) > 4][:4]
        if pid in answer_lower or any(w in answer_lower for w in title_tokens):
            refs += 1
    # 0 refs → 0.65 baseline (may still be faithful), all cited → 0.95
    return round(0.65 + (refs / max(len(papers[:5]), 1)) * 0.30, 3)


def _compute_overall(f: float, ar: float, cp: float) -> float:
    return round(f * 0.4 + ar * 0.35 + cp * 0.25, 3)


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

class RAGASService:
    """
    RAG pipeline quality evaluation.

    Two modes:
    - LLM available: LLM-as-judge (authoritative scores + rationale)
    - Mock / no LLM: heuristic text-overlap scoring (dynamic, query-dependent)
    """

    async def evaluate(self, query: str, answer: str, context_papers: List[Dict]) -> Dict:
        """Full evaluation for summarize / hypothesize results."""
        # Always compute heuristic scores first — used as fallback and validation
        h_cp = _context_precision(query, context_papers)
        h_ar = _answer_relevancy(query, answer)
        h_f  = _faithfulness(answer, context_papers)

        if settings.MOCK_LLM_MODE or not settings.has_any_llm:
            return {
                "faithfulness": h_f,
                "answer_relevancy": h_ar,
                "context_precision": h_cp,
                "overall_score": _compute_overall(h_f, h_ar, h_cp),
                "rationale": {
                    "faithfulness": f"Proxy: answer references {sum(1 for p in context_papers[:5] if any(w in answer.lower() for w in p.get('title','').lower().split()[:4] if len(w)>4))} of {min(len(context_papers),5)} retrieved papers",
                    "answer_relevancy": f"Query-term coverage in answer: {round(_query_terms(query) and sum(1 for t in _query_terms(query) if t in answer.lower()) / len(_query_terms(query)) * 100 if _query_terms(query) else 75)}%",
                    "context_precision": f"Retrieved papers with query-term overlap: {round(h_cp * 100)}%",
                },
                "status": "heuristic",
            }

        from app.services.llm_service import llm_service
        context_text = "\n".join(
            f"[{i+1}] {p.get('title', '')}: {p.get('abstract', '')[:300]}"
            for i, p in enumerate(context_papers[:5])
        )
        prompt_text = _EVAL_PROMPT.format(
            query=query[:300],
            context=context_text,
            answer=answer[:600],
        )
        try:
            raw = await llm_service.chat(
                [{"role": "user", "content": prompt_text}],
                model_alias="primary",
                use_cache=False,
            )
            raw = raw.strip()
            # Strip markdown fences
            if "```" in raw:
                raw = raw[raw.find("{"):raw.rfind("}")+1]
            data = json.loads(raw)
            f  = max(0.0, min(1.0, float(data.get("faithfulness", h_f))))
            ar = max(0.0, min(1.0, float(data.get("answer_relevancy", h_ar))))
            cp = max(0.0, min(1.0, float(data.get("context_precision", h_cp))))
            return {
                "faithfulness": round(f, 3),
                "answer_relevancy": round(ar, 3),
                "context_precision": round(cp, 3),
                "overall_score": _compute_overall(f, ar, cp),
                "rationale": data.get("rationale", {}),
                "status": "llm_evaluated",
            }
        except Exception as exc:
            logger.warning("ragas_llm_eval_failed", error=str(exc))
            # Fall through to heuristic scores (never return hardcoded values)
            return {
                "faithfulness": h_f,
                "answer_relevancy": h_ar,
                "context_precision": h_cp,
                "overall_score": _compute_overall(h_f, h_ar, h_cp),
                "rationale": {"error": str(exc)},
                "status": "heuristic_fallback",
            }

    async def evaluate_retrieval(self, query: str, papers: List[Dict]) -> Dict:
        """
        Retrieval-only evaluation for the sync search endpoint.
        Faithfulness is not applicable (no generated text); answer_relevancy
        proxies whether the top result matches the query intent.
        """
        cp = _context_precision(query, papers)
        # For retrieval: relevancy = did the top paper's title relate to the query?
        top_title = papers[0].get("title", "") if papers else ""
        ar = _answer_relevancy(query, top_title) if top_title else 0.75
        # Faithfulness N/A for pure retrieval → set to 1.0 (no generation risk)
        f = 1.0
        return {
            "faithfulness": f,
            "answer_relevancy": ar,
            "context_precision": cp,
            "overall_score": _compute_overall(f, ar, cp),
            "rationale": {
                "faithfulness": "No generated text — faithfulness not applicable for search results",
                "answer_relevancy": f"Top result relevance to query: {round(ar * 100)}%",
                "context_precision": f"Retrieved papers with query-term overlap: {round(cp * 100)}%",
            },
            "status": "retrieval_eval",
        }

ragas_service = RAGASService()
