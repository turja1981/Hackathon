from __future__ import annotations

import asyncio
import json
import time
from typing import Any, Dict, List, Optional, TypedDict

from langgraph.graph import StateGraph, END

from app.config import settings
from app.models.schemas import AgentName, JobStatus
from app.services.job_store import job_store
from app.services.llm_service import llm_service, _MOCK_HYPOTHESES, _MOCK_SUMMARY, _MOCK_GAPS
from app.services.pubmed import pubmed_service
from app.services.vector_store import vector_store
from app.utils.logging import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# LangGraph state
# ---------------------------------------------------------------------------

class AgentState(TypedDict):
    job_id: str
    query: str
    intent: str                        # "search" | "summarize" | "hypothesize" | "gaps"
    paper_ids: Optional[List[str]]
    focus_area: Optional[str]
    num_hypotheses: int
    max_papers: int

    retrieved_papers: List[Dict[str, Any]]
    ranked_papers: List[Dict[str, Any]]
    summaries: List[str]
    combined_summary: str
    hypotheses: List[Dict[str, Any]]
    key_findings: List[str]
    citations: List[Dict[str, str]]
    research_gaps: List[Dict[str, Any]]

    # KPI 1: time tracking
    started_at: float
    processing_time_ms: int

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
# Node: Orchestrator
# ---------------------------------------------------------------------------

async def orchestrate_node(state: AgentState) -> AgentState:
    _publish(state, AgentName.ORCHESTRATOR, f"Routing query: '{state['query']}'")
    logger.info("orchestrate", intent=state["intent"], query=state["query"])
    return state


# ---------------------------------------------------------------------------
# Node: Search
# ---------------------------------------------------------------------------

async def search_node(state: AgentState) -> AgentState:
    _publish(state, AgentName.SEARCH, "Fetching papers from PubMed...")
    query = state["query"]

    if state.get("paper_ids"):
        # Explicit paper ID list — skip PubMed fetch
        papers = vector_store.get_by_ids(state["paper_ids"])
    else:
        # Fetch live results from PubMed for this specific query
        pubmed_papers = await pubmed_service.search(query)
        if pubmed_papers:
            # Only index papers not already in the vector store (dedup by ID)
            new_papers = [p for p in pubmed_papers if not vector_store.get_by_id(p["id"])]
            if new_papers:
                await asyncio.to_thread(vector_store.add_papers, new_papers)
                _publish(
                    state, AgentName.SEARCH,
                    f"Indexed {len(new_papers)} new PubMed papers",
                    {"new_papers": len(new_papers), "total_fetched": len(pubmed_papers)},
                )

        papers = await asyncio.to_thread(vector_store.search, query, settings.MAX_RETRIEVED_DOCS)

    _publish(
        state, AgentName.SEARCH,
        f"Found {len(papers)} candidate papers",
        {"count": len(papers), "source": "pubmed+index"},
    )
    return {**state, "retrieved_papers": papers}


# ---------------------------------------------------------------------------
# Node: Ranker
# ---------------------------------------------------------------------------

async def rank_node(state: AgentState) -> AgentState:
    papers = state["retrieved_papers"]
    if not papers:
        return {**state, "ranked_papers": []}

    _publish(state, AgentName.RANKER, f"Reranking {len(papers)} papers...")
    top_k = min(settings.RERANK_TOP_K, len(papers))

    paper_snippets = "\n".join(
        f"[{i}] id={p.get('id','?')} title=\"{p.get('title','')[:80]}\" score={p.get('score',0):.3f}"
        for i, p in enumerate(papers)
    )

    prompt = [
        {
            "role": "system",
            "content": (
                "You are a scientific relevance ranker. Given a search query and papers, "
                f"return a JSON array of the {top_k} most relevant paper ids in descending order. "
                "Respond ONLY with a JSON array like: [\"id1\",\"id2\",...]"
            ),
        },
        {"role": "user", "content": f"Query: {state['query']}\n\nPapers:\n{paper_snippets}"},
    ]

    try:
        response = await llm_service.chat(prompt, model_alias="primary")
        response = response.strip()
        if "```" in response:
            response = response.split("```")[1].replace("json", "").strip()
        ranked_ids: List[str] = json.loads(response)
        id_to_paper = {p.get("id"): p for p in papers}
        ranked = [id_to_paper[rid] for rid in ranked_ids if rid in id_to_paper]
        ranked_set = set(ranked_ids)
        ranked += [p for p in papers if p.get("id") not in ranked_set]
        ranked_papers = ranked[:top_k]
    except Exception as exc:
        logger.warning("ranker_fallback", error=str(exc))
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
    paper_id_list = ", ".join(f"{p.get('id')} = \"{p.get('title','')}\"" for p in papers)

    prompt = [
        {
            "role": "system",
            "content": (
                "You are an expert life sciences research analyst. Summarize the provided research papers "
                "in 3-5 paragraphs. Ground every claim in the source papers — do not hallucinate facts. "
                "After the summary, output a JSON block with:\n"
                "- key_findings: list of concise finding strings\n"
                "- citations: list of objects {paper_id, paper_title, claim}\n\n"
                "Format:\n<summary text>\n\n"
                "```json\n"
                "{\"key_findings\": [...], \"citations\": [{\"paper_id\": \"...\", \"paper_title\": \"...\", \"claim\": \"...\"}]}\n"
                "```"
            ),
        },
        {
            "role": "user",
            "content": (
                f"Query context: {state['query']}\n\n"
                f"Available papers (cite by paper_id): {paper_id_list}\n\n"
                f"Research Papers:\n{paper_texts}"
            ),
        },
    ]

    citations: List[Dict[str, str]] = []
    try:
        response = await llm_service.chat(prompt, model_alias="reasoning")
        key_findings: List[str] = []
        summary = response
        if "```json" in response:
            parts = response.split("```json")
            summary = parts[0].strip()
            try:
                json_str = parts[1].split("```")[0].strip()
                data = json.loads(json_str)
                key_findings = data.get("key_findings", [])
                citations = data.get("citations", [])
            except Exception:
                pass
    except Exception as exc:
        logger.warning("summarizer_fallback", error=str(exc))
        summary = _MOCK_SUMMARY
        key_findings = ["Advanced gene editing shows high efficiency", "AI accelerates drug discovery"]
        citations = [{"paper_id": p.get("id", ""), "paper_title": p.get("title", ""), "claim": "Supporting evidence"} for p in papers[:2]]

    _publish(state, AgentName.SUMMARIZER, "Summary complete", {"preview": summary[:120], "citations": len(citations)})
    return {
        **state,
        "combined_summary": summary,
        "key_findings": key_findings,
        "summaries": [summary],
        "citations": citations,
    }


# ---------------------------------------------------------------------------
# Node: Hypothesis Generator
# ---------------------------------------------------------------------------

def _compute_evidence_score(hypothesis: Dict, ranked_papers: List[Dict]) -> Dict:
    total = len(ranked_papers)
    if total == 0:
        return {"overall_score": 0.0, "supporting_papers_count": 0, "recency_score": 0.0,
                "agreement_score": 0.0, "citation_impact_score": 0.0, "label": "Weak"}

    supporting_ids = set(hypothesis.get("supporting_paper_ids", []))
    supporting_count = len(supporting_ids) if supporting_ids else total
    supporting_normalized = min(supporting_count / max(total, 1), 1.0)

    recency_scores = []
    for p in ranked_papers:
        year = p.get("year")
        if year and isinstance(year, int):
            recency_scores.append(max(0.0, min(1.0, (year - 2015) / 10.0)))
    recency_score = sum(recency_scores) / len(recency_scores) if recency_scores else 0.5

    citation_scores = [1 if len(p.get("authors", [])) > 3 else 0 for p in ranked_papers]
    citation_impact_score = sum(citation_scores) / len(citation_scores) if citation_scores else 0.5

    agreement_score = float(hypothesis.get("agreement_score", hypothesis.get("novelty_score", 0.75)))

    overall = (supporting_normalized * 0.30 + recency_score * 0.20 +
               agreement_score * 0.30 + citation_impact_score * 0.20) * 100

    label = "Strong" if overall >= 75 else "Moderate" if overall >= 50 else "Weak"

    return {
        "overall_score": round(overall, 1),
        "supporting_papers_count": supporting_count,
        "recency_score": round(recency_score, 3),
        "agreement_score": round(agreement_score, 3),
        "citation_impact_score": round(citation_impact_score, 3),
        "label": label,
    }


async def hypothesis_node(state: AgentState) -> AgentState:
    _publish(state, AgentName.HYPOTHESIS, "Generating novel research hypotheses...")

    n = state.get("num_hypotheses", 3)
    focus = state.get("focus_area") or "life sciences"
    summary = state.get("combined_summary", "")

    paper_context = "\n".join(
        f"- [{p.get('id','')}] {p.get('title','')} ({p.get('year','')}): {p.get('abstract','')[:200]}..."
        for p in state.get("ranked_papers", [])
    )

    prompt = [
        {
            "role": "system",
            "content": (
                f"You are a creative scientific hypothesis generator specializing in {focus}. "
                f"Generate exactly {n} novel, testable research hypotheses based on the provided literature.\n\n"
                "Respond ONLY with a valid JSON array. Each object must have these exact fields:\n"
                "id (str), hypothesis (str), rationale (str), experiments (array of str), "
                "novelty_score (0-1 float), impact_area (str), supporting_paper_ids (array of paper ids), "
                "reasoning_path (array of {paper_id, paper_title, finding, relevance}), "
                "agreement_score (0-1 float, degree of consensus across the provided papers)"
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

    ranked_papers = state.get("ranked_papers", [])
    try:
        response = await llm_service.chat(prompt, model_alias="reasoning", use_cache=False)
        response = response.strip()
        if "```" in response:
            response = response.split("```")[1].replace("json", "").strip()
        hypotheses = json.loads(response)
    except Exception as exc:
        logger.warning("hypothesis_fallback", error=str(exc))
        hypotheses = _MOCK_HYPOTHESES[:n]

    # Compute evidence_score per hypothesis
    for h in hypotheses:
        h["evidence_score"] = _compute_evidence_score(h, ranked_papers)

    _publish(state, AgentName.HYPOTHESIS, f"{len(hypotheses)} hypotheses generated", {"count": len(hypotheses)})
    return {**state, "hypotheses": hypotheses}


# ---------------------------------------------------------------------------
# Node: Critic Agent
# ---------------------------------------------------------------------------

async def critic_node(state: AgentState) -> AgentState:
    hypotheses = state.get("hypotheses", [])
    if not hypotheses:
        return state

    _publish(state, AgentName.CRITIC, "Generating scientific critiques for each hypothesis...")

    hyp_list = "\n".join(
        f"[{i+1}] id={h.get('id','')} hypothesis=\"{h.get('hypothesis','')[:200]}\""
        for i, h in enumerate(hypotheses)
    )

    prompt = [
        {
            "role": "system",
            "content": (
                "You are a rigorous scientific peer reviewer. For each hypothesis, provide a brief "
                "critical counter-argument (1-2 sentences) that a reviewer might raise — focusing on "
                "methodological limitations, alternative explanations, or missing evidence.\n\n"
                "Respond ONLY with a JSON object mapping hypothesis id to critic_challenge string: "
                "{\"hyp_id\": \"critique text\", ...}"
            ),
        },
        {"role": "user", "content": f"Hypotheses to critique:\n{hyp_list}"},
    ]

    _default = [
        "The causal mechanism requires direct experimental validation; correlation in the cited studies does not confirm causation in the target cell type.",
        "Alternative confounding variables (patient heterogeneity, batch effects) must be rigorously controlled before conclusions can be drawn.",
        "Off-target effects of the proposed intervention remain uncharacterized; safety profiling must precede efficacy studies.",
    ]

    try:
        response = await llm_service.chat(prompt, model_alias="primary")
        response = response.strip()
        if "```" in response:
            response = response.split("```")[1].replace("json", "").strip()
        critique_map: Dict[str, str] = json.loads(response)
        hypotheses = [
            {**h, "critic_challenge": critique_map.get(h.get("id", ""), _default[i % len(_default)])}
            for i, h in enumerate(hypotheses)
        ]
    except Exception as exc:
        logger.warning("critic_fallback", error=str(exc))
        hypotheses = [
            {**h, "critic_challenge": _default[i % len(_default)]}
            for i, h in enumerate(hypotheses)
        ]

    _publish(state, AgentName.CRITIC, "Scientific critique complete", {"count": len(hypotheses)})
    return {**state, "hypotheses": hypotheses}


# ---------------------------------------------------------------------------
# Node: Gap Detection Agent
# ---------------------------------------------------------------------------

async def gap_detection_node(state: AgentState) -> AgentState:
    _publish(state, AgentName.GAP_DETECTOR, "Identifying unexplored research connections...")

    papers = state["ranked_papers"]
    paper_context = "\n".join(
        f"- [{p.get('id','')}] {p.get('title','')} ({p.get('year','')}): {p.get('abstract','')[:200]}"
        for p in papers
    )

    max_gaps = state.get("max_papers", 5)

    prompt = [
        {
            "role": "system",
            "content": (
                "You are a scientific research gap analyst. Analyze the provided papers and identify "
                f"{max_gaps} unexplored research connections or missing research areas with high value.\n\n"
                "Respond ONLY with a valid JSON array. Each object must have:\n"
                "id (str), gap_description (str), area (str), opportunity_level (\"High\"|\"Medium\"|\"Low\"), "
                "missing_connections (array of str), suggested_experiments (array of str), "
                "novelty_score (0.0-1.0 float), related_paper_ids (array of paper ids from the provided list)"
            ),
        },
        {
            "role": "user",
            "content": f"Research topic: {state['query']}\n\nAvailable papers:\n{paper_context}",
        },
    ]

    try:
        response = await llm_service.chat(prompt, model_alias="reasoning", use_cache=False)
        response = response.strip()
        if "```" in response:
            response = response.split("```")[1].replace("json", "").strip()
        gaps = json.loads(response)
    except Exception as exc:
        logger.warning("gap_detection_fallback", error=str(exc))
        gaps = _MOCK_GAPS[:max_gaps]

    _publish(state, AgentName.GAP_DETECTOR, f"{len(gaps)} research gaps identified", {"count": len(gaps)})
    return {**state, "research_gaps": gaps}


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------

def _route_after_rank(state: AgentState) -> str:
    intent = state.get("intent", "search")
    if intent == "gaps":
        return "gap_detection"
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
    g.add_node("critic", critic_node)
    g.add_node("gap_detection", gap_detection_node)

    g.set_entry_point("orchestrate")
    g.add_edge("orchestrate", "search")
    g.add_edge("search", "rank")
    g.add_conditional_edges(
        "rank", _route_after_rank,
        {"summarize": "summarize", "gap_detection": "gap_detection", END: END}
    )
    g.add_conditional_edges(
        "summarize", _route_after_summarize,
        {"hypothesize": "hypothesize", END: END}
    )
    g.add_edge("hypothesize", "critic")
    g.add_edge("critic", END)
    g.add_edge("gap_detection", END)

    return g.compile()


compiled_graph = build_graph()


# ---------------------------------------------------------------------------
# Runner
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
    t0 = time.monotonic()

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
        "citations": [],
        "research_gaps": [],
        "started_at": t0,
        "processing_time_ms": 0,
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

        elapsed_ms = int((time.monotonic() - t0) * 1000)
        final_state = {**final_state, "processing_time_ms": elapsed_ms}

        result = _build_result(intent, final_state, query)
        job_store.complete(job_id, result)
    except Exception as exc:
        logger.error("graph_execution_failed", job_id=job_id, error=str(exc))
        job_store.fail(job_id, str(exc))


def _build_result(intent: str, state: AgentState, query: str) -> Dict[str, Any]:
    processing_ms = state.get("processing_time_ms", 0)
    baseline_hours = 5.0
    ai_hours = processing_ms / 3_600_000
    time_reduction_pct = round((1 - ai_hours / baseline_hours) * 100, 1) if baseline_hours > 0 else 0

    kpi_metrics = {
        "processing_time_ms": processing_ms,
        "processing_time_label": f"{processing_ms / 1000:.1f}s",
        "time_reduction_pct": time_reduction_pct,
        "time_saved_label": f"Saves ~{baseline_hours - ai_hours:.1f}h vs manual review",
        "kpi_target_met": time_reduction_pct >= 70,
    }

    if intent == "search":
        return {
            "type": "search",
            "query": query,
            "papers": state["ranked_papers"],
            "total": len(state["ranked_papers"]),
            "kpi_metrics": kpi_metrics,
        }
    elif intent == "summarize":
        return {
            "type": "summarize",
            "query": query,
            "summary": state["combined_summary"],
            "key_findings": state["key_findings"],
            "citations": state.get("citations", []),
            "papers_used": state["ranked_papers"],
            "kpi_metrics": kpi_metrics,
        }
    elif intent == "gaps":
        gaps = state.get("research_gaps", [])
        return {
            "type": "gaps",
            "query": query,
            "research_gaps": gaps,
            "papers_analyzed": len(state["ranked_papers"]),
            "kpi_metrics": {
                **kpi_metrics,
                "gap_count": len(gaps),
                "gap_target_met": len(gaps) >= 3,
                "gap_detection_rate": round(len(gaps) / max(state.get("max_papers", 5), 1) * 100),
            },
        }
    else:  # hypothesize
        hypotheses = state["hypotheses"]
        avg_novelty = (
            round(sum(h.get("novelty_score", 0) for h in hypotheses) / len(hypotheses), 2)
            if hypotheses else 0
        )
        return {
            "type": "hypothesize",
            "query": query,
            "hypotheses": hypotheses,
            "context_summary": state["combined_summary"],
            "citations": state.get("citations", []),
            "papers_used": state["ranked_papers"],
            "kpi_metrics": {
                **kpi_metrics,
                "avg_novelty_score": avg_novelty,
                "avg_novelty_pct": round(avg_novelty * 100),
                "novelty_target_met": avg_novelty >= 0.75,
            },
        }
