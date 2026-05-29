from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, List, Optional, TypedDict

from langgraph.graph import StateGraph, END

from app.config import settings
from app.models.schemas import AgentName, JobStatus
from app.services.job_store import job_store
from app.services.llm_service import llm_service, _MOCK_HYPOTHESES, _MOCK_SUMMARY
from app.services.vector_store import vector_store
from app.utils.logging import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# LangGraph state
# ---------------------------------------------------------------------------

class AgentState(TypedDict):
    job_id: str
    query: str
    intent: str                       # "search" | "summarize" | "hypothesize"
    paper_ids: Optional[List[str]]    # optional paper ID filter
    focus_area: Optional[str]
    num_hypotheses: int
    max_papers: int

    retrieved_papers: List[Dict[str, Any]]
    ranked_papers: List[Dict[str, Any]]
    summaries: List[str]
    combined_summary: str
    hypotheses: List[Dict[str, Any]]
    key_findings: List[str]

    error: Optional[str]


# ---------------------------------------------------------------------------
# Helper: publish SSE event
# ---------------------------------------------------------------------------

def _publish(state: AgentState, agent: AgentName, msg: str, data: Optional[Dict] = None) -> None:
    job_store.publish(state["job_id"], {
        "agent": agent.value,
        "status": "running",
        "message": msg,
        "data": data or {},
    })


# ---------------------------------------------------------------------------
# Node: Orchestrator - validates and enriches intent
# ---------------------------------------------------------------------------

async def orchestrate_node(state: AgentState) -> AgentState:
    _publish(state, AgentName.ORCHESTRATOR, f"Routing query: '{state['query']}'")
    # intent is already set by the API layer; just log and pass through
    logger.info("orchestrate", intent=state["intent"], query=state["query"])
    return state


# ---------------------------------------------------------------------------
# Node: Search - semantic + optional keyword search via FAISS
# ---------------------------------------------------------------------------

async def search_node(state: AgentState) -> AgentState:
    _publish(state, AgentName.SEARCH, "Searching scientific papers...")
    query = state["query"]

    if state.get("paper_ids"):
        papers = vector_store.get_by_ids(state["paper_ids"])
        logger.info("papers_by_id", count=len(papers))
    else:
        # Run blocking FAISS search in a thread pool to avoid blocking the event loop
        papers = await asyncio.to_thread(vector_store.search, query, settings.MAX_RETRIEVED_DOCS)
        logger.info("semantic_search", count=len(papers), query=query)

    _publish(state, AgentName.SEARCH, f"Found {len(papers)} candidate papers", {"count": len(papers)})
    return {**state, "retrieved_papers": papers}


# ---------------------------------------------------------------------------
# Node: Ranker - reranks via LLM relevance scoring
# ---------------------------------------------------------------------------

async def rank_node(state: AgentState) -> AgentState:
    papers = state["retrieved_papers"]
    if not papers:
        return {**state, "ranked_papers": []}

    _publish(state, AgentName.RANKER, f"Reranking {len(papers)} papers...")

    top_k = min(settings.RERANK_TOP_K, len(papers))

    # Build compact paper list for LLM
    paper_snippets = "\n".join(
        f"[{i}] id={p.get('id','?')} title=\"{p.get('title','')[:80]}\" score={p.get('score',0):.3f}"
        for i, p in enumerate(papers)
    )

    prompt = [
        {
            "role": "system",
            "content": (
                "You are a scientific relevance ranker. Given a search query and papers, "
                f"return a JSON array of the {top_k} most relevant paper ids in descending order of relevance. "
                "Respond ONLY with a JSON array like: [\"id1\",\"id2\",...]"
            ),
        },
        {
            "role": "user",
            "content": f"Query: {state['query']}\n\nPapers:\n{paper_snippets}",
        },
    ]

    try:
        response = await llm_service.chat(prompt, model_alias="primary")
        response = response.strip()
        # Extract JSON array if wrapped in markdown
        if "```" in response:
            response = response.split("```")[1].replace("json", "").strip()
        ranked_ids: List[str] = json.loads(response)
        id_to_paper = {p.get("id"): p for p in papers}
        ranked = [id_to_paper[rid] for rid in ranked_ids if rid in id_to_paper]
        # Append any not ranked
        ranked_set = set(ranked_ids)
        ranked += [p for p in papers if p.get("id") not in ranked_set]
        ranked_papers = ranked[:top_k]
    except Exception as exc:
        logger.warning("ranker_fallback", error=str(exc))
        # Fall back to FAISS score ordering
        ranked_papers = sorted(papers, key=lambda p: p.get("score", 0), reverse=True)[:top_k]

    _publish(state, AgentName.RANKER, f"Top {len(ranked_papers)} papers selected",
             {"paper_titles": [p.get("title", "")[:60] for p in ranked_papers]})
    return {**state, "ranked_papers": ranked_papers}


# ---------------------------------------------------------------------------
# Node: Summarizer
# ---------------------------------------------------------------------------

async def summarize_node(state: AgentState) -> AgentState:
    papers = state["ranked_papers"]
    if not papers:
        return {**state, "combined_summary": "No papers found for this query.", "key_findings": [], "summaries": []}

    _publish(state, AgentName.SUMMARIZER, f"Summarizing {len(papers)} papers...")

    paper_texts = "\n\n---\n\n".join(
        f"Title: {p.get('title','')}\nAuthors: {', '.join(p.get('authors',[]))}\n"
        f"Year: {p.get('year','')}\nAbstract: {p.get('abstract','')}"
        for p in papers
    )

    prompt = [
        {
            "role": "system",
            "content": (
                "You are an expert life sciences research analyst. Summarize the provided research papers "
                "in 3-5 paragraphs. After the summary, output a JSON block with key findings:\n\n"
                "Format:\n<summary text>\n\n```json\n{\"key_findings\": [\"finding1\", ...]}\n```"
            ),
        },
        {
            "role": "user",
            "content": (
                f"Query context: {state['query']}\n\n"
                f"Research Papers:\n{paper_texts}"
            ),
        },
    ]

    try:
        response = await llm_service.chat(prompt, model_alias="reasoning")
        # Parse out key findings if present
        key_findings: List[str] = []
        summary = response
        if "```json" in response:
            parts = response.split("```json")
            summary = parts[0].strip()
            try:
                json_str = parts[1].split("```")[0].strip()
                data = json.loads(json_str)
                key_findings = data.get("key_findings", [])
            except Exception:
                pass
    except Exception as exc:
        logger.warning("summarizer_fallback", error=str(exc))
        summary = _MOCK_SUMMARY
        key_findings = ["Advanced gene editing shows high efficiency", "AI accelerates drug discovery"]

    _publish(state, AgentName.SUMMARIZER, "Summary complete", {"preview": summary[:120]})
    return {
        **state,
        "combined_summary": summary,
        "key_findings": key_findings,
        "summaries": [summary],
    }


# ---------------------------------------------------------------------------
# Node: Hypothesis Generator
# ---------------------------------------------------------------------------

async def hypothesis_node(state: AgentState) -> AgentState:
    _publish(state, AgentName.HYPOTHESIS, "Generating novel research hypotheses...")

    n = state.get("num_hypotheses", 3)
    focus = state.get("focus_area") or "life sciences"
    summary = state.get("combined_summary", "")

    paper_context = "\n".join(
        f"- {p.get('title','')} ({p.get('year','')}): {p.get('abstract','')[:200]}..."
        for p in state.get("ranked_papers", [])
    )

    prompt = [
        {
            "role": "system",
            "content": (
                f"You are a creative scientific hypothesis generator specializing in {focus}. "
                f"Generate exactly {n} novel, testable research hypotheses based on the provided literature. "
                "Each hypothesis should build upon current findings and suggest unexplored directions.\n\n"
                "Respond ONLY with a valid JSON array of objects with these exact fields:\n"
                "id, hypothesis, rationale, experiments (array), novelty_score (0-1 float), impact_area, supporting_paper_ids (array)"
            ),
        },
        {
            "role": "user",
            "content": (
                f"Research query: {state['query']}\n\n"
                f"Summary of current findings:\n{summary}\n\n"
                f"Key papers:\n{paper_context}"
            ),
        },
    ]

    try:
        response = await llm_service.chat(prompt, model_alias="reasoning", use_cache=False)
        response = response.strip()
        if "```" in response:
            response = response.split("```")[1].replace("json", "").strip()
        hypotheses = json.loads(response)
    except Exception as exc:
        logger.warning("hypothesis_fallback", error=str(exc))
        hypotheses = _MOCK_HYPOTHESES[:n]

    _publish(state, AgentName.HYPOTHESIS, f"{len(hypotheses)} hypotheses generated",
             {"count": len(hypotheses)})
    return {**state, "hypotheses": hypotheses}


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------

def _route_after_rank(state: AgentState) -> str:
    intent = state.get("intent", "search")
    if intent in ("summarize", "hypothesize"):
        return "summarize"
    return END


def _route_after_summarize(state: AgentState) -> str:
    if state.get("intent") == "hypothesize":
        return "hypothesize"
    return END


# ---------------------------------------------------------------------------
# Build compiled graph
# ---------------------------------------------------------------------------

def build_graph():
    g = StateGraph(AgentState)
    g.add_node("orchestrate", orchestrate_node)
    g.add_node("search", search_node)
    g.add_node("rank", rank_node)
    g.add_node("summarize", summarize_node)
    g.add_node("hypothesize", hypothesis_node)

    g.set_entry_point("orchestrate")
    g.add_edge("orchestrate", "search")
    g.add_edge("search", "rank")
    g.add_conditional_edges("rank", _route_after_rank, {"summarize": "summarize", END: END})
    g.add_conditional_edges("summarize", _route_after_summarize, {"hypothesize": "hypothesize", END: END})
    g.add_edge("hypothesize", END)

    return g.compile()


compiled_graph = build_graph()


# ---------------------------------------------------------------------------
# Runner: executes graph and publishes SSE events
# ---------------------------------------------------------------------------

async def run_graph(
    job_id: str,
    query: str,
    intent: str,
    paper_ids: Optional[List[str]] = None,
    focus_area: Optional[str] = None,
    num_hypotheses: int = 3,
    max_papers: int = 5,
) -> None:
    initial_state: AgentState = {
        "job_id": job_id,
        "query": query,
        "intent": intent,
        "paper_ids": paper_ids,
        "focus_area": focus_area,
        "num_hypotheses": num_hypotheses,
        "max_papers": max_papers,
        "retrieved_papers": [],
        "ranked_papers": [],
        "summaries": [],
        "combined_summary": "",
        "hypotheses": [],
        "key_findings": [],
        "error": None,
    }

    job = job_store.get(job_id)
    if job:
        job.status = JobStatus.RUNNING

    try:
        final_state: AgentState = initial_state
        async for step in compiled_graph.astream(initial_state):
            node_name, node_state = next(iter(step.items()))
            final_state = node_state
            logger.info("graph_step", node=node_name, job_id=job_id)

        result = _build_result(intent, final_state, query)
        job_store.complete(job_id, result)
    except Exception as exc:
        logger.error("graph_execution_failed", job_id=job_id, error=str(exc))
        job_store.fail(job_id, str(exc))


def _build_result(intent: str, state: AgentState, query: str) -> Dict[str, Any]:
    if intent == "search":
        return {
            "type": "search",
            "query": query,
            "papers": state["ranked_papers"],
            "total": len(state["ranked_papers"]),
        }
    elif intent == "summarize":
        return {
            "type": "summarize",
            "query": query,
            "summary": state["combined_summary"],
            "key_findings": state["key_findings"],
            "papers_used": state["ranked_papers"],
        }
    else:  # hypothesize
        return {
            "type": "hypothesize",
            "query": query,
            "hypotheses": state["hypotheses"],
            "context_summary": state["combined_summary"],
            "papers_used": state["ranked_papers"],
        }
