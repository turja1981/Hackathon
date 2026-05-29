from __future__ import annotations

from fastapi import APIRouter
from app.models.schemas import FeedbackRequest
from app.utils.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)

# In production this would persist to a database and feed into RLHF pipeline
_feedback_store: list = []


@router.post("/feedback")
async def submit_feedback(request: FeedbackRequest):
    """Human-in-the-loop feedback endpoint for hypothesis/summary quality."""
    record = request.model_dump()
    _feedback_store.append(record)
    logger.info("feedback_received", **record)
    return {"status": "accepted", "message": "Feedback recorded. Thank you for improving the system."}


@router.get("/feedback/stats")
async def feedback_stats():
    total = len(_feedback_store)
    accepted = sum(1 for f in _feedback_store if f["feedback_type"] == "accept")
    rejected = sum(1 for f in _feedback_store if f["feedback_type"] == "reject")
    flagged = sum(1 for f in _feedback_store if f["feedback_type"] == "flag")
    return {"total": total, "accepted": accepted, "rejected": rejected, "flagged": flagged}
