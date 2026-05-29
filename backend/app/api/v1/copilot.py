from __future__ import annotations

import uuid
from fastapi import APIRouter, BackgroundTasks
from app.agents.graph import run_graph
from app.models.schemas import CopilotRequest, JobStatus
from app.services.job_store import job_store
from app.services.metrics import adoption_counter

router = APIRouter()


def _detect_intent(message: str) -> str:
    msg = message.lower()
    if any(w in msg for w in ["gap", "missing", "unexplored", "unknown research", "what's missing"]):
        return "gaps"
    if any(w in msg for w in ["hypothesis", "hypothesize", "novel direction", "suggest experiment", "what could"]):
        return "hypothesize"
    return "summarize"


@router.post("/copilot")
async def research_copilot(request: CopilotRequest, background_tasks: BackgroundTasks):
    """Research Copilot: auto-detects intent and runs the full agent pipeline."""
    job_id = str(uuid.uuid4())
    job_store.create(job_id)
    adoption_counter.queries_total += 1

    intent = _detect_intent(request.message)
    background_tasks.add_task(
        run_graph,
        job_id=job_id,
        query=request.message,
        intent=intent,
    )
    return {
        "job_id": job_id,
        "status": JobStatus.PENDING,
        "stream_url": f"/api/v1/stream/{job_id}",
        "detected_intent": intent,
    }
