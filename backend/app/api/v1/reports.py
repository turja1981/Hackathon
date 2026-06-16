from __future__ import annotations
from fastapi import APIRouter
from app.services.reports_store import reports_store
from app.services.pii_service import pii_service

router = APIRouter()

@router.get("/reports/pii")
async def get_pii_report():
    return {**reports_store.pii_summary(), "backend": pii_service.backend}

@router.get("/reports/ragas")
async def get_ragas_report():
    return reports_store.ragas_summary()

@router.get("/reports/guardrails")
async def get_guardrail_report():
    return reports_store.guardrail_summary()

@router.get("/reports/summary")
async def get_reports_summary():
    pii = reports_store.pii_summary()
    ragas = reports_store.ragas_summary()
    guard = reports_store.guardrail_summary()
    return {
        "pii": {
            "total_scanned": pii["total_queries_scanned"],
            "flagged": pii["queries_with_pii"],
            "pii_rate_pct": pii["pii_rate_pct"],
        },
        "ragas": {
            "total_evaluations": ragas["total_evaluations"],
            "avg_overall_score": ragas.get("avg_scores", {}).get("overall", 0),
        },
        "guardrails": {
            "total_validations": guard["total_validations"],
            "pass_rate_pct": guard["pass_rate_pct"],
        },
    }
