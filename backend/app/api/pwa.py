"""PWA & Mobile API - manifests, offline support, push config"""
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from datetime import datetime

router = APIRouter()


@router.get("/manifest.json")
async def web_manifest():
    return JSONResponse({
        "name": "SARO — AI Regulatory Intelligence",
        "short_name": "SARO",
        "description": "Enterprise AI Compliance & Regulatory Intelligence Platform",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#03070f",
        "theme_color": "#00d4ff",
        "orientation": "any",
        "icons": [
            {"src": "/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any maskable"},
            {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable"},
        ],
        "categories": ["business", "productivity", "finance"],
        "shortcuts": [
            {"name": "Dashboard", "url": "/", "description": "Platform overview"},
            {"name": "Run Audit", "url": "/mvp2", "description": "AI model compliance audit"},
            {"name": "Guardrails", "url": "/mvp4", "description": "Real-time guardrail check"},
        ],
    })


@router.get("/pwa/config")
async def pwa_config():
    return {
        "push_enabled": True,
        "offline_mode": True,
        "sync_interval_seconds": 30,
        "cached_routes": ["/api/v1/dashboard", "/api/v1/mvp4/guardrails/stats"],
        "version": "4.0.0",
    }


@router.post("/pwa/subscribe")
async def push_subscribe(payload: dict):
    return {
        "subscribed": True,
        "subscriber_id": payload.get("endpoint", "")[:20],
        "topics": ["regulatory_alerts", "audit_completions", "guardrail_blocks"],
        "subscribed_at": datetime.utcnow().isoformat(),
    }
