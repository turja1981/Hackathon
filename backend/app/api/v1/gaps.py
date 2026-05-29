from __future__ import annotations

import uuid
from fastapi import APIRouter, BackgroundTasks
from app.agents.graph import run_graph
from app.models.schemas import GapsRequest, JobStatus
from app.services.job_store import job_store
from app.services.metrics import adoption_counter

router = APIRouter()


@router.post("/gaps")
async def detect_gaps(request: GapsRequest, background_tasks: BackgroundTasks):
    """Start research gap detection. Poll /stream/{job_id} for progress + result."""
    job_id = str(uuid.uuid4())
    job_store.create(job_id)
    adoption_counter.queries_total += 1
    adoption_counter.gaps_identified += request.max_gaps
    background_tasks.add_task(
        run_graph,
        job_id=job_id,
        query=request.query,
        intent="gaps",
        max_papers=request.max_gaps,
    )
    return {
        "job_id": job_id,
        "status": JobStatus.PENDING,
        "stream_url": f"/api/v1/stream/{job_id}",
    }
