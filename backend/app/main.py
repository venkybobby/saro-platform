"""SARO Platform v6.0 — AI Regulatory Intelligence
New in v6: Magic Link Auth, AI Policy Chat Agent, Gateway/Orchestrator, ROI Simulator, 1-click Try Free
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
    # v6 additions
    auth, policy_chat, gateway,
)

app = FastAPI(
    title="SARO Platform API",
    version="6.0.0",
    description="Smart AI Risk Orchestrator — Magic Link Auth, AI Policy Agent, Gateway Orchestrator",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=False, allow_methods=["*"], allow_headers=["*"])

# ── Existing routers ───────────────────────────────────────────────────
app.include_router(ingestion.router,     prefix="/api/v1/mvp1",  tags=["Ingestion"])
app.include_router(audit.router,         prefix="/api/v1/mvp2",  tags=["Audit"])
app.include_router(orchestrator.router,  prefix="/api/v1/mvp2",  tags=["Orchestrator"])
app.include_router(enterprise.router,    prefix="/api/v1/mvp3",  tags=["Enterprise"])
app.include_router(guardrails.router,    prefix="/api/v1/mvp4",  tags=["Guardrails"])
app.include_router(compliance.router,    prefix="/api/v1/mvp4",  tags=["Compliance"])
app.include_router(training.router,      prefix="/api/v1/mvp4",  tags=["Training"])
app.include_router(commercial.router,    prefix="/api/v1/mvp4",  tags=["Commercial"])
app.include_router(bots.router,          prefix="/api/v1/mvp5",  tags=["Autonomous Bots"])
app.include_router(marketplace.router,   prefix="/api/v1/mvp5",  tags=["Marketplace"])
app.include_router(surveillance.router,  prefix="/api/v1/mvp5",  tags=["Ethics"])
app.include_router(personas.router,      prefix="/api/v1",       tags=["Personas"])
app.include_router(policies.router,      prefix="/api/v1",       tags=["Policies"])
app.include_router(audit_reports.router, prefix="/api/v1",       tags=["Audit Reports"])
app.include_router(model_output.router,  prefix="/api/v1",       tags=["Model Output"])
app.include_router(checklist.router,     prefix="/api/v1",       tags=["Checklist"])
app.include_router(agent_audit.router,   prefix="/api/v1",       tags=["Agent Pipeline"])
app.include_router(dashboard.router,     prefix="/api/v1",       tags=["Dashboard"])
app.include_router(health.router,        prefix="/api/v1",       tags=["Health"])
# ── v6 new routers ─────────────────────────────────────────────────────
app.include_router(auth.router,          prefix="/api/v1",       tags=["Auth — Magic Link"])
app.include_router(policy_chat.router,   prefix="/api/v1",       tags=["AI Policy Chat"])
app.include_router(gateway.router,       prefix="/api/v1",       tags=["Gateway Orchestrator"])


@app.get("/")
async def root():
    return {
        "platform": "SARO",
        "version": "6.0.0",
        "status": "operational",
        "docs": "/api/docs",
        "new_in_v6": [
            "Magic Link passwordless auth (POST /api/v1/auth/magic-link)",
            "1-click Try Free trial (POST /api/v1/auth/try-free)",
            "AI Policy Chat Agent (POST /api/v1/policy-chat/ask)",
            "Gateway Orchestrator (POST /api/v1/gateway/submit)",
            "ROI Simulator (POST /api/v1/gateway/roi-estimate)",
            "GitHub Repo Scanner (POST /api/v1/gateway/scan-github)",
            "Industry Test Datasets (GET /api/v1/gateway/industry-data)",
        ],
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/health")
async def health_root():
    return {
        "status": "healthy",
        "version": "6.0.0",
        "uptime": "operational",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "api": "operational", "auth": "operational",
            "policy_chat": "operational", "gateway": "operational",
        }
    }
