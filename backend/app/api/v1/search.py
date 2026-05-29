from __future__ import annotations

import uuid
from fastapi import APIRouter, BackgroundTasks
from app.agents.graph import run_graph
from app.models.schemas import JobStatus, SearchRequest, SearchResponse, Paper
from app.services.job_store import job_store
from app.services.vector_store import vector_store
from app.config import settings

router = APIRouter()


@router.post("/search", response_model=SearchResponse)
async def search_papers(request: SearchRequest) -> SearchResponse:
    """Synchronous semantic + keyword search (fast path, no LLM reranking)."""
    papers_raw = vector_store.search(request.query, k=request.max_results)
    papers = [Paper(**{k: v for k, v in p.items() if k in Paper.model_fields}) for p in papers_raw]
    return SearchResponse(query=request.query, papers=papers, total=len(papers))


@router.post("/search/async")
async def search_papers_async(request: SearchRequest, background_tasks: BackgroundTasks):
    """Async search with LLM reranking via SSE stream."""
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
