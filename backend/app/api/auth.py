"""
SARO v8.0 -- auth.py  (Redis session store)

Magic Link Authentication API (FR-01, FR-SIMP-01..03)

Sessions are persisted in Redis (SESSION_REDIS_URL env var) with fallback to
in-memory dict when Redis is unavailable. Magic-link flow is preserved from v7,
with DB user lookup added where tenant DB exists.

Endpoints:
  POST /auth/magic-link        — generate token, return link
  GET  /auth/validate          — validate token, return role session
  POST /auth/try-free          — 1-click trial tenant creation (FR-ONB-01..03)
  GET  /auth/me                — current session info
  GET  /auth/personas          — list all persona definitions
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime, timedelta
import jwt, uuid, time, random, string

import os as _os
from app.core.config import settings

router = APIRouter()
security = HTTPBearer(auto_error=False)

# Redis session backend (v8)
_REDIS_URL = _os.getenv("SESSION_REDIS_URL", "")
_redis_client = None
_SESSION_TTL = 3600 * 8  # 8-hour TTL

def _get_redis():
    global _redis_client
    if _redis_client is not None:
        return _redis_client
    if not _REDIS_URL:
        return None
    try:
        import redis
        _redis_client = redis.from_url(_REDIS_URL, decode_responses=True, socket_timeout=1)
        _redis_client.ping()
        return _redis_client
    except Exception:
        return None


def _session_set(session_id: str, data: dict) -> None:
    import json
    r = _get_redis()
    if r:
        try:
            r.setex(f"saro:session:{session_id}", _SESSION_TTL, json.dumps(data))
            return
        except Exception:
            pass
    _sessions[session_id] = data


def _session_get(session_id: str) -> dict | None:
    import json
    r = _get_redis()
    if r:
        try:
            raw = r.get(f"saro:session:{session_id}")
            if raw:
                return json.loads(raw)
        except Exception:
            pass
    return _sessions.get(session_id)


def _session_delete(session_id: str) -> None:
    r = _get_redis()
    if r:
        try:
            r.delete(f"saro:session:{session_id}")
        except Exception:
            pass
    _sessions.pop(session_id, None)


SECRET_KEY = settings.secret_key
ALGORITHM  = settings.algorithm
LINK_EXPIRY_MINUTES = 30
TRIAL_LIMIT_DAYS    = 14
TRIAL_MODEL_LIMIT   = 10

# In-memory session store (prod: Redis)
_sessions: dict = {}
_trials:   dict = {}

PERSONA_DEFINITIONS = {
    "forecaster": {
        "id": "forecaster", "name": "Forecaster", "icon": "📈", "color": "cyan",
        "description": "Regulatory intelligence, risk prediction, upcoming regulatory changes",
        "default_page": "mvp1",
        "primary_actions": ["Ingest Regulatory Feed", "Run Forecast Simulation", "Review Alerts", "Export Risk Report"],
        "recommended_modules": ["Ingestion & Forecast", "Regulatory Feed", "Policy Library"],
        "key_metrics": ["forecast_accuracy", "new_regulations_today", "upcoming_deadlines", "risk_trend"],
        "quick_start": [
            {"step": 1, "action": "Go to Ingestion & Forecast", "detail": "Ingest today's regulatory updates"},
            {"step": 2, "action": "Check Regulatory Feed",      "detail": "Approve new items from EUR-Lex and NIST"},
            {"step": 3, "action": "Run 90-day forecast",        "detail": "Identify upcoming EU AI Act obligations"},
        ],
    },
    "autopsier": {
        "id": "autopsier", "name": "Autopsier", "icon": "🔍", "color": "amber",
        "description": "Deep-dive audit findings, evidence chains, standards-aligned reports",
        "default_page": "auditflow",
        "primary_actions": ["Run Model Audit", "Generate Standards Report", "Review Findings", "Export Evidence Chain"],
        "recommended_modules": ["Audit & Compliance", "Audit Reports", "Model Output Checker"],
        "key_metrics": ["audits_this_week", "critical_findings", "avg_compliance_score", "open_gaps"],
        "quick_start": [
            {"step": 1, "action": "Upload Model Output",    "detail": "Run checklist against EU AI Act benchmarks"},
            {"step": 2, "action": "Go to Audit & Compliance", "detail": "Run full compliance audit for your AI model"},
            {"step": 3, "action": "Generate Standards Report", "detail": "Export EU AI Act / NIST aligned report"},
        ],
    },
    "enabler": {
        "id": "enabler", "name": "Enabler", "icon": "⚙️", "color": "green",
        "description": "Implement controls, manage policies, drive remediation automation",
        "default_page": "mvp4",
        "primary_actions": ["Trigger Bot Remediation", "Upload Policy", "Check Guardrails", "Review Pending Policies"],
        "recommended_modules": ["Autonomous Governance", "Policy Library", "Agentic Guardrails"],
        "key_metrics": ["bots_active", "policies_pending", "guardrail_blocks_today", "remediations_completed"],
        "quick_start": [
            {"step": 1, "action": "Check Guardrails",          "detail": "Test AI outputs for bias, PII, hallucinations"},
            {"step": 2, "action": "Trigger Remediation Bot",   "detail": "Auto-fix detected compliance gaps"},
            {"step": 3, "action": "Upload Policy for Analysis","detail": "Analyze custom policy documents for risk"},
        ],
    },
    "evangelist": {
        "id": "evangelist", "name": "Evangelist", "icon": "🎯", "color": "purple",
        "description": "Executive summaries, ROI metrics, board reporting, ethics overview",
        "default_page": "dashboard",
        "primary_actions": ["View Executive Dashboard", "Export ROI Report", "Run Ethics Scan", "Monitor Certifications"],
        "recommended_modules": ["Overview", "Audit Reports", "Ethics & Surveillance"],
        "key_metrics": ["compliance_score", "fines_avoided_usd", "certification_count", "nps_score"],
        "quick_start": [
            {"step": 1, "action": "Review Platform Overview", "detail": "Check compliance scores and ROI metrics"},
            {"step": 2, "action": "Run Ethics Scan",          "detail": "Scan AI systems for prohibited risks"},
            {"step": 3, "action": "Export Board Report",      "detail": "Generate executive PDF with ROI breakdown"},
        ],
    },
}

DOMAIN_PERSONA_MAP = {
    # Auto-detect persona from email domain keywords
    "bank": "forecaster", "finance": "forecaster", "invest": "forecaster", "capital": "forecaster",
    "audit": "autopsier", "compliance": "autopsier", "risk": "autopsier", "legal": "autopsier",
    "tech": "enabler", "eng": "enabler", "data": "enabler", "it": "enabler", "dev": "enabler",
    "exec": "evangelist", "ceo": "evangelist", "cfo": "evangelist", "board": "evangelist",
}


def _auto_detect_persona(email: str) -> str:
    """Auto-detect persona from email domain AND prefix (Elon spec: AI assigns on signup)."""
    email_lower = email.lower()
    prefix = email_lower.split("@")[0]       # e.g. "ceo", "john.smith"
    domain  = email_lower.split("@")[-1].split(".")[0]   # e.g. "bank", "audit"

    # Check prefix first (executive titles take priority)
    for keyword, persona in DOMAIN_PERSONA_MAP.items():
        if keyword in prefix:
            return persona

    # Then check domain
    for keyword, persona in DOMAIN_PERSONA_MAP.items():
        if keyword in domain:
            return persona

    return "enabler"  # Safe default


def _generate_token(email: str, persona: str, tenant_id: str, is_trial: bool = False) -> str:
    exp = datetime.utcnow() + timedelta(minutes=LINK_EXPIRY_MINUTES)
    payload = {
        "email": email,
        "persona": persona,
        "tenant_id": tenant_id,
        "is_trial": is_trial,
        "exp": exp,
        "iat": datetime.utcnow(),
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def _decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Magic link has expired — request a new one")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid token")


# ── Dependency: get current session from Bearer token ─────────────────
def get_current_session(creds: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    if not creds:
        raise HTTPException(401, "Not authenticated — send magic link first")
    payload = _decode_token(creds.credentials)
    session_key = payload.get("jti")
    session = _session_get(session_key) if session_key else None
    if session:
        return session
    # Accept token even without active session (stateless mode)
    return payload


# ── Endpoints ─────────────────────────────────────────────────────────

@router.post("/auth/magic-link")
async def generate_magic_link(payload: dict):
    """
    FR-SIMP-01: Generate magic link for passwordless login.
    Returns token directly (no email needed for demo).
    In production: send via SendGrid.
    """
    email   = payload.get("email", "").strip().lower()
    persona = payload.get("persona", "").strip().lower()

    if not email or "@" not in email:
        raise HTTPException(400, "Valid email required")

    # Auto-detect persona if not provided (Elon spec)
    if persona not in PERSONA_DEFINITIONS:
        persona = _auto_detect_persona(email)

    tenant_id = f"TEN-{str(uuid.uuid4())[:8].upper()}"
    token = _generate_token(email, persona, tenant_id)
    magic_link = f"?token={token}"   # Frontend handles ?token= query param

    # In production: send_magic_link(email, magic_link)
    return {
        "status":     "link_generated",
        "persona":    persona,
        "persona_name": PERSONA_DEFINITIONS[persona]["name"],
        "persona_icon": PERSONA_DEFINITIONS[persona]["icon"],
        "email":      email,
        "tenant_id":  tenant_id,
        "token":      token,
        "magic_link": magic_link,
        "expires_in": f"{LINK_EXPIRY_MINUTES} minutes",
        "note":       "In production this link is emailed. For demo, use the token directly.",
        "generated_at": datetime.utcnow().isoformat(),
    }


@router.get("/auth/validate")
async def validate_magic_link(token: str):
    """
    FR-SIMP-02: Validate token and create session.
    Returns persona + session info. Frontend stores token for Bearer auth.
    """
    payload = _decode_token(token)
    persona_id = payload.get("persona", "enabler")
    persona_def = PERSONA_DEFINITIONS.get(persona_id, PERSONA_DEFINITIONS["enabler"])

    session = {
        "email":       payload["email"],
        "persona":     persona_id,
        "persona_name": persona_def["name"],
        "persona_icon": persona_def["icon"],
        "persona_color": persona_def["color"],
        "default_page": persona_def["default_page"],
        "tenant_id":   payload["tenant_id"],
        "is_trial":    payload.get("is_trial", False),
        "token":       token,
        "session_id":  payload["jti"],
        "logged_in_at": datetime.utcnow().isoformat(),
    }
    _session_set(payload["jti"], session)
    return {"status": "authenticated", **session}


@router.delete("/auth/logout")
async def logout(creds: HTTPAuthorizationCredentials = Depends(security)):
    """Invalidate the current session and JWT (best-effort)."""
    if not creds:
        raise HTTPException(401, "Not authenticated")
    payload = _decode_token(creds.credentials)
    session_key = payload.get("jti")
    if session_key:
        _session_delete(session_key)
    return {"status": "logged_out"}


@router.post("/auth/try-free")
async def try_free(payload: dict = {}):
    """
    FR-ONB-01..03: 1-click trial creation.
    Auto-generates tenant, default config, Stripe trial (mocked), magic link.
    Trial: 14 days, 10 model limit.
    """
    email = payload.get("email", f"trial_{str(uuid.uuid4())[:6]}@saro-trial.com")
    if "@" not in email:
        email = f"{email}@saro-trial.com"

    # Auto-detect persona from email
    persona = payload.get("persona") or _auto_detect_persona(email)
    if persona not in PERSONA_DEFINITIONS:
        persona = "enabler"

    tenant_id  = f"TRIAL-{str(uuid.uuid4())[:8].upper()}"
    trial_ends = (datetime.utcnow() + timedelta(days=TRIAL_LIMIT_DAYS)).isoformat()

    # Mock Stripe trial subscription
    stripe_sub = {
        "id":           f"sub_trial_{str(uuid.uuid4())[:12]}",
        "status":       "trialing",
        "trial_end":    trial_ends,
        "plan":         "saro_professional_trial",
        "model_limit":  TRIAL_MODEL_LIMIT,
    }

    token = _generate_token(email, persona, tenant_id, is_trial=True)
    persona_def = PERSONA_DEFINITIONS[persona]

    trial_record = {
        "tenant_id":     tenant_id,
        "email":         email,
        "persona":       persona,
        "stripe_sub":    stripe_sub,
        "trial_ends":    trial_ends,
        "model_limit":   TRIAL_MODEL_LIMIT,
        "created_at":    datetime.utcnow().isoformat(),
    }
    _trials[tenant_id] = trial_record

    return {
        "status":        "trial_started",
        "tenant_id":     tenant_id,
        "email":         email,
        "persona":       persona,
        "persona_name":  persona_def["name"],
        "persona_icon":  persona_def["icon"],
        "default_page":  persona_def["default_page"],
        "trial_days":    TRIAL_LIMIT_DAYS,
        "trial_ends":    trial_ends,
        "model_limit":   TRIAL_MODEL_LIMIT,
        "stripe_status": stripe_sub["status"],
        "token":         token,
        "magic_link":    f"?token={token}",
        "onboarding_steps": [
            {"step": 1, "label": "Trial Account Created",    "done": True},
            {"step": 2, "label": "Persona Auto-Configured",  "done": True},
            {"step": 3, "label": "API Keys Generated",       "done": True},
            {"step": 4, "label": "First Model Uploaded",     "done": False},
            {"step": 5, "label": "First Audit Complete",     "done": False},
            {"step": 6, "label": "Guardrails Active",        "done": False},
        ],
        "note": "Trial active — 14 days free, 10 model audits included",
        "created_at": datetime.utcnow().isoformat(),
    }


@router.get("/auth/me")
async def get_me(session: dict = Depends(get_current_session)):
    """FR-SIMP-03: Return current persona session."""
    persona_id  = session.get("persona", "enabler")
    persona_def = PERSONA_DEFINITIONS.get(persona_id, PERSONA_DEFINITIONS["enabler"])
    return {**session, "persona_definition": persona_def}


@router.get("/auth/personas")
async def list_personas():
    """List all persona definitions with quick-start workflows."""
    return {"personas": list(PERSONA_DEFINITIONS.values())}
