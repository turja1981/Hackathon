from __future__ import annotations

from fastapi import APIRouter, HTTPException
from app.services.vector_store import vector_store

router = APIRouter()


@router.get("/papers/{paper_id}")
async def get_paper(paper_id: str):
    paper = vector_store.get_by_id(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail=f"Paper {paper_id} not found")
    return paper


@router.get("/papers")
async def list_papers(limit: int = 20, offset: int = 0):
    all_papers = vector_store._papers[offset: offset + limit]
    return {"papers": all_papers, "total": vector_store.paper_count, "offset": offset, "limit": limit}
