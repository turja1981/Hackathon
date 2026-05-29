from __future__ import annotations

import uuid
from fastapi import APIRouter
from app.models.schemas import IngestRequest, IngestResponse
from app.services.vector_store import vector_store
from app.utils.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("/ingest", response_model=IngestResponse)
async def ingest_papers(request: IngestRequest) -> IngestResponse:
    papers = [
        {**p.model_dump(), "id": p.doi.replace("/", "_") if p.doi else str(uuid.uuid4())}
        for p in request.papers
    ]
    ids = vector_store.add_papers(papers)
    logger.info("ingested", count=len(ids))
    return IngestResponse(
        ingested_count=len(ids),
        paper_ids=ids,
        message=f"Successfully ingested {len(ids)} papers into the vector store.",
    )
