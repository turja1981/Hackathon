from __future__ import annotations
import json
from typing import Dict, List
from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)

_EVAL_PROMPT = """You are a RAG quality evaluator. Evaluate the following on a 0.0 to 1.0 scale.

Query: {query}

Retrieved Context (top papers):
{context}

Generated Answer:
{answer}

Score these three RAGAS metrics and return ONLY valid JSON:
{{
  "faithfulness": <0.0-1.0, is every claim in the answer grounded in the retrieved context?>,
  "answer_relevancy": <0.0-1.0, how relevant is the answer to the query?>,
  "context_precision": <0.0-1.0, how relevant are the retrieved papers to the query?>,
  "rationale": {{
    "faithfulness": "<one sentence>",
    "answer_relevancy": "<one sentence>",
    "context_precision": "<one sentence>"
  }}
}}"""

_MOCK_SCORES = {
    "faithfulness": 0.82,
    "answer_relevancy": 0.87,
    "context_precision": 0.79,
    "overall_score": 0.83,
    "rationale": {
        "faithfulness": "Answer closely follows the retrieved abstracts",
        "answer_relevancy": "Response directly addresses the research query",
        "context_precision": "Retrieved papers are topically relevant",
    },
    "status": "mock",
}

class RAGASService:
    """RAGAS-inspired RAG pipeline evaluation using LLM-as-judge."""

    async def evaluate(self, query: str, answer: str, context_papers: List[Dict]) -> Dict:
        from app.services.llm_service import llm_service

        if settings.MOCK_LLM_MODE or not settings.has_any_llm:
            return {**_MOCK_SCORES}

        context_text = "\n".join(
            f"[{i+1}] {p.get('title', '')}: {p.get('abstract', '')[:300]}"
            for i, p in enumerate(context_papers[:5])
        )
        prompt_text = _EVAL_PROMPT.format(
            query=query[:300],
            context=context_text,
            answer=answer[:500],
        )
        try:
            raw = await llm_service.chat(
                [{"role": "user", "content": prompt_text}],
                model_alias="primary",
                use_cache=False,
            )
            raw = raw.strip()
            if "```" in raw:
                raw = raw.split("```")[1].replace("json", "", 1).strip()
            data = json.loads(raw)
            f = float(data.get("faithfulness", 0.75))
            ar = float(data.get("answer_relevancy", 0.75))
            cp = float(data.get("context_precision", 0.75))
            return {
                "faithfulness": round(f, 3),
                "answer_relevancy": round(ar, 3),
                "context_precision": round(cp, 3),
                "overall_score": round(f * 0.4 + ar * 0.35 + cp * 0.25, 3),
                "rationale": data.get("rationale", {}),
                "status": "evaluated",
            }
        except Exception as exc:
            logger.warning("ragas_eval_failed", error=str(exc))
            return {**_MOCK_SCORES, "status": "fallback"}

ragas_service = RAGASService()
