from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from app.models.schemas import JobStatus


class Job:
    def __init__(self, job_id: str) -> None:
        self.job_id = job_id
        self.status = JobStatus.PENDING
        self.queue: asyncio.Queue[Optional[Dict[str, Any]]] = asyncio.Queue()
        self.result: Optional[Dict[str, Any]] = None
        self.error: Optional[str] = None
        self.created_at = datetime.now(timezone.utc)
        self.completed_at: Optional[datetime] = None


class JobStore:
    """In-memory job store with TTL-based cleanup."""

    def __init__(self, ttl_seconds: int = 3600) -> None:
        self._jobs: Dict[str, Job] = {}
        self._ttl = ttl_seconds

    def create(self, job_id: str) -> Job:
        job = Job(job_id)
        self._jobs[job_id] = job
        self._cleanup()
        return job

    def get(self, job_id: str) -> Optional[Job]:
        return self._jobs.get(job_id)

    def complete(self, job_id: str, result: Dict[str, Any]) -> None:
        job = self._jobs.get(job_id)
        if job:
            job.status = JobStatus.COMPLETED
            job.result = result
            job.completed_at = datetime.now(timezone.utc)
            job.queue.put_nowait(None)  # sentinel to close stream

    def fail(self, job_id: str, error: str) -> None:
        job = self._jobs.get(job_id)
        if job:
            job.status = JobStatus.FAILED
            job.error = error
            job.completed_at = datetime.now(timezone.utc)
            job.queue.put_nowait(None)

    def publish(self, job_id: str, event: Dict[str, Any]) -> None:
        job = self._jobs.get(job_id)
        if job:
            job.queue.put_nowait(event)

    def _cleanup(self) -> None:
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=self._ttl)
        stale = [jid for jid, j in self._jobs.items() if j.created_at < cutoff]
        for jid in stale:
            del self._jobs[jid]


job_store = JobStore()
