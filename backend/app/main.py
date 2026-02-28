"""
SARO Platform - Main FastAPI Application
AI Regulatory Intelligence Platform - MVP1-4 Integration
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import uvicorn

from app.api import (
    ingestion, audit, orchestrator, enterprise,
    guardrails, compliance, training, commercial,
    dashboard, health
)
from app.core.config import settings

app = FastAPI(
    title="SARO Platform API",
    description="AI Regulatory Intelligence — MVP1-4 Unified Platform",
    version="4.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MVP1 - Forecast & Ingestion
app.include_router(ingestion.router, prefix="/api/v1/mvp1", tags=["MVP1: Ingestion"])

# MVP2 - L1 Orchestrator & Audit
app.include_router(audit.router, prefix="/api/v1/mvp2", tags=["MVP2: Audit"])
app.include_router(orchestrator.router, prefix="/api/v1/mvp2", tags=["MVP2: Orchestrator"])

# MVP3 - Enterprise
app.include_router(enterprise.router, prefix="/api/v1/mvp3", tags=["MVP3: Enterprise"])

# MVP4 - Agentic GA
app.include_router(guardrails.router, prefix="/api/v1/mvp4", tags=["MVP4: Guardrails"])
app.include_router(compliance.router, prefix="/api/v1/mvp4", tags=["MVP4: Compliance"])
app.include_router(training.router, prefix="/api/v1/mvp4", tags=["MVP4: Training"])
app.include_router(commercial.router, prefix="/api/v1/mvp4", tags=["MVP4: Commercial"])

# Cross-MVP
app.include_router(dashboard.router, prefix="/api/v1", tags=["Dashboard"])
app.include_router(health.router, prefix="/api/v1", tags=["Health"])


@app.get("/")
async def root():
    return {
        "platform": "SARO - AI Regulatory Intelligence",
        "version": "4.0.0",
        "mvps": ["MVP1: Forecast", "MVP2: Audit", "MVP3: Enterprise", "MVP4: Agentic GA"],
        "status": "operational",
        "total_tests": 793,
        "docs": "/api/docs"
    }


# Root-level health endpoint for Railway/Render/Fly healthchecks
@app.get("/health")
async def health_root():
    return {"status": "healthy", "version": "4.0.0"}


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
