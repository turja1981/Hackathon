from __future__ import annotations

import uuid
from fastapi import APIRouter, BackgroundTasks, HTTPException
from app.agents.graph import run_graph
from app.models.schemas import JobStatus, SearchRequest, SearchResponse, Paper
from app.services.guardrail_service import guardrail_service
from app.services.pii_service import pii_service
from app.services.ragas_service import ragas_service
from app.services.reports_store import reports_store
from app.services.job_store import job_store
from app.services.vector_store import vector_store

router = APIRouter()


@router.post("/search", response_model=SearchResponse)
async def search_papers(request: SearchRequest) -> SearchResponse:
    """Synchronous semantic + keyword search with PII masking and retrieval quality scoring."""
    # Topic restriction
    on_topic, reason = guardrail_service.is_on_topic(request.query)
    if not on_topic:
        raise HTTPException(status_code=422, detail=reason)

    # PII mask the query before processing
    masked_query, pii_entities = pii_service.mask(request.query)
    reports_store.record_pii(
        query_preview=masked_query[:80],
        entities=pii_entities,
        backend=pii_service.backend,
    )

    # Retrieve papers using the masked query
    papers_raw = vector_store.search(masked_query, k=request.max_results)
    papers = [Paper(**{k: v for k, v in p.items() if k in Paper.model_fields}) for p in papers_raw]

    # RAGAS retrieval-quality evaluation (always dynamic, never hardcoded)
    ragas_scores = await ragas_service.evaluate_retrieval(masked_query, papers_raw)
    reports_store.record_ragas(query_preview=masked_query[:80], scores=ragas_scores)

    responsible_ai = {
        "pii_report": {
            "entities": pii_entities,
            "backend": pii_service.backend,
        },
        "ragas_evaluation": ragas_scores,
        "guardrail_report": None,
    }

    return SearchResponse(
        query=request.query,
        papers=papers,
        total=len(papers),
        responsible_ai=responsible_ai,
    )


@router.post("/search/async")
async def search_papers_async(request: SearchRequest, background_tasks: BackgroundTasks):
    """Async search with LLM reranking via SSE stream."""
    on_topic, reason = guardrail_service.is_on_topic(request.query)
    if not on_topic:
        raise HTTPException(status_code=422, detail=reason)
    job_id = str(uuid.uuid4())
    job_store.create(job_id)
    background_tasks.add_task(
        run_graph,
        job_id=job_id,
        query=request.query,
        intent="search",
        max_papers=request.max_results,
    )
    return {"job_id": job_id, "status": JobStatus.PENDING, "stream_url": f"/api/v1/stream/{job_id}"}
