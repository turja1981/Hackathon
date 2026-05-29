from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
import uuid


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentName(str, Enum):
    ORCHESTRATOR = "orchestrator"
    SEARCH = "search"
    RANKER = "ranker"
    SUMMARIZER = "summarizer"
    HYPOTHESIS = "hypothesis"
    GAP_DETECTOR = "gap_detector"
    CRITIC = "critic"


class FeedbackType(str, Enum):
    ACCEPT = "accept"
    REJECT = "reject"
    FLAG = "flag"


# ---------------------------------------------------------------------------
# Paper models
# ---------------------------------------------------------------------------

class Paper(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    authors: List[str] = []
    journal: Optional[str] = None
    year: Optional[int] = None
    doi: Optional[str] = None
    abstract: str
    keywords: List[str] = []
    publication_date: Optional[str] = None
    score: Optional[float] = None
    rerank_score: Optional[float] = None
    # PubMed-specific fields
    pmid: Optional[str] = None
    url: Optional[str] = None        # e.g. https://pubmed.ncbi.nlm.nih.gov/{pmid}/
    source: Optional[str] = None     # "pubmed" | "uploaded" | None (static)


class PaperIngest(BaseModel):
    title: str
    authors: List[str] = []
    journal: Optional[str] = None
    year: Optional[int] = None
    doi: Optional[str] = None
    abstract: str
    keywords: List[str] = []
    publication_date: Optional[str] = None


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class IngestRequest(BaseModel):
    papers: List[PaperIngest]


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    max_results: int = Field(default=10, ge=1, le=50)
    use_semantic: bool = True


class SummarizeRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    paper_ids: Optional[List[str]] = None
    max_papers: int = Field(default=5, ge=1, le=20)


class HypothesizeRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    paper_ids: Optional[List[str]] = None
    num_hypotheses: int = Field(default=3, ge=1, le=10)
    focus_area: Optional[str] = None


class Citation(BaseModel):
    paper_id: str
    paper_title: str
    claim: str


class FeedbackRequest(BaseModel):
    job_id: str
    item_id: str
    feedback_type: FeedbackType
    # KPI 2: Summary accuracy rating on 1-10 scale (≥ 8.5 target)
    accuracy_rating: Optional[int] = Field(default=None, ge=1, le=10)
    comment: Optional[str] = None


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class JobResponse(BaseModel):
    job_id: str
    status: JobStatus
    message: str = ""


class IngestResponse(BaseModel):
    ingested_count: int
    paper_ids: List[str]
    message: str


class SearchResponse(BaseModel):
    query: str
    papers: List[Paper]
    total: int
    job_id: Optional[str] = None


class ReasoningStep(BaseModel):
    paper_id: str
    paper_title: str
    finding: str
    relevance: str


class EvidenceScore(BaseModel):
    overall_score: float         # 0-100
    supporting_papers_count: int
    recency_score: float         # 0-1
    agreement_score: float       # 0-1
    citation_impact_score: float # 0-1
    label: str                   # "Strong" | "Moderate" | "Weak"


class ResearchGap(BaseModel):
    id: str
    gap_description: str
    area: str
    opportunity_level: str       # "High" | "Medium" | "Low"
    missing_connections: List[str] = []
    suggested_experiments: List[str] = []
    novelty_score: float = 0.8
    related_paper_ids: List[str] = []


class Hypothesis(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    hypothesis: str
    rationale: str
    experiments: List[str] = []
    novelty_score: float = Field(default=0.8, ge=0.0, le=1.0)
    impact_area: str = ""
    supporting_paper_ids: List[str] = []
    reasoning_path: List[ReasoningStep] = []
    evidence_score: Optional[EvidenceScore] = None
    critic_challenge: str = ""


class SummarizeResponse(BaseModel):
    query: str
    summary: str
    key_findings: List[str] = []
    papers_used: List[Paper] = []
    job_id: Optional[str] = None


class HypothesizeResponse(BaseModel):
    query: str
    hypotheses: List[Hypothesis] = []
    context_summary: str = ""
    papers_used: List[Paper] = []
    job_id: Optional[str] = None


# ---------------------------------------------------------------------------
# SSE event models
# ---------------------------------------------------------------------------

class AgentEvent(BaseModel):
    job_id: str
    agent: AgentName
    status: str
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class JobResult(BaseModel):
    job_id: str
    status: JobStatus
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    completed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class GapsRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    max_gaps: int = Field(default=5, ge=1, le=10)


class CopilotRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    conversation_history: List[Dict[str, str]] = Field(default_factory=list)


class AdoptionMetrics(BaseModel):
    papers_processed: int = 0
    hypotheses_generated: int = 0
    gaps_identified: int = 0
    queries_total: int = 0


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

class HealthResponse(BaseModel):
    status: str
    version: str = "1.0.0"
    llm_configured: bool
    vector_store_loaded: bool
    paper_count: int
    mock_mode: bool
