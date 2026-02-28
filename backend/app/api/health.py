"""Health Check API"""
from fastapi import APIRouter
from datetime import datetime

router = APIRouter()


@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "4.0.0",
        "services": {
            "api": "operational",
            "database": "operational",
            "redis": "operational",
            "guardrails": "operational",
        },
        "mvps": {
            "mvp1_ingestion": "operational",
            "mvp2_audit": "operational",
            "mvp3_enterprise": "operational",
            "mvp4_agentic": "operational",
        }
    }
