# BioMind AI — Research Discovery Platform

> **TCS Hackathon 2026** · Production-grade 7-agent AI system for autonomous life sciences research discovery

[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2-orange)](https://langchain-ai.github.io/langgraph)
[![LiteLLM](https://img.shields.io/badge/LiteLLM-routing-purple)](https://litellm.ai)
[![Next.js](https://img.shields.io/badge/Next.js-14-black)](https://nextjs.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.x-blue)](https://typescriptlang.org)
[![FAISS](https://img.shields.io/badge/FAISS-vector--search-red)](https://github.com/facebookresearch/faiss)

---

## Problem Statement

Life sciences researchers spend 5+ hours per query manually reading and synthesizing papers. Current tools (PubMed, Semantic Scholar, Elicit) only retrieve and summarize — they do not reason across papers, identify knowledge gaps, or generate testable hypotheses.

**BioMind AI** solves this with a 7-agent autonomous pipeline that moves beyond information retrieval into **scientific discovery**: cross-paper reasoning, gap detection, evidence scoring, explainable hypotheses, and Responsible AI guardrails — all streamed to the researcher in real time.

---

## Competitive Differentiation

| Capability | PubMed | Semantic Scholar | Elicit | ChatGPT | **BioMind AI** |
|---|:---:|:---:|:---:|:---:|:---:|
| Semantic search | ✓ | ✓ | ✓ | — | ✓ |
| Paper summarization | — | — | ✓ | ✓ | ✓ |
| Cross-paper reasoning | — | — | — | — | **✓** |
| Research gap detection | — | — | — | — | **✓** |
| Explainable hypotheses | — | — | — | — | **✓** |
| Evidence scoring | — | — | — | — | **✓** |
| Responsible AI (PII, guardrails) | — | — | — | — | **✓** |
| RAG quality evaluation | — | — | — | — | **✓** |
| Real-time agent streaming | — | — | — | — | **✓** |
| Dynamic PubMed integration | ✓ | — | — | — | **✓** |

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                          FRONTEND  (Next.js 14 / TypeScript / Tailwind CSS)  │
│                                                                              │
│  /         Home + KPI Dashboard + Competitive Comparison                     │
│  /search   Semantic Search + PubMed live results                             │
│  /gaps     Research Gap Discovery                                            │
│  /hypotheses  Hypothesis Explorer + Evidence Scores + Reasoning Path        │
│  /copilot  Research Copilot Chat                                             │
│  /radar    Research Opportunity Radar                                        │
│  /ingest   Paper Ingestion (JSON upload + manual form)                       │
│  /reports  Responsible AI Reports (PII / RAGAS / Guardrails)                │
│                                                                              │
│  Components: AgentStatusTracker · HypothesisPanel · ResearchGapCard         │
│             EvidenceScoreBar · ReasoningPath · AnswerMetricsPanel            │
└───────────────────────────────┬──────────────────────────────────────────────┘
                                │  REST  +  Server-Sent Events (SSE)
┌───────────────────────────────▼──────────────────────────────────────────────┐
│                           BACKEND  (FastAPI / Python 3.11)                   │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │                    LangGraph  StateGraph  (7 agents)                   │  │
│  │                                                                        │  │
│  │  ┌─────────────┐   ┌──────────┐   ┌────────┐   ┌──────────────────┐  │  │
│  │  │Orchestrator │──►│  Search  │──►│ Ranker │──►│   Summarizer     │  │  │
│  │  │  (PII mask, │   │ (FAISS + │   │ (LLM   │   │ (synthesis +     │  │  │
│  │  │topic check) │   │  PubMed) │   │ rerank)│   │  RAGAS eval)     │  │  │
│  │  └─────────────┘   └──────────┘   └────────┘   └────────┬─────────┘  │  │
│  │                                                           │            │  │
│  │          ┌────────────────────────┬──────────────────────┘            │  │
│  │          ▼                        ▼                                   │  │
│  │  ┌────────────────┐    ┌─────────────────────┐                        │  │
│  │  │  Gap Detector  │    │  Hypothesis Agent   │                        │  │
│  │  │  (unexplored   │    │  (novel hypotheses, │                        │  │
│  │  │   connections) │    │   evidence scores,  │                        │  │
│  │  └────────────────┘    │   reasoning path)   │                        │  │
│  │                        └──────────┬──────────┘                        │  │
│  │                                   ▼                                   │  │
│  │                         ┌─────────────────┐                           │  │
│  │                         │  Critic Agent   │                           │  │
│  │                         │ (challenges each│                           │  │
│  │                         │  hypothesis)    │                           │  │
│  │                         └─────────────────┘                           │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐  ┌────────────────┐   │
│  │ FAISS Index  │  │LiteLLM Router│  │  PII Service│  │GuardrailService│   │
│  │ (3072-dim    │  │ GenAI Lab    │  │  (Presidio/ │  │(content safety,│   │
│  │  Azure embed)│  │ primary +    │  │   regex)    │  │ PII leakage,   │   │
│  └──────────────┘  │ azure fallbk │  └─────────────┘  │ med disclaimer)│   │
│                    └──────────────┘                    └────────────────┘   │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐  ┌────────────────┐   │
│  │ RAGAS Service│  │ PubMed Scraper│  │ ReportsStore│  │   Job Store    │   │
│  │ (LLM-as-judge│  │ (NCBI E-util │  │ (circular   │  │  (SSE queue)   │   │
│  │  evaluation) │  │  esearch +   │  │  buffers)   │  │                │   │
│  └──────────────┘  │  efetch XML) │  └─────────────┘  └────────────────┘   │
│                    └──────────────┘                                         │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## Agent Pipeline

### Intent Routing

```
User Query → [Orchestrator: topic check + PII mask + intent detect]
                      │
        ┌─────────────┼─────────────────────┐
        │             │                     │
   "search"      "summarize"          "hypothesize"     "gaps"
        │             │                     │              │
    [Search]      [Search]             [Search]        [Search]
        │             │                     │              │
    [Ranker]      [Ranker]             [Ranker]        [Ranker]
        │             │                     │              │
      [END]      [Summarizer]         [Summarizer]  [Gap Detector]
                      │                     │              │
                    [END]            [Hypothesis]        [END]
                                           │
                                       [Critic]
                                           │
                                         [END]
```

### What Each Agent Does

| Agent | Role | Output |
|---|---|---|
| **Orchestrator** | Topic restriction, PII masking, intent classification | Masked query, routing decision |
| **Search** | FAISS semantic search + live PubMed E-utilities query | Top-K candidate papers |
| **Ranker** | LLM-based relevance reranking | Top-5 scored papers |
| **Summarizer** | Cross-paper synthesis, key findings extraction | Summary + citations (triggers RAGAS async) |
| **Hypothesis** | Novel hypothesis generation with reasoning path + evidence score | 3-5 hypotheses |
| **Critic** | Challenges each hypothesis with counter-argument | `critic_challenge` per hypothesis |
| **Gap Detector** | Identifies unexplored research connections | 3-5 structured research gaps |

---

## Responsible AI Features

### PII Masking
- Input queries scanned before any LLM call using **Microsoft Presidio** (with regex fallback)
- Detected entities (EMAIL, PHONE, SSN, CREDIT_CARD, IP_ADDRESS, DOB) are masked with `<ENTITY_TYPE>` placeholders
- All PII events logged to in-memory `ReportsStore` with timestamp, entity types, and backend used
- Viewable in `/reports` → PII Masking tab

### RAG Quality Evaluation (RAGAS-inspired)
- LLM-as-judge scores each summarization output on three axes:
  - **Faithfulness** (40%): claims supported by retrieved papers
  - **Answer Relevancy** (35%): response addresses the query
  - **Context Precision** (25%): retrieved context is pertinent
- Runs **fire-and-forget** — never blocks the user response
- `overall_score = faithfulness×0.4 + answer_relevancy×0.35 + context_precision×0.25`
- Viewable in `/reports` → RAG Evaluation tab

### Responsible AI Guardrails
Four automated checks on every LLM output:
1. **Content Safety** — regex patterns for harmful instructions
2. **PII Leakage** — Presidio scan on output text
3. **Medical Disclaimer** — detects medical claims without disclaimer
4. **Citation Grounding** — verifies response references source papers

### Topic Restriction
Off-topic queries (movies, sports, news, crypto, travel, gaming, etc.) are rejected at every endpoint with a `422` and a human-readable message. Mixed queries containing life-sciences keywords alongside an off-topic term are allowed (e.g. *"cancer diet study"*).

### Answer Traceability Panel
Every hypothesis and gap result page shows an inline **AnswerMetricsPanel** with:
- Guardrail status badge (✓ Passed / ✗ N violations with breakdown)
- PII status badge (entity count + types masked)
- RAGAS score bars (Faithfulness / Answer Relevancy / Context Precision)

---

## KPI Tracking

| KPI | Target | How Measured |
|---|---|---|
| 1. Processing Time Reduction | ≥ 70% vs. 5h manual baseline | `processing_time_ms` per job |
| 2. Hypothesis Novelty Score | ≥ 75% avg novelty | LLM-assigned `novelty_score` per hypothesis |
| 3. User Adoption | Growing counters | Papers processed, hypotheses generated, queries total |
| 4. Accuracy Feedback | Track accept/reject ratio | HITL feedback endpoint per output item |
| 5. Gap Detection Rate | ≥ 3 gaps per analysis | Gap count per `/gaps` job |
| 6. RAG Quality (RAGAS) | Overall score trend | Faithfulness × 0.4 + Relevancy × 0.35 + Precision × 0.25 |
| 7. Guardrail Pass Rate | ≥ 95% | Pass/fail ratio across all LLM outputs |

---

## Technology Stack

### Backend

| Layer | Technology | Version | Purpose |
|---|---|---|---|
| **Web Framework** | [FastAPI](https://fastapi.tiangolo.com) | 0.115 | Async REST API + OpenAPI docs |
| **Agent Orchestration** | [LangGraph](https://langchain-ai.github.io/langgraph) | 0.2 | Typed StateGraph, conditional routing |
| **LLM Routing** | [LiteLLM](https://litellm.ai) | 1.x | Multi-provider router with fallback |
| **LLM Provider** | TCS GenAI Lab MaaS | — | GPT-4o (primary), Azure GPT fallback |
| **Vector Database** | [FAISS](https://github.com/facebookresearch/faiss) | 1.8 | CPU vector similarity search |
| **Embeddings** | Azure OpenAI `text-embedding-3-large` | — | 3072-dim dense embeddings via LiteLLM |
| **PubMed Integration** | [NCBI E-utilities](https://www.ncbi.nlm.nih.gov/books/NBK25499/) | REST | `esearch` + `efetch` XML parse per query |
| **PII Detection** | [Microsoft Presidio](https://microsoft.github.io/presidio/) | 2.2 | Entity recognition + anonymization |
| **PII Fallback** | Python `re` | stdlib | Regex patterns when Presidio unavailable |
| **HTTP Client** | [httpx](https://www.python-httpx.org) | 0.27 | Async HTTP for PubMed scraping |
| **XML Parsing** | `xml.etree.ElementTree` | stdlib | PubMed article XML parsing |
| **Data Validation** | [Pydantic](https://docs.pydantic.dev) | 2.x | Request/response models, settings |
| **SSE Streaming** | [sse-starlette](https://github.com/sysid/sse-starlette) | 2.x | Server-Sent Events for agent progress |
| **Structured Logging** | [structlog](https://www.structlog.org) | 24.x | JSON-structured log output |
| **Config Management** | Pydantic Settings | 2.x | `.env` file loading |
| **Python** | CPython | 3.11+ | Runtime |

### Frontend

| Layer | Technology | Version | Purpose |
|---|---|---|---|
| **Framework** | [Next.js](https://nextjs.org) | 14.2 | React app router, SSG/SSR |
| **Language** | [TypeScript](https://typescriptlang.org) | 5.x | Strict typing across all components |
| **Styling** | [Tailwind CSS](https://tailwindcss.com) | 3.x | Utility-first dark-theme UI |
| **Icons** | [Lucide React](https://lucide.dev) | 0.x | Consistent SVG icon set |
| **CSS Utilities** | [clsx](https://github.com/lukeed/clsx) | 2.x | Conditional className merging |
| **HTTP Client** | Native `fetch` | — | Typed API client in `lib/api.ts` |
| **SSE Hook** | Custom `useSSE` | — | EventSource wrapper for streaming |
| **Node.js** | Node.js | 18+ | Runtime |

### DevOps / Infrastructure

| Tool | Purpose |
|---|---|
| Git | Version control |
| GitHub | Repository hosting + PR workflow |
| `.env` files | All secrets isolated, never committed |
| `uvicorn` | ASGI server for FastAPI |
| `npm run build` | Next.js production build + type check |

---

## Directory Structure

```
Hackathon/
├── backend/                          # Python FastAPI backend
│   ├── app/
│   │   ├── main.py                   # FastAPI entry point + lifespan + CORS
│   │   ├── config.py                 # Pydantic settings (LLM_PROVIDER, EMBEDDING_PROVIDER, etc.)
│   │   ├── models/
│   │   │   └── schemas.py            # All Pydantic request/response models
│   │   ├── agents/
│   │   │   └── graph.py              # LangGraph StateGraph — all 7 agent nodes
│   │   ├── services/
│   │   │   ├── llm_service.py        # LiteLLM router (GenAI Lab + Azure fallback + mock)
│   │   │   ├── embeddings.py         # Azure OpenAI embeddings via LiteLLM
│   │   │   ├── vector_store.py       # FAISS index (load/build/search/ingest)
│   │   │   ├── pubmed.py             # Dynamic PubMed scraping (NCBI E-utilities)
│   │   │   ├── pii_service.py        # PII detection + masking (Presidio / regex)
│   │   │   ├── guardrail_service.py  # Responsible AI output validation + topic restriction
│   │   │   ├── ragas_service.py      # LLM-as-judge RAG quality evaluation
│   │   │   ├── reports_store.py      # In-memory circular buffers for AI audit events
│   │   │   ├── job_store.py          # In-memory SSE job queue
│   │   │   └── metrics.py            # Adoption counters
│   │   ├── api/v1/
│   │   │   ├── search.py             # POST /search (sync, topic-checked)
│   │   │   ├── summarize.py          # POST /summarize (async SSE)
│   │   │   ├── hypothesize.py        # POST /hypothesize (async SSE)
│   │   │   ├── gaps.py               # POST /gaps (async SSE)
│   │   │   ├── copilot.py            # POST /copilot (conversational)
│   │   │   ├── stream.py             # GET  /stream/{job_id} (SSE)
│   │   │   ├── ingest.py             # POST /ingest
│   │   │   ├── papers.py             # GET  /papers
│   │   │   ├── feedback.py           # POST /feedback (HITL)
│   │   │   ├── metrics.py            # GET  /metrics/adoption
│   │   │   └── reports.py            # GET  /reports/{pii,ragas,guardrails,summary}
│   │   └── utils/
│   │       └── logging.py            # structlog JSON configuration
│   ├── data/
│   │   ├── sample_papers.json        # 10 pre-loaded life sciences papers
│   │   └── faiss_index/              # Persisted FAISS index (auto-built on startup)
│   ├── .env.example                  # Environment variable template
│   └── requirements.txt
│
├── frontend/                         # Next.js 14 frontend
│   ├── app/
│   │   ├── layout.tsx                # Root layout + Navbar
│   │   ├── page.tsx                  # Home: hero + KPI dashboard + comparison table
│   │   ├── search/page.tsx           # Semantic search + PubMed results
│   │   ├── gaps/page.tsx             # Research gap discovery
│   │   ├── hypotheses/page.tsx       # Hypothesis explorer + traceability panel
│   │   ├── copilot/page.tsx          # Research Copilot chat interface
│   │   ├── radar/page.tsx            # Research Opportunity Radar
│   │   ├── ingest/page.tsx           # Paper ingestion (JSON upload + manual)
│   │   ├── reports/page.tsx          # Responsible AI reports dashboard
│   │   └── paper/[id]/page.tsx       # Paper detail + on-demand summary
│   ├── components/
│   │   ├── Navbar.tsx                # Navigation with all routes
│   │   ├── SearchBar.tsx             # Reusable search input
│   │   ├── PaperCard.tsx             # Paper result card (PubMed badge + link)
│   │   ├── AgentStatusTracker.tsx    # Real-time SSE pipeline visualizer
│   │   ├── HypothesisPanel.tsx       # Hypothesis card + evidence + reasoning
│   │   ├── ResearchGapCard.tsx       # Gap card with opportunity level badge
│   │   ├── EvidenceScoreBar.tsx      # 4-component evidence score display
│   │   ├── ReasoningPath.tsx         # Step-chain reasoning transparency view
│   │   ├── KpiMetricsBar.tsx         # KPI metrics bar (time, novelty, gaps)
│   │   ├── AnswerMetricsPanel.tsx    # Inline traceability (guardrails + PII + RAGAS)
│   │   └── SummaryVisualization.tsx  # Summary prose + key findings
│   ├── lib/
│   │   ├── types.ts                  # TypeScript domain types (all interfaces)
│   │   ├── api.ts                    # Typed API client for all endpoints
│   │   └── hooks/useSSE.ts           # SSE EventSource hook
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
- TCS GenAI Lab API key (or OpenAI/Gemini key) — optional, system runs in mock mode without one

### 1. Backend

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env — set GENAILAB_API_KEY + GENAILAB_API_BASE (or OPENAI_API_KEY)
# Without any key, the system runs in mock mode with pre-generated responses

# Start server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

On first start the server will:
- Auto-build the FAISS index from `data/sample_papers.json`
- Start serving at `http://localhost:8000`
- Expose interactive API docs at `http://localhost:8000/docs`

### 2. Frontend

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.local.example .env.local
# NEXT_PUBLIC_API_URL=http://localhost:8000

# Development server
npm run dev

# Production build
npm run build && npm start
```

Frontend runs at `http://localhost:3000`

---

## Environment Configuration

### Backend `.env`

**Provider Selection (set one)**

```env
# TCS GenAI Lab (recommended for hackathon)
LLM_PROVIDER=genailab
EMBEDDING_PROVIDER=genailab
GENAILAB_API_KEY=sk-...
GENAILAB_API_BASE=https://your-genailab-endpoint/

# Primary model (OpenAI-compatible endpoint)
LITELLM_PRIMARY_MODEL=genailab-maas-gpt-4o
LITELLM_REASONING_MODEL=genailab-maas-gpt-4o

# Azure-format fallback
LITELLM_AZURE_FALLBACK_MODEL=azure/genailab-maas-gpt-5-mini
LITELLM_API_VERSION=2024-06-01

# Azure-format embedding model
EMBEDDING_MODEL=azure/genailab-maas-text-embedding-3-large
```

**Available TCS GenAI Lab Models**

| Category | Model ID |
|---|---|
| GPT-4o | `genailab-maas-gpt-4o` |
| GPT-4.1 | `azure/genailab-maas-gpt-4.1` |
| GPT-5 mini | `azure/genailab-maas-gpt-5-mini` |
| DeepSeek V3 | `genailab-maas-DeepSeek-V3-0324` |
| DeepSeek R1 | `azure_ai/genailab-maas-DeepSeek-R1` |
| Gemini 2.5 Pro | `gemini-2.5-pro` |
| Gemini 2.5 Flash | `gemini-2.5-flash` |
| Llama 4 Maverick | `azure_ai/genailab-maas-Llama-4-Maverick-17B-128E-Instruct-FP8` |
| Llama 3.3 70B | `azure_ai/genailab-maas-Llama-3.3-70B-Instruct` |
| Embedding (3072-dim) | `azure/genailab-maas-text-embedding-3-large` |

**Other settings**

```env
# PubMed
PUBMED_ENABLED=true
PUBMED_MAX_RESULTS=20
PUBMED_API_KEY=               # optional, increases rate limit

# SSL (for corporate proxies)
DISABLE_SSL_VERIFY=false

# Mock mode (no API key needed)
MOCK_LLM_MODE=false
```

### Frontend `.env.local`

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## API Reference

### Research Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/health` | System status, paper count, LLM mode |
| `POST` | `/api/v1/search` | Fast semantic + PubMed search (sync) |
| `POST` | `/api/v1/summarize` | Multi-paper synthesis → job_id for SSE |
| `POST` | `/api/v1/hypothesize` | Hypothesis generation → job_id for SSE |
| `POST` | `/api/v1/gaps` | Research gap detection → job_id for SSE |
| `POST` | `/api/v1/copilot` | Conversational research assistant |
| `GET` | `/api/v1/stream/{job_id}` | SSE event stream (real-time agent progress) |

### Data & Feedback Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/ingest` | Add papers to vector store |
| `GET` | `/api/v1/papers` | List all indexed papers |
| `GET` | `/api/v1/papers/{id}` | Single paper detail |
| `POST` | `/api/v1/feedback` | HITL accept/reject/flag per output |
| `GET` | `/api/v1/metrics/adoption` | Adoption counters |

### Responsible AI Reports

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/reports/pii` | PII masking history + entity breakdown |
| `GET` | `/api/v1/reports/ragas` | RAGAS evaluation scores + trends |
| `GET` | `/api/v1/reports/guardrails` | Guardrail pass/fail history |
| `GET` | `/api/v1/reports/summary` | Combined summary of all three |

### Example: Generate Hypotheses

```bash
# 1. Start the job
curl -X POST http://localhost:8000/api/v1/hypothesize \
  -H "Content-Type: application/json" \
  -d '{"query": "CRISPR Alzheimer treatment", "num_hypotheses": 3}'
# → {"job_id": "abc-123", "status": "pending", "stream_url": "/api/v1/stream/abc-123"}

# 2. Stream real-time agent events
curl -N http://localhost:8000/api/v1/stream/abc-123
# → data: {"agent":"search","status":"running","message":"Searching papers..."}
# → data: {"agent":"ranker","status":"completed","message":"Ranked 5 papers"}
# → ...
# → data: {"type":"done","result":{"hypotheses":[...],"responsible_ai":{...}}}
```

### Example: Detect Research Gaps

```bash
curl -X POST http://localhost:8000/api/v1/gaps \
  -H "Content-Type: application/json" \
  -d '{"query": "mRNA vaccine delivery CNS", "max_gaps": 5}'
```

### Topic Restriction Examples

```bash
# ✓ Accepted — life sciences topic
curl -X POST http://localhost:8000/api/v1/search \
  -d '{"query": "gut microbiome cancer immunotherapy"}'

# ✗ Rejected with 422
curl -X POST http://localhost:8000/api/v1/search \
  -d '{"query": "best football matches 2024"}'
# → {"detail": "Query appears to be about 'football', which is outside the life sciences scope..."}
```

---

## LLM Routing Strategy

```
User Request
     │
     ▼
[LiteLLM Router]
     │
     ├─ Cache hit? → return cached response (sub-10ms)
     │
     ├─ LLM_PROVIDER=genailab
     │       ├─ Primary:  openai/genailab-maas-gpt-4o  (OpenAI-compatible)
     │       ├─ Reasoning: openai/genailab-maas-gpt-4o
     │       └─ Fallback: azure/genailab-maas-gpt-5-mini  (needs api_version)
     │
     ├─ LLM_PROVIDER=openai
     │       ├─ Primary: gpt-4o
     │       └─ Fallback: gpt-4o-mini
     │
     ├─ LLM_PROVIDER=gemini
     │       ├─ Primary: gemini/gemini-2.5-pro
     │       └─ Fallback: gemini/gemini-2.5-flash
     │
     └─ No keys / MOCK_LLM_MODE=true
             └─ Pre-generated mock responses (full demo, zero API cost)
```

---

## Performance Targets

| Stage | Target | Strategy |
|---|---|---|
| FAISS search | < 50 ms | Pre-built index, cosine similarity |
| PubMed fetch | < 2 s | Async httpx, top-20 results |
| LLM reranking | < 1.5 s | Single batched call |
| Summarization | < 3 s | Async SSE streaming |
| Hypothesis gen | < 4.5 s | Async background task |
| **End-to-end P99** | **< 5 s** | Async pipeline + streaming UX |
| RAGAS evaluation | async | Fire-and-forget, never blocks response |

---

## Security & Governance

- All API keys stored exclusively in `.env` files — never committed to git
- `.env.example` shows only variable names (no values)
- CORS restricted to configured `FRONTEND_URL`
- Input validation via Pydantic on all endpoints
- Topic restriction prevents misuse of LLM resources
- PII masking ensures personal data never reaches LLM
- Output guardrails prevent harmful or misleading content
- Structured JSON audit log for all agent decisions
- Human-in-the-loop feedback loop for hypothesis quality control

---

## Demo Flow for Judges

1. **Health Check** — `GET /api/v1/health` → paper count, LLM mode, vector store status
2. **Semantic Search** — Search *"CRISPR Alzheimer"* → instant results from FAISS + live PubMed
3. **Topic Guard** — Search *"best movies 2024"* → rejected with scope explanation
4. **Research Gaps** — Enter *"mRNA vaccine neurodegeneration"* → 3-5 structured gaps with opportunity levels
5. **Hypothesis Explorer** — Enter *"gut microbiome cancer immunotherapy"* → 3 novel hypotheses with:
   - Evidence score bars (supporting papers, recency, agreement, citation impact)
   - Reasoning path (paper → finding → paper → hypothesis chain)
   - Critic challenge counter-argument
   - **Answer Traceability Panel** (guardrail status + PII + RAGAS scores)
6. **Reports Dashboard** — `/reports` → PII masking history, RAGAS evaluation trends, guardrail pass rates
7. **Ingest** — Upload a JSON file of papers → immediately searchable

---

## Scalability Roadmap

| Phase | Scope | Technologies |
|---|---|---|
| **Phase 1** (current) | Single-node, in-memory | FAISS CPU, Python dict job store |
| **Phase 2** | Persistence + caching | Redis cache, PostgreSQL jobs + feedback, Pinecone/Milvus |
| **Phase 3** | Horizontal scaling | Kubernetes, load balancer, distributed FAISS |
| **Phase 4** | Continuous learning | RLHF pipeline from HITL feedback, domain fine-tuning |
| **Phase 5** | Enterprise | SSO/SAML, audit log export, role-based access |
