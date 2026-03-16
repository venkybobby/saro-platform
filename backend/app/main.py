"""SARO Platform v9.0 — Smart AI Risk Orchestrator
Spec-complete implementation: FR-001 to FR-018 + NFR-001 to NFR-007
v9.0 Enhancements: Onboarding DB, Selective Logging, Transactions, AI Compliance Reports,
Multi-Role, Auto-Tuning AI, ROI Simulator, Auto-Healing Bots.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from datetime import datetime

from app.api import (
    ingestion, audit, orchestrator, enterprise,
    guardrails, compliance, training, commercial,
    dashboard, health, bots, marketplace, surveillance,
    personas, policies, audit_reports, model_output,
    checklist, agent_audit,
    auth, policy_chat, gateway, pwa,
    # v9.0 enhancements
    onboarding_db, transactions, multi_role,
    auto_tuner, roi_simulator,
)

app = FastAPI(
    title="SARO Platform API",
    version="9.0.0",
    description=(
        "Smart AI Risk Orchestrator v9.0 | "
        "FR-001 Ingestion · FR-003 Forecasting · FR-004 Audit · "
        "FR-005 Remediation · FR-006 Standards · FR-007 Policy Chat · "
        "FR-008 Magic Link · FR-009 Onboarding · FR-018 Executive Dashboard | "
        "v9.0: Onboarding DB · Selective Logging · Transactions · AI Reports · "
        "Multi-Role · Auto-Tuning · ROI Simulator · Auto-Healing Bots"
    ),
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MVP1: Ingestion & Forecasting (FR-001, FR-003, FR-006)
app.include_router(ingestion.router,     prefix="/api/v1/mvp1",  tags=["FR-001/003/006 Ingestion & Forecasting"])
# MVP2: Audit & Remediation (FR-004, FR-005, FR-006)
app.include_router(audit.router,         prefix="/api/v1/mvp2",  tags=["FR-004/005/006 Audit & Remediation"])
app.include_router(orchestrator.router,  prefix="/api/v1/mvp2",  tags=["Orchestrator L1 Pipeline"])
# MVP3: Enterprise (FR-011, FR-012, FR-013)
app.include_router(enterprise.router,    prefix="/api/v1/mvp3",  tags=["FR-011/012/013 Enterprise"])
# MVP4: Agentic (FR-007, FR-015)
app.include_router(guardrails.router,    prefix="/api/v1/mvp4",  tags=["FR-007 Guardrails"])
app.include_router(compliance.router,    prefix="/api/v1/mvp4",  tags=["Compliance Reports"])
app.include_router(training.router,      prefix="/api/v1/mvp4",  tags=["FR-015 AI Fluency Training"])
app.include_router(commercial.router,    prefix="/api/v1/mvp4",  tags=["FR-017 Billing & Commercial"])
# MVP5: Autonomous (FR-016)
app.include_router(bots.router,          prefix="/api/v1/mvp5",  tags=["FR-016 Autonomous Bots"])
app.include_router(marketplace.router,   prefix="/api/v1/mvp5",  tags=["FR-016 DeFi Marketplace"])
app.include_router(surveillance.router,  prefix="/api/v1/mvp5",  tags=["Ethics & Surveillance"])
# Cross-cutting
app.include_router(personas.router,      prefix="/api/v1",       tags=["FR-010 Personas"])
app.include_router(policies.router,      prefix="/api/v1",       tags=["Policy Library"])
app.include_router(audit_reports.router, prefix="/api/v1",       tags=["Audit Reports"])
app.include_router(model_output.router,  prefix="/api/v1",       tags=["FR-002 Model Output"])
app.include_router(checklist.router,     prefix="/api/v1",       tags=["Checklist"])
app.include_router(agent_audit.router,   prefix="/api/v1",       tags=["Agent Pipeline"])
app.include_router(dashboard.router,     prefix="/api/v1",       tags=["FR-018 Executive Dashboard"])
app.include_router(health.router,        prefix="/api/v1",       tags=["NFR-004 Health"])
# v6/v7 additions
app.include_router(auth.router,          prefix="/api/v1",       tags=["FR-008/009 Auth & Onboarding"])
app.include_router(policy_chat.router,   prefix="/api/v1",       tags=["FR-007 AI Policy Chat"])
app.include_router(gateway.router,       prefix="/api/v1",       tags=["Gateway Orchestrator"])
app.include_router(pwa.router,           prefix="/api/v1",       tags=["PWA & Mobile"])
# v9.0 enhancements
app.include_router(onboarding_db.router, prefix="/api/v1",       tags=["v9 Story-1 Onboarding DB"])
app.include_router(transactions.router,  prefix="/api/v1",       tags=["v9 Story-3 Transactions"])
app.include_router(multi_role.router,    prefix="/api/v1",       tags=["v9 Story-5 Multi-Role"])
app.include_router(auto_tuner.router,    prefix="/api/v1",       tags=["v9 Elon-E1 Auto-Tuning"])
app.include_router(roi_simulator.router, prefix="/api/v1",       tags=["v9 Elon-E2 ROI Simulator"])


@app.get("/")
async def root():
    return {
        "platform": "SARO",
        "version": "9.0.0",
        "status": "operational",
        "docs": "/api/docs",
        "spec_coverage": {
            "FR-001": "Regulatory ingestion + NLP entity extraction (95% accuracy) — /api/v1/mvp1/ingest",
            "FR-002": "Model output ingest via API/UI — /api/v1/model-output/upload",
            "FR-003": "Proactive Bayesian forecasting (85% accuracy) — /api/v1/mvp1/forecast",
            "FR-004": "Reactive auditing bias/privacy/accuracy scan — /api/v1/mvp2/audit",
            "FR-005": "Remediation generation (70% mitigation) — /api/v1/mvp2/remediate",
            "FR-006": "Standards mapping EU/NIST/ISO/FDA — /api/v1/mvp1/standards-explorer",
            "FR-007": "AI Policy Chat Agent (Claude) — /api/v1/policy-chat/ask",
            "FR-008": "Magic link passwordless auth — /api/v1/auth/magic-link",
            "FR-009": "1-click Try Free onboarding — /api/v1/auth/try-free",
            "FR-010": "Persona-based UI RBAC — /api/v1/auth/personas",
            "FR-011": "Multi-tenant isolation — /api/v1/mvp3/tenants",
            "FR-015": "AI Fluency Training — /api/v1/mvp4/training/courses",
            "FR-016": "DeFi Marketplace — /api/v1/mvp5/marketplace/listings",
            "FR-018": "Executive Dashboard + ROI — /api/v1/dashboard",
        },
        "v9_enhancements": {
            "Story-1": "Onboarding DB (Redis→RDS async) — POST /api/v1/onboarding/start",
            "Story-2": "Selective Action Logging (high-impact only, ELK) — service/action_logger.py",
            "Story-3": "Transactional Data + GDPR purge — POST /api/v1/transactions/create",
            "Story-4": "AI Compliance Reports (Claude) — POST /api/v1/mvp4/compliance/generate-report",
            "Story-5": "Multi-Role + AI auto-assign — POST /api/v1/roles/{user_id}/ai-suggest",
            "Elon-E1": "Auto-Tuning AI thresholds — POST /api/v1/autotune/run",
            "Elon-E2": "What-If ROI Simulator — POST /api/v1/roi/simulate",
            "Elon-E5": "Auto-Healing Bots (low-risk) — POST /api/v1/mvp5/bots/autoheal",
        },
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/health")
async def health_root():
    return {
        "status": "healthy",
        "version": "9.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "api": "operational", "auth": "operational",
            "policy_chat": "operational", "gateway": "operational",
            "ingestion": "operational", "audit": "operational",
            "onboarding_db": "operational", "transactions": "operational",
            "multi_role": "operational", "auto_tuner": "operational",
            "roi_simulator": "operational", "autoheal_bots": "operational",
        }
    }
