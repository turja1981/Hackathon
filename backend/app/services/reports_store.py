from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

@dataclass
class PIIEvent:
    timestamp: str
    query_preview: str          # first 80 chars of masked query
    entities: List[Dict]        # [{entity_type, score, text}] (text is already masked)
    entity_count: int
    entity_types: List[str]
    backend: str                # "presidio" | "regex"
    masked: bool

@dataclass
class RAGASEval:
    timestamp: str
    query_preview: str
    faithfulness: float
    answer_relevancy: float
    context_precision: float
    overall_score: float
    status: str                 # "evaluated" | "mock" | "fallback"

@dataclass
class GuardrailEvent:
    timestamp: str
    query_preview: str
    agent: str
    passed: bool
    checks: Dict[str, bool]
    violations: List[str]
    pii_in_output_count: int

class ReportsStore:
    _MAX = 200

    def __init__(self):
        self.pii_events: List[PIIEvent] = []
        self.ragas_evals: List[RAGASEval] = []
        self.guardrail_events: List[GuardrailEvent] = []

    def _trim(self, lst: list) -> None:
        if len(lst) > self._MAX:
            del lst[: len(lst) - self._MAX]

    def record_pii(
        self,
        query_preview: str,
        entities: List[Dict],
        backend: str,
    ) -> None:
        event = PIIEvent(
            timestamp=_now(),
            query_preview=query_preview,
            entities=[{"entity_type": e["entity_type"], "score": e["score"]} for e in entities],
            entity_count=len(entities),
            entity_types=sorted({e["entity_type"] for e in entities}),
            backend=backend,
            masked=len(entities) > 0,
        )
        self.pii_events.append(event)
        self._trim(self.pii_events)

    def record_ragas(self, query_preview: str, scores: Dict) -> None:
        event = RAGASEval(
            timestamp=_now(),
            query_preview=query_preview,
            faithfulness=scores.get("faithfulness", 0.0),
            answer_relevancy=scores.get("answer_relevancy", 0.0),
            context_precision=scores.get("context_precision", 0.0),
            overall_score=scores.get("overall_score", 0.0),
            status=scores.get("status", "unknown"),
        )
        self.ragas_evals.append(event)
        self._trim(self.ragas_evals)

    def record_guardrail(self, query_preview: str, result: Dict) -> None:
        event = GuardrailEvent(
            timestamp=_now(),
            query_preview=query_preview,
            agent=result.get("agent", "unknown"),
            passed=result.get("passed", True),
            checks=result.get("checks", {}),
            violations=result.get("violations", []),
            pii_in_output_count=len(result.get("pii_in_output", [])),
        )
        self.guardrail_events.append(event)
        self._trim(self.guardrail_events)

    # ---- Aggregate helpers used by the API ----

    def pii_summary(self) -> Dict:
        total = len(self.pii_events)
        flagged = sum(1 for e in self.pii_events if e.masked)
        type_counts: Dict[str, int] = {}
        for ev in self.pii_events:
            for t in ev.entity_types:
                type_counts[t] = type_counts.get(t, 0) + 1
        return {
            "total_queries_scanned": total,
            "queries_with_pii": flagged,
            "pii_rate_pct": round(flagged / total * 100, 1) if total else 0,
            "entity_type_counts": type_counts,
            "backend": self.pii_events[-1].backend if self.pii_events else "none",
            "recent_events": [
                {
                    "timestamp": e.timestamp,
                    "query_preview": e.query_preview,
                    "entity_count": e.entity_count,
                    "entity_types": e.entity_types,
                    "masked": e.masked,
                }
                for e in reversed(self.pii_events[-20:])
            ],
        }

    def ragas_summary(self) -> Dict:
        evals = self.ragas_evals
        if not evals:
            return {"total_evaluations": 0, "avg_scores": {}, "recent_evals": []}
        def avg(attr: str) -> float:
            return round(sum(getattr(e, attr) for e in evals) / len(evals), 3)
        return {
            "total_evaluations": len(evals),
            "avg_scores": {
                "faithfulness": avg("faithfulness"),
                "answer_relevancy": avg("answer_relevancy"),
                "context_precision": avg("context_precision"),
                "overall": avg("overall_score"),
            },
            "recent_evals": [
                {
                    "timestamp": e.timestamp,
                    "query_preview": e.query_preview,
                    "faithfulness": e.faithfulness,
                    "answer_relevancy": e.answer_relevancy,
                    "context_precision": e.context_precision,
                    "overall_score": e.overall_score,
                    "status": e.status,
                }
                for e in reversed(evals[-20:])
            ],
        }

    def guardrail_summary(self) -> Dict:
        evs = self.guardrail_events
        if not evs:
            return {"total_validations": 0, "pass_rate_pct": 100, "recent_events": []}
        passed = sum(1 for e in evs if e.passed)
        violation_counts: Dict[str, int] = {}
        for ev in evs:
            for v in ev.violations:
                key = v.split(":")[0].strip()
                violation_counts[key] = violation_counts.get(key, 0) + 1
        return {
            "total_validations": len(evs),
            "passed": passed,
            "failed": len(evs) - passed,
            "pass_rate_pct": round(passed / len(evs) * 100, 1),
            "violation_breakdown": violation_counts,
            "recent_events": [
                {
                    "timestamp": e.timestamp,
                    "query_preview": e.query_preview,
                    "agent": e.agent,
                    "passed": e.passed,
                    "checks": e.checks,
                    "violations": e.violations,
                    "pii_in_output": e.pii_in_output_count,
                }
                for e in reversed(evs[-20:])
            ],
        }

reports_store = ReportsStore()
