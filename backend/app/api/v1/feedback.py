from __future__ import annotations

from fastapi import APIRouter
from app.models.schemas import FeedbackRequest
from app.utils.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)

_feedback_store: list = []


@router.post("/feedback")
async def submit_feedback(request: FeedbackRequest):
    """Human-in-the-loop feedback (KPI 2: accuracy rating 1-10)."""
    record = request.model_dump()
    _feedback_store.append(record)
    logger.info("feedback_received", **{k: v for k, v in record.items() if v is not None})
    return {"status": "accepted", "message": "Feedback recorded. Thank you for improving the system."}


@router.get("/feedback/stats")
async def feedback_stats():
    """Returns KPI 2 (summary accuracy) and overall feedback statistics."""
    total = len(_feedback_store)
    accepted = sum(1 for f in _feedback_store if f["feedback_type"] == "accept")
    rejected = sum(1 for f in _feedback_store if f["feedback_type"] == "reject")
    flagged  = sum(1 for f in _feedback_store if f["feedback_type"] == "flag")

    # KPI 2: Summary Accuracy Score (1-10 scale, target ≥ 8.5)
    ratings = [f["accuracy_rating"] for f in _feedback_store if f.get("accuracy_rating") is not None]
    avg_accuracy = round(sum(ratings) / len(ratings), 2) if ratings else None

    return {
        "total_feedback": total,
        "accepted": accepted,
        "rejected": rejected,
        "flagged": flagged,
        "kpi_summary_accuracy": {
            "average_rating": avg_accuracy,
            "rating_count": len(ratings),
            "target": 8.5,
            "target_met": avg_accuracy >= 8.5 if avg_accuracy is not None else None,
            "scale": "1-10",
        },
    }
