from __future__ import annotations

import uuid
from fastapi import APIRouter, BackgroundTasks
from app.agents.graph import run_graph
from app.models.schemas import HypothesizeRequest, JobStatus
from app.services.job_store import job_store

router = APIRouter()


@router.post("/hypothesize")
async def hypothesize(request: HypothesizeRequest, background_tasks: BackgroundTasks):
    """Start hypothesis generation workflow. Stream progress via /stream/{job_id}."""
    job_id = str(uuid.uuid4())
    job_store.create(job_id)
    background_tasks.add_task(
        run_graph,
        job_id=job_id,
        query=request.query,
        intent="hypothesize",
        paper_ids=request.paper_ids,
        focus_area=request.focus_area,
        num_hypotheses=request.num_hypotheses,
    )
    return {
        "job_id": job_id,
        "status": JobStatus.PENDING,
        "stream_url": f"/api/v1/stream/{job_id}",
    }
