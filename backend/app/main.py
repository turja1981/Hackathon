from __future__ import annotations

from contextlib import asynccontextmanager
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import ingest, papers, search, summarize, hypothesize, stream, feedback
from app.config import settings
from app.models.schemas import HealthResponse
from app.services.vector_store import vector_store
from app.utils.logging import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("startup", mock_mode=settings.MOCK_LLM_MODE, has_llm=settings.has_any_llm)
    # Preload FAISS index from sample data on startup
    sample_path = os.path.join(os.path.dirname(__file__), "..", "data", "sample_papers.json")
    vector_store.load_or_build(papers_json_path=sample_path)
    logger.info("vector_store_ready", papers=vector_store.paper_count)
    yield
    logger.info("shutdown")


app = FastAPI(
    title="Life Sciences AI - Research Paper Summarization & Hypothesis Generation",
    description=(
        "Production-grade multi-agent system for life sciences researchers. "
        "Powered by LangGraph, LiteLLM (GPT-4o / Gemini 1.5 Pro), and FAISS."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routes
PREFIX = "/api/v1"
app.include_router(ingest.router, prefix=PREFIX, tags=["Ingest"])
app.include_router(papers.router, prefix=PREFIX, tags=["Papers"])
app.include_router(search.router, prefix=PREFIX, tags=["Search"])
app.include_router(summarize.router, prefix=PREFIX, tags=["Summarize"])
app.include_router(hypothesize.router, prefix=PREFIX, tags=["Hypothesize"])
app.include_router(stream.router, prefix=PREFIX, tags=["Stream"])
app.include_router(feedback.router, prefix=PREFIX, tags=["Feedback"])


@app.get("/api/v1/health", response_model=HealthResponse, tags=["Health"])
async def health():
    return HealthResponse(
        status="ok",
        llm_configured=settings.has_any_llm,
        vector_store_loaded=vector_store.paper_count > 0,
        paper_count=vector_store.paper_count,
        mock_mode=settings.MOCK_LLM_MODE or not settings.has_any_llm,
    )


@app.get("/", include_in_schema=False)
async def root():
    return {"message": "Life Sciences AI API", "docs": "/docs", "health": "/api/v1/health"}
