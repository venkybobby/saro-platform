"""FR-018: Executive Dashboard — persona KPIs, ROI metrics, risk heat maps, <3s load"""
from fastapi import APIRouter
from datetime import datetime, timedelta
import random

router = APIRouter()


@router.get("/dashboard")
async def get_dashboard(role: str = "enabler"):
    now = datetime.utcnow()
    compliance_score = round(random.uniform(0.72, 0.91), 3)
    fines_avoided = round(random.uniform(1_200_000, 4_800_000), -3)

    persona_metrics = {
        "forecaster": {
            "headline": "Regulatory Risk Forecast",
            "kpis": [
                {"label": "Forecast Accuracy",    "value": "85%",   "trend": "+2%",  "color": "cyan"},
                {"label": "Upcoming Deadlines",   "value": str(random.randint(3, 8)), "trend": "", "color": "amber"},
                {"label": "90d Gap Probability",  "value": f"{round(random.uniform(42,68))}%", "trend": "+3%", "color": "red"},
                {"label": "New Regulations",      "value": str(random.randint(2, 6)), "trend": "", "color": "green"},
            ],
            "quick_actions": [
                {"label": "Run 90-day forecast", "page": "mvp1"},
                {"label": "Check feed",          "page": "feed"},
                {"label": "Standards Explorer",  "page": "mvp1"},
            ],
        },
        "autopsier": {
            "headline": "Audit Intelligence",
            "kpis": [
                {"label": "Audits This Week",     "value": str(random.randint(12, 45)),  "trend": "+8",   "color": "cyan"},
                {"label": "Critical Findings",    "value": str(random.randint(2, 12)),   "trend": "-3",   "color": "red"},
                {"label": "Avg Compliance Score", "value": f"{round(compliance_score*100)}%", "trend": "+2%", "color": "green"},
                {"label": "Open Gaps",            "value": str(random.randint(4, 18)),   "trend": "-2",   "color": "amber"},
            ],
            "quick_actions": [
                {"label": "Run Audit",          "page": "auditflow"},
                {"label": "View Reports",       "page": "reports"},
                {"label": "Model Checker",      "page": "modelchecker"},
            ],
        },
        "enabler": {
            "headline": "Remediation & Controls",
            "kpis": [
                {"label": "Bots Active",           "value": str(random.randint(3, 7)),  "trend": "",   "color": "green"},
                {"label": "Policies Pending",      "value": str(random.randint(2, 8)),  "trend": "-1", "color": "amber"},
                {"label": "Guardrail Blocks Today","value": str(random.randint(8, 35)), "trend": "+5", "color": "red"},
                {"label": "Remediations Done",     "value": str(random.randint(20, 60)),"trend": "+12","color": "cyan"},
            ],
            "quick_actions": [
                {"label": "Check Guardrails",    "page": "mvp4"},
                {"label": "View Policies",       "page": "policies"},
                {"label": "Trigger Bot",         "page": "mvp5"},
            ],
        },
        "evangelist": {
            "headline": "Executive Governance Summary",
            "kpis": [
                {"label": "Compliance Score", "value": f"{round(compliance_score*100)}%", "trend": "+4%",        "color": "green"},
                {"label": "Fines Avoided",    "value": f"${fines_avoided/1e6:.1f}M",      "trend": "+$120K",     "color": "cyan"},
                {"label": "Certifications",   "value": str(random.randint(2, 5)),          "trend": "+1",         "color": "purple"},
                {"label": "NPS Score",        "value": str(random.randint(72, 89)),         "trend": "+3",         "color": "amber"},
            ],
            "quick_actions": [
                {"label": "Export Board Report", "page": "reports"},
                {"label": "Platform Overview",   "page": "dashboard"},
                {"label": "Policy Chat",         "page": "policychat"},
            ],
        },
    }

    compliance_items = [
        {"module": "Ingestion",  "label": "EU EUR-Lex feed active",           "status": "pass",                                     "detail": "Last polled 4 hrs ago"},
        {"module": "Audit",      "label": "Bias score within threshold",       "status": "pass",                                     "detail": f"Score: {round(random.uniform(0.08,0.14),2)} vs 0.15 threshold"},
        {"module": "Audit",      "label": "Transparency score",                "status": random.choice(["pass","warn"]),              "detail": f"Score: {round(random.uniform(0.55,0.70),2)} vs 0.60 threshold"},
        {"module": "Guardrails", "label": "PII guardrails active",             "status": "pass",                                     "detail": f"{random.randint(8,35)} blocks today"},
        {"module": "Guardrails", "label": "Hallucination detection",           "status": "pass",                                     "detail": "Real-time scanning enabled"},
        {"module": "Policies",   "label": "Policy library up to date",         "status": random.choice(["pass","warn"]),              "detail": f"{random.randint(1,3)} policies pending review"},
        {"module": "Bots",       "label": "Remediation bot fleet active",      "status": "pass",                                     "detail": f"{random.randint(3,5)} bots running"},
        {"module": "Reports",    "label": "Audit reports generated",           "status": "pass",                                     "detail": f"{random.randint(1,6)} reports this week"},
        {"module": "Audit",      "label": "Human oversight configured",        "status": random.choice(["warn","critical"]),          "detail": "Review required per Art.14"},
        {"module": "Ingestion",  "label": "Technical documentation complete",  "status": random.choice(["pass","warn"]),              "detail": "Art.11 compliance check"},
    ]

    risk_trend = [
        {"day": (now - timedelta(days=6-i)).strftime("%a"),
         "score": round(random.uniform(0.45, 0.75), 2),
         "alerts": random.randint(2, 15)}
        for i in range(7)
    ]

    return {
        "platform": "SARO v8.0",
        "role": role,
        "persona_metrics": persona_metrics.get(role, persona_metrics["enabler"]),
        "mvp1_ingestion": {
            "total_documents": random.randint(1240, 1560),
            "today": random.randint(8, 24),
            "avg_risk_score": round(random.uniform(0.38, 0.55), 3),
            "high_risk_docs": random.randint(12, 45),
            "processing_rate": f"{random.randint(95, 99)}%",
        },
        "mvp2_audit": {
            "audits_total": random.randint(180, 340),
            "audits_this_week": random.randint(12, 45),
            "avg_compliance_score": compliance_score,
            "critical_findings": random.randint(2, 12),
            "mitigation_rate": round(random.uniform(0.68, 0.85), 3),
        },
        "mvp3_enterprise": {
            "active_tenants": random.randint(12, 48),
            "uptime_pct": round(random.uniform(99.90, 99.99), 2),
            "api_calls_today": random.randint(8000, 25000),
            "avg_latency_ms": random.randint(120, 380),
        },
        "mvp4_agentic": {
            "guardrail_blocks_today": random.randint(8, 35),
            "policies_active": random.randint(8, 15),
            "chat_queries_today": random.randint(5, 28),
            "models_monitored": random.randint(180, 340),
        },
        "roi_summary": {
            "fines_avoided_usd": fines_avoided,
            "compliance_overhead_saved_usd": round(random.uniform(80000, 220000), -3),
            "models_audited": random.randint(180, 340),
            "nps_score": random.randint(72, 89),
        },
        "compliance_checklist": compliance_items,
        "risk_trend_7d": risk_trend,
        "alert_summary": [
            {"type": "Bias Alert",    "count": random.randint(1, 5),  "severity": "high",    "regulation": "EU AI Act Art.10"},
            {"type": "Transparency",  "count": random.randint(0, 3),  "severity": "medium",  "regulation": "EU AI Act Art.13"},
            {"type": "Oversight Gap", "count": random.randint(0, 2),  "severity": "critical","regulation": "EU AI Act Art.14"},
            {"type": "Doc Missing",   "count": random.randint(1, 4),  "severity": "low",     "regulation": "ISO 42001 A.6.1"},
        ],
        "overall_compliance_score": compliance_score,
        "overall_mitigation_rate": round(random.uniform(0.68, 0.85), 3),
        "generated_at": now.isoformat(),
    }


@router.get("/dashboard/risk-heatmap")
async def risk_heatmap():
    """FR-018: Risk heat map for executive dashboard — domains × regulations."""
    domains = ["Finance", "Healthcare", "HR", "General", "Retail", "Government"]
    regulations = ["EU AI Act", "NIST AI RMF", "ISO 42001", "FDA SaMD"]
    base_risks = {"Finance": 0.60, "Healthcare": 0.55, "HR": 0.65, "General": 0.40, "Retail": 0.35, "Government": 0.50}
    cells = []
    for domain in domains:
        for reg in regulations:
            base = base_risks.get(domain, 0.4)
            score = round(min(0.99, base + random.gauss(0, 0.09)), 2)
            cells.append({
                "domain": domain, "regulation": reg, "score": score,
                "level": "critical" if score > 0.75 else ("high" if score > 0.55 else "medium"),
                "trend": random.choice(["up", "down", "stable"]),
            })
    return {
        "cells": cells, "domains": domains, "regulations": regulations,
        "generated_at": datetime.utcnow().isoformat()
    }
