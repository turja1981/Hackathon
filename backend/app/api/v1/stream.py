from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, HTTPException
from sse_starlette.sse import EventSourceResponse

from app.models.schemas import JobStatus
from app.services.job_store import job_store

router = APIRouter()

_SSE_TIMEOUT = 120  # seconds


@router.get("/stream/{job_id}")
async def stream_job(job_id: str):
    """Server-Sent Events endpoint for real-time agent progress."""
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    async def event_generator():
        # Yield a heartbeat immediately so the client knows the stream started
        yield {"event": "connected", "data": json.dumps({"job_id": job_id, "status": "connected"})}

        while True:
            try:
                event = await asyncio.wait_for(job.queue.get(), timeout=_SSE_TIMEOUT)
            except asyncio.TimeoutError:
                yield {"event": "heartbeat", "data": "{}"}
                continue

            if event is None:
                # Job completed or failed
                result_payload = {
                    "job_id": job_id,
                    "status": job.status.value,
                    "result": job.result,
                    "error": job.error,
                }
                yield {"event": "done", "data": json.dumps(result_payload, default=str)}
                break

            yield {"event": "agent_update", "data": json.dumps(event, default=str)}

    return EventSourceResponse(event_generator())


@router.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Poll-based alternative to SSE for job status."""
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return {
        "job_id": job_id,
        "status": job.status.value,
        "result": job.result,
        "error": job.error,
    }
