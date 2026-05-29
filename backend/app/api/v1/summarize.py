from __future__ import annotations

import uuid
from fastapi import APIRouter, BackgroundTasks
from app.agents.graph import run_graph
from app.models.schemas import JobStatus, SummarizeRequest
from app.services.job_store import job_store

router = APIRouter()


@router.post("/summarize")
async def summarize(request: SummarizeRequest, background_tasks: BackgroundTasks):
    """Start summarization workflow. Poll /stream/{job_id} for progress + result."""
    job_id = str(uuid.uuid4())
    job_store.create(job_id)
    background_tasks.add_task(
        run_graph,
        job_id=job_id,
        query=request.query,
        intent="summarize",
        paper_ids=request.paper_ids,
        max_papers=request.max_papers,
    )
    return {
        "job_id": job_id,
        "status": JobStatus.PENDING,
        "stream_url": f"/api/v1/stream/{job_id}",
    }
