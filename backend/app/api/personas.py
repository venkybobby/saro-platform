"""Persona & Onboarding API"""
from fastapi import APIRouter
from datetime import datetime
import uuid

router = APIRouter()

PERSONAS = {
    "forecaster": {
        "id": "forecaster", "name": "Forecaster", "icon": "📈",
        "description": "Regulatory intelligence, risk prediction, upcoming regulatory changes",
        "modules": ["Ingestion & Forecast", "Regulatory Alerts", "Feed Log"],
        "color": "cyan",
    },
    "autopsier": {
        "id": "autopsier", "name": "Autopsier", "icon": "🔍",
        "description": "Deep-dive audit findings, evidence chains, standards-aligned reports",
        "modules": ["Audit & Compliance", "Standards Reports", "Evidence Chain"],
        "color": "amber",
    },
    "enabler": {
        "id": "enabler", "name": "Enabler", "icon": "⚙️",
        "description": "Implement controls, manage policies, drive remediation automation",
        "modules": ["Guardrails", "Autonomous Bots", "Policy Library"],
        "color": "green",
    },
    "evangelist": {
        "id": "evangelist", "name": "Evangelist", "icon": "🎯",
        "description": "Executive summaries, ROI metrics, board reporting, ethics overview",
        "modules": ["Executive Dashboard", "Commercial", "Ethics & Surveillance"],
        "color": "purple",
    },
}


@router.get("/personas")
async def list_personas():
    return {"personas": list(PERSONAS.values())}


@router.post("/onboard")
async def onboard_client(payload: dict):
    tenant_id = f"TEN-{str(uuid.uuid4())[:8].upper()}"
    return {
        "tenant_id": tenant_id,
        "company_name": payload.get("company_name"),
        "industry": payload.get("industry", "technology"),
        "plan": payload.get("plan", "professional"),
        "persona": payload.get("persona", "enabler"),
        "api_key": f"saro-live-{str(uuid.uuid4()).replace('-', '')}",
        "sandbox_key": f"saro-test-{str(uuid.uuid4()).replace('-', '')}",
        "steps": [
            {"step": "Account Created", "done": True},
            {"step": "Persona Configured", "done": True},
            {"step": "API Keys Generated", "done": True},
            {"step": "First Document Ingested", "done": False},
            {"step": "First Audit Run", "done": False},
            {"step": "Guardrails Active", "done": False},
        ],
        "onboarded_at": datetime.utcnow().isoformat(),
    }
