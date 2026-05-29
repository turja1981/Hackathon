# LifeSci AI – Research Paper Summarization & Hypothesis Generation

> **TCS Hackathon 2026** · Production-grade multi-agent AI system for life sciences researchers

[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2-orange)](https://langchain-ai.github.io/langgraph)
[![Next.js](https://img.shields.io/badge/Next.js-14-black)](https://nextjs.org)
[![LiteLLM](https://img.shields.io/badge/LiteLLM-routing-purple)](https://litellm.ai)

---

## Problem Statement

Life sciences researchers face an overwhelming volume of scientific publications, making it difficult to stay current and generate novel research hypotheses. This system addresses that with a production-grade multi-agent AI pipeline that can:

1. **Search** thousands of papers semantically (FAISS vector store)
2. **Summarize** paper collections with key findings extraction
3. **Generate** novel, testable research hypotheses with experimental designs
4. **Stream** real-time agent progress to the UI via SSE

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Next.js 14)                    │
│  Home │ Search │ Paper Detail │ Hypotheses │ Ingest              │
│  SSE streaming · Real-time agent tracker · Human-in-the-loop    │
└────────────────────────┬────────────────────────────────────────┘
                         │ REST + SSE (EventSource)
┌────────────────────────▼────────────────────────────────────────┐
│                   BACKEND (FastAPI + Python)                     │
│                                                                  │
│  POST /api/v1/search        POST /api/v1/summarize              │
│  POST /api/v1/hypothesize   GET  /api/v1/stream/{job_id}        │
│  POST /api/v1/ingest        POST /api/v1/feedback               │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              LangGraph Multi-Agent Pipeline               │   │
│  │                                                           │   │
│  │  ┌──────────────┐     ┌────────────┐     ┌───────────┐  │   │
│  │  │ Orchestrator │────►│   Search   │────►│  Ranker   │  │   │
│  │  │   Agent      │     │   Agent    │     │   Agent   │  │   │
│  │  └──────────────┘     └────────────┘     └─────┬─────┘  │   │
│  │                                                 │         │   │
│  │                          ┌──────────────────────┘         │   │
│  │                          ▼                                │   │
│  │                   ┌────────────┐     ┌──────────────┐    │   │
│  │                   │ Summarizer │────►│  Hypothesis  │    │   │
│  │                   │   Agent    │     │    Agent     │    │   │
│  │                   └────────────┘     └──────────────┘    │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌─────────────────┐  ┌──────────────────┐  ┌───────────────┐  │
│  │   FAISS Index   │  │   LiteLLM Router │  │  Job Store    │  │
│  │  (embeddings)   │  │  GPT-4o/Gemini  │  │  (SSE queue)  │  │
│  └─────────────────┘  └──────────────────┘  └───────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Agent Workflow Sequence

```
User Query
    │
    ▼
[OrchestratorAgent]  ── Detects intent (search / summarize / hypothesize)
    │
    ▼
[SearchAgent]        ── FAISS semantic search → top-K candidate papers
    │
    ▼
[RankerAgent]        ── LLM-based relevance reranking → top-5 papers
    │
    ├──(intent=search)──────────────────────────────────► SSE: results
    │
    ▼
[SummaryAgent]       ── Multi-paper synthesis + key findings extraction
    │
    ├──(intent=summarize)───────────────────────────────► SSE: summary
    │
    ▼
[HypothesisAgent]    ── 3-5 novel hypotheses with experiments + novelty scores
    │
    └──(intent=hypothesize)─────────────────────────────► SSE: hypotheses
```

---

## Directory Structure

```
Hackathon/
├── backend/                    # Python FastAPI backend
│   ├── app/
│   │   ├── main.py             # FastAPI entry point + lifespan
│   │   ├── config.py           # Pydantic settings (all from .env)
│   │   ├── models/
│   │   │   └── schemas.py      # All Pydantic request/response models
│   │   ├── agents/
│   │   │   └── graph.py        # LangGraph StateGraph + all agent nodes
│   │   ├── services/
│   │   │   ├── llm_service.py  # LiteLLM wrapper (routing + caching)
│   │   │   ├── vector_store.py # FAISS vector store
│   │   │   ├── embeddings.py   # sentence-transformers embedding service
│   │   │   └── job_store.py    # In-memory SSE job queue
│   │   ├── api/v1/
│   │   │   ├── ingest.py       # POST /ingest
│   │   │   ├── search.py       # POST /search
│   │   │   ├── summarize.py    # POST /summarize
│   │   │   ├── hypothesize.py  # POST /hypothesize
│   │   │   ├── stream.py       # GET  /stream/{job_id}  (SSE)
│   │   │   └── feedback.py     # POST /feedback
│   │   └── utils/
│   │       └── logging.py      # Structured JSON logging (structlog)
│   ├── data/
│   │   ├── sample_papers.json  # 10 synthetic life sciences papers
│   │   └── faiss_index/        # Persisted FAISS index (auto-built)
│   ├── .env.example
│   └── requirements.txt
│
├── frontend/                   # Next.js 14 frontend
│   ├── app/
│   │   ├── layout.tsx          # Root layout + Navbar
│   │   ├── page.tsx            # Home: hero + search + features
│   │   ├── search/page.tsx     # Search results with paper cards
│   │   ├── paper/[id]/page.tsx # Paper detail + on-demand summary
│   │   ├── hypotheses/page.tsx # Hypothesis generator with SSE
│   │   └── ingest/page.tsx     # Manual paper ingestion form
│   ├── components/
│   │   ├── Navbar.tsx
│   │   ├── SearchBar.tsx
│   │   ├── PaperCard.tsx
│   │   ├── AgentStatusTracker.tsx  # Real-time agent pipeline visualizer
│   │   ├── HypothesisPanel.tsx     # Collapsible hypothesis + HITL feedback
│   │   └── SummaryVisualization.tsx
│   ├── lib/
│   │   ├── types.ts            # TypeScript domain types
│   │   ├── api.ts              # Typed API client
│   │   └── hooks/useSSE.ts     # SSE stream hook
│   ├── .env.local.example
│   ├── package.json
│   ├── tailwind.config.js
│   └── next.config.js
│
└── README.md
```

---

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- (Optional) OpenAI or Google Gemini API key for real LLM responses

### 1. Backend Setup

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env — at minimum set OPENAI_API_KEY or GEMINI_API_KEY
# Without API keys, the system runs in demo mode with pre-generated responses

# Start server (auto-builds FAISS index on first run)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The server will:
- Auto-download `all-MiniLM-L6-v2` embedding model (~80 MB, one time)
- Build and persist a FAISS index from `data/sample_papers.json`
- Start serving on `http://localhost:8000`
- Interactive docs at `http://localhost:8000/docs`

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.local.example .env.local
# NEXT_PUBLIC_API_URL=http://localhost:8000

# Start dev server
npm run dev
```

Frontend runs at `http://localhost:3000`

---

## Environment Configuration

### Backend `.env`

Three provider options — set only one:

**Option A — TCS GenAI Lab MaaS (recommended for hackathon)**

| Variable | Value | Description |
|---|---|---|
| `GENAILAB_API_KEY` | `sk-…` | TCS GenAI Lab API key |
| `GENAILAB_API_BASE` | `https://genailab.tcs.in/` | MaaS endpoint |
| `LITELLM_PRIMARY_MODEL` | `genailab-maas-gpt-4o` | GPT-4o via GenAI Lab |
| `LITELLM_FALLBACK_MODEL` | `gemini-2.5-flash` | Gemini 2.5 Flash via GenAI Lab |
| `LITELLM_REASONING_MODEL` | `genailab-maas-gpt-4o` | For summarisation + hypotheses |

**Option B — Direct OpenAI / Gemini**

| Variable | Value | Description |
|---|---|---|
| `OPENAI_API_KEY` | `sk-…` | OpenAI API key |
| `GEMINI_API_KEY` | `AI…` | Google Gemini API key |
| `LITELLM_PRIMARY_MODEL` | `gpt-4o` | Any OpenAI model |
| `LITELLM_FALLBACK_MODEL` | `gemini/gemini-1.5-pro` | Gemini fallback |

**Common settings**

| Variable | Default | Description |
|---|---|---|
| `LITELLM_CACHE_ENABLED` | `true` | In-memory response cache |
| `LITELLM_CACHE_TTL` | `3600` | Cache TTL in seconds |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Local embeddings (no API key needed) |
| `FAISS_INDEX_PATH` | `./data/faiss_index` | Persisted FAISS index |
| `MAX_RETRIEVED_DOCS` | `10` | Candidates before reranking |
| `RERANK_TOP_K` | `5` | Final docs sent to LLM |
| `MOCK_LLM_MODE` | `false` | Demo mode — no API key needed |

**Available GenAI Lab models (from the platform)**

| Category | Model name |
|---|---|
| GPT-4o | `genailab-maas-gpt-4o` |
| GPT-4.1 | `azure/genailab-maas-gpt-4.1` |
| GPT-5 mini | `azure/genailab-maas-gpt-5-mini` |
| Gemini 2.5 Pro | `gemini-2.5-pro` |
| Gemini 2.5 Flash | `gemini-2.5-flash` |
| DeepSeek V3 | `genailab-maas-DeepSeek-V3-0324` |
| DeepSeek R1 | `azure_ai/genailab-maas-DeepSeek-R1` |
| Llama 4 Maverick | `azure_ai/genailab-maas-Llama-4-Maverick-17B-128E-Instruct-FP8` |
| Llama 3.3 70B | `azure_ai/genailab-maas-Llama-3.3-70B-Instruct` |

### Frontend `.env.local`

| Variable | Default | Description |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Backend API URL |

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/health` | Health check + system status |
| `POST` | `/api/v1/ingest` | Ingest papers into vector store |
| `POST` | `/api/v1/search` | Fast semantic search (synchronous) |
| `POST` | `/api/v1/search/async` | Search with LLM reranking (returns job_id) |
| `POST` | `/api/v1/summarize` | Summarize papers (returns job_id for streaming) |
| `POST` | `/api/v1/hypothesize` | Generate hypotheses (returns job_id for streaming) |
| `GET` | `/api/v1/stream/{job_id}` | SSE stream for real-time agent progress |
| `GET` | `/api/v1/jobs/{job_id}` | Poll-based job status |
| `POST` | `/api/v1/feedback` | Human-in-the-loop feedback (accept/reject/flag) |
| `GET` | `/api/v1/feedback/stats` | Feedback statistics |

### Example: Generate Hypotheses

```bash
# Start the job
curl -X POST http://localhost:8000/api/v1/hypothesize \
  -H "Content-Type: application/json" \
  -d '{"query": "CRISPR Alzheimer treatment", "num_hypotheses": 3}'

# Response: {"job_id": "abc-123", "status": "pending", "stream_url": "/api/v1/stream/abc-123"}

# Stream progress
curl -N http://localhost:8000/api/v1/stream/abc-123

# Or poll
curl http://localhost:8000/api/v1/jobs/abc-123
```

---

## LLM Routing Strategy

```
                    ┌─────────────┐
Request             │ LiteLLM     │
─────────────────►  │ Router      │
                    └──────┬──────┘
                           │
              ┌────────────▼─────────────┐
              │ Cache hit? → return cached│
              └────────────┬─────────────┘
                           │ cache miss
                 ┌─────────▼──────────┐
                 │ Primary: GPT-4o    │
                 │ (OpenAI API key)   │
                 └─────────┬──────────┘
                           │ fail / rate-limit
                 ┌─────────▼──────────────────┐
                 │ Fallback: Gemini 1.5 Pro    │
                 │ (Google Gemini API key)      │
                 └─────────┬──────────────────┘
                           │ no keys at all
                 ┌─────────▼──────────┐
                 │ Mock mode: pre-gen │
                 │ demo responses     │
                 └────────────────────┘
```

**Prompt Caching**: All LLM responses are cached in-memory by SHA-256 hash of the prompt. Repeated identical queries hit cache with ~0ms latency, supporting the P99 < 5s SLA.

---

## P99 Performance Architecture

| Stage | Latency Target | Strategy |
|---|---|---|
| FAISS search | < 50ms | Pre-built index, normalized inner-product |
| LLM reranking | < 1.5s | Single batched call, cached |
| Summarization | < 3s | Async streaming SSE, cached |
| Hypothesis gen | < 4.5s | Async background task, streaming |
| **End-to-end P99** | **< 5s** | Async pipeline + caching + streaming |

---

## Demo Flow for Judges

1. **Health Check** → `GET /api/v1/health` shows system status, paper count, LLM mode
2. **Semantic Search** → Search "CRISPR Alzheimer" → instant results with relevance scores
3. **AI Summary** → Click paper → "Generate AI Summary" → watch agent pipeline in real-time
4. **Hypothesis Explorer** → Enter "gut microbiome cancer immunotherapy" → see 3 novel hypotheses with novelty scores and experimental designs
5. **Human-in-the-Loop** → Accept/reject/flag hypotheses → feedback recorded
6. **Paper Ingestion** → Add a new paper → immediately searchable

---

## Governance & Security

- All API keys stored exclusively in `.env` files (never hardcoded)
- CORS restricted to configured `FRONTEND_URL`
- Input validation via Pydantic on all endpoints
- No PII ingested; papers are public research abstracts
- Human-in-the-loop feedback loop for hypothesis quality control
- Structured JSON logging for full audit trail

---

## Scalability Roadmap

- **Phase 1** (current): Single-node, in-memory FAISS + local cache
- **Phase 2**: Redis cache, PostgreSQL for jobs + feedback, FAISS distributed with Milvus
- **Phase 3**: Kubernetes deployment, horizontal scaling, PubMed live integration
- **Phase 4**: RLHF pipeline from user feedback, fine-tuned domain model

---

## Innovation Differentiators

| Feature | Competitors | This System |
|---|---|---|
| Multi-agent orchestration | Single LLM call | LangGraph pipeline with typed state |
| LLM routing | Single provider | LiteLLM: GPT-4o → Gemini fallback |
| Real-time UX | Loading spinner | SSE agent-by-agent streaming |
| Human-in-the-loop | None | Accept/reject/flag per hypothesis |
| Demo without API keys | Fails | Full mock mode with realistic data |
| Prompt caching | None | SHA-256 cache, sub-5s P99 |
