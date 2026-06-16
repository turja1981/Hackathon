from __future__ import annotations

import uuid
from fastapi import APIRouter, BackgroundTasks, HTTPException
from app.agents.graph import run_graph
from app.models.schemas import HypothesizeRequest, JobStatus
from app.services.guardrail_service import guardrail_service
from app.services.job_store import job_store
from app.services.metrics import adoption_counter

router = APIRouter()


@router.post("/hypothesize")
async def hypothesize(request: HypothesizeRequest, background_tasks: BackgroundTasks):
    """Start hypothesis generation workflow. Stream progress via /stream/{job_id}."""
    on_topic, reason = guardrail_service.is_on_topic(request.query)
    if not on_topic:
        raise HTTPException(status_code=422, detail=reason)
    job_id = str(uuid.uuid4())
    job_store.create(job_id)
    adoption_counter.queries_total += 1
    adoption_counter.hypotheses_generated += request.num_hypotheses
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
