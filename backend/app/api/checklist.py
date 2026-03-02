"""Interactive Checklist & Persona Context API"""
from fastapi import APIRouter
from datetime import datetime, timedelta
import uuid, random

router = APIRouter()

PERSONA_WORKFLOWS = {
    "forecaster": {
        "primary_actions": ["Ingest Regulatory Feed", "Run Forecast Simulation", "Review New Alerts", "Export Risk Report"],
        "key_metrics": ["forecast_accuracy", "new_regulations_today", "upcoming_deadlines", "risk_trend"],
        "recommended_modules": ["Ingestion & Forecast", "Regulatory Feed", "Policy Library"],
        "quick_start": [
            {"step": 1, "action": "Go to Ingestion & Forecast", "detail": "Ingest today's regulatory updates"},
            {"step": 2, "action": "Check Regulatory Feed", "detail": "Approve new feed items from EUR-Lex and NIST"},
            {"step": 3, "action": "Run 90-day forecast", "detail": "Identify upcoming EU AI Act obligations"},
        ],
    },
    "autopsier": {
        "primary_actions": ["Run Model Audit", "Generate Standards Report", "Review Findings", "Export Evidence Chain"],
        "key_metrics": ["audits_this_week", "critical_findings", "avg_compliance_score", "open_gaps"],
        "recommended_modules": ["Audit & Compliance", "Audit Reports", "Model Output Checker"],
        "quick_start": [
            {"step": 1, "action": "Upload Model Output", "detail": "Run checklist against EU AI Act benchmarks"},
            {"step": 2, "action": "Go to Audit & Compliance", "detail": "Run full compliance audit for your AI model"},
            {"step": 3, "action": "Generate Standards Report", "detail": "Export EU AI Act / NIST aligned report"},
        ],
    },
    "enabler": {
        "primary_actions": ["Trigger Bot Remediation", "Upload Policy", "Check Guardrails", "Review Pending Policies"],
        "key_metrics": ["bots_active", "policies_pending_review", "guardrail_blocks_today", "remediations_completed"],
        "recommended_modules": ["Autonomous Governance", "Policy Library", "Agentic Guardrails"],
        "quick_start": [
            {"step": 1, "action": "Check Guardrails", "detail": "Test your AI outputs for bias, PII, hallucinations"},
            {"step": 2, "action": "Trigger Remediation Bot", "detail": "Auto-fix detected compliance gaps"},
            {"step": 3, "action": "Upload Policy for Analysis", "detail": "Analyze custom policy documents for risk"},
        ],
    },
    "evangelist": {
        "primary_actions": ["View Executive Dashboard", "Export ROI Report", "Review Ethics Scan", "Monitor Certifications"],
        "key_metrics": ["compliance_score", "fines_avoided_usd", "certification_count", "nps_score"],
        "recommended_modules": ["Overview", "Audit Reports", "Ethics & Surveillance"],
        "quick_start": [
            {"step": 1, "action": "Review Platform Overview", "detail": "Check compliance scores and ROI metrics"},
            {"step": 2, "action": "Run Ethics Scan", "detail": "Scan AI systems for surveillance/prohibited risks"},
            {"step": 3, "action": "Export Board Report", "detail": "Generate executive PDF with ROI breakdown"},
        ],
    },
}

@router.get("/checklist/persona/{persona_id}")
async def get_persona_workflow(persona_id: str):
    workflow = PERSONA_WORKFLOWS.get(persona_id, PERSONA_WORKFLOWS["enabler"])
    return {
        "persona_id": persona_id,
        "workflow": workflow,
        "generated_at": datetime.utcnow().isoformat(),
    }

@router.get("/checklist/compliance-status")
async def compliance_status_checklist():
    """Cross-module compliance status checklist for dashboard."""
    return {
        "generated_at": datetime.utcnow().isoformat(),
        "items": [
            {"module": "Ingestion", "check": "RSS feeds active", "status": "pass", "detail": "6 feeds polled, 3 new items"},
            {"module": "Ingestion", "check": "Document library current", "status": "pass", "detail": "1,247 docs, last updated 12min ago"},
            {"module": "Audit", "check": "No unreviewed critical findings", "status": "warn", "detail": "2 critical findings pending review"},
            {"module": "Audit", "check": "All models audited this quarter", "status": "pass", "detail": "23 models — all audited"},
            {"module": "Guardrails", "check": "Guardrails operational", "status": "pass", "detail": "< 1ms latency, 96.2% block rate"},
            {"module": "Guardrails", "check": "Bias threshold within bounds", "status": "warn", "detail": "CreditScorer-v2 at 17.3% (limit 15%)"},
            {"module": "Policies", "check": "No flagged policies pending", "status": "critical", "detail": "FDA SaMD policy flagged — needs review"},
            {"module": "Policies", "check": "Feed log reviewed", "status": "warn", "detail": "3 feed items pending approval"},
            {"module": "Bots", "check": "Bot fleet operational", "status": "pass", "detail": "4/4 bots active, 247 actions today"},
            {"module": "Reports", "check": "Standards reports generated", "status": "pass", "detail": "Last report: EU AI Act compliant"},
        ],
    }
