"""SARO Platform v5.1 — AI Regulatory Intelligence"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.api import (
    ingestion, audit, orchestrator, enterprise,
    guardrails, compliance, training, commercial,
    dashboard, health, bots, marketplace, surveillance,
    personas, policies, audit_reports, model_output, checklist
)

app = FastAPI(title="SARO Platform API", version="5.1.0", docs_url="/api/docs", redoc_url="/api/redoc")

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=False, allow_methods=["*"], allow_headers=["*"])

# MVP1 — Ingestion & Forecast
app.include_router(ingestion.router,     prefix="/api/v1/mvp1",  tags=["Ingestion"])

# MVP2 — Audit & Compliance
app.include_router(audit.router,         prefix="/api/v1/mvp2",  tags=["Audit"])
app.include_router(orchestrator.router,  prefix="/api/v1/mvp2",  tags=["Orchestrator"])

# MVP3 — Enterprise
app.include_router(enterprise.router,    prefix="/api/v1/mvp3",  tags=["Enterprise"])

# MVP4 — Agentic GA
app.include_router(guardrails.router,    prefix="/api/v1/mvp4",  tags=["Guardrails"])
app.include_router(compliance.router,    prefix="/api/v1/mvp4",  tags=["Compliance"])
app.include_router(training.router,      prefix="/api/v1/mvp4",  tags=["Training"])
app.include_router(commercial.router,    prefix="/api/v1/mvp4",  tags=["Commercial"])

# MVP5 — Autonomous Governance
app.include_router(bots.router,          prefix="/api/v1/mvp5",  tags=["Bots"])
app.include_router(marketplace.router,   prefix="/api/v1/mvp5",  tags=["Marketplace"])
app.include_router(surveillance.router,  prefix="/api/v1/mvp5",  tags=["Ethics"])

# Cross-MVP features
app.include_router(personas.router,      prefix="/api/v1",       tags=["Personas"])
app.include_router(policies.router,      prefix="/api/v1",       tags=["Policies"])
app.include_router(audit_reports.router, prefix="/api/v1",       tags=["Audit Reports"])
app.include_router(model_output.router,  prefix="/api/v1",       tags=["Model Output"])
app.include_router(checklist.router,     prefix="/api/v1",       tags=["Checklist"])
app.include_router(dashboard.router,     prefix="/api/v1",       tags=["Dashboard"])
app.include_router(health.router,        prefix="/api/v1",       tags=["Health"])


@app.get("/")
async def root():
    return {
        "platform": "SARO - AI Regulatory Intelligence",
        "version": "5.1.0",
        "status": "operational",
        "docs": "/api/docs",
        "new_in_5.1": ["model-output-checklist", "persona-workflows", "compliance-status-checklist"]
    }

@app.get("/health")
async def health_root():
    return {"status": "healthy", "version": "5.1.0"}
