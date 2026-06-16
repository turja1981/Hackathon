from __future__ import annotations

from fastapi import APIRouter
from app.models.schemas import AdoptionMetrics
from app.services.metrics import adoption_counter
from app.services.vector_store import vector_store

router = APIRouter()


@router.get("/metrics/adoption", response_model=AdoptionMetrics)
async def get_adoption_metrics():
    """Return live adoption KPI counters (KPI 7: User Adoption)."""
    return AdoptionMetrics(
        papers_processed=adoption_counter.papers_processed + vector_store.paper_count,
        hypotheses_generated=adoption_counter.hypotheses_generated,
        gaps_identified=adoption_counter.gaps_identified,
        queries_total=adoption_counter.queries_total,
    )
