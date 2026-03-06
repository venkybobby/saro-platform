"""
SARO Persona RBAC — Example Protected Domain Routes
=====================================================
Demonstrates how persona-level RBAC middleware is applied to actual
business endpoints. Each endpoint uses require_scope() or require_any_scope()
as FastAPI dependencies.

These are reference implementations — your domain logic goes here.
"""

from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from models.database import get_db
from models.db_models import UserSession
from models.personas import APIScope, DataSensitivity
from middleware import (
    require_scope, require_any_scope, require_admin,
    get_current_session, check_data_sensitivity, enforce_export_limit,
)

router = APIRouter(prefix="/api/v1", tags=["Protected Domain Endpoints"])


# ===========================================================================
# FORECASTER ENDPOINTS — require forecast:* scopes
# ===========================================================================

@router.get("/forecast/dashboard")
async def forecast_dashboard(
    session: UserSession = Depends(require_scope(APIScope.FORECAST_READ)),
):
    """Forecaster + Auditor (read-only) can access this."""
    return {
        "message": "Forecast dashboard data",
        "user_id": str(session.user_id),
        "tip": "This endpoint is gated by forecast:read scope",
    }


@router.post("/forecast/scenarios")
async def create_scenario(
    session: UserSession = Depends(require_scope(APIScope.FORECAST_SCENARIO)),
):
    """Only Forecaster persona can create scenarios."""
    return {
        "message": "Scenario created",
        "note": "Only users with forecast:scenario scope (Forecaster persona) reach here",
    }


@router.get("/risk/alerts")
async def risk_alerts(
    session: UserSession = Depends(require_scope(APIScope.RISK_ALERTS)),
):
    """Only Forecaster has risk:alerts scope."""
    return {"alerts": [], "message": "Risk alerts — Forecaster only"}


# ===========================================================================
# ENABLER ENDPOINTS — require onboard:* scopes
# ===========================================================================

@router.get("/onboarding/status")
async def onboarding_status(
    session: UserSession = Depends(require_scope(APIScope.ONBOARD_MANAGE)),
):
    """Enabler persona — manage onboarding workflows."""
    return {"onboarding_queue": [], "message": "Enabler access granted"}


@router.get("/training/modules")
async def training_modules(
    session: UserSession = Depends(require_scope(APIScope.ONBOARD_TRAINING)),
):
    """Enabler persona — training hub."""
    return {"modules": [], "message": "Training content — Enabler only"}


@router.get("/integrations")
async def integration_manager(
    session: UserSession = Depends(require_scope(APIScope.ONBOARD_INTEGRATIONS)),
):
    """Enabler persona — integration management."""
    return {"integrations": [], "message": "Integration manager — Enabler only"}


# ===========================================================================
# EVANGELIST ENDPOINTS — require ethics:* scopes
# ===========================================================================

@router.get("/ethics/reports")
async def ethics_reports(
    session: UserSession = Depends(
        require_any_scope(APIScope.ETHICS_REPORTS, APIScope.AUDIT_TRAIL)
    ),
):
    """Evangelist + Auditor can access ethics reports."""
    return {"reports": [], "message": "Ethics reports — Evangelist or Auditor"}


@router.get("/ethics/bias-review")
async def bias_review(
    session: UserSession = Depends(require_scope(APIScope.ETHICS_BIAS_REVIEW)),
):
    """Evangelist only — bias review dashboard."""
    return {"reviews": [], "message": "Bias review — Evangelist only"}


@router.get("/public/compliance-docs")
async def public_compliance_docs(
    session: UserSession = Depends(require_scope(APIScope.ETHICS_PUBLIC)),
):
    """Evangelist — public-facing compliance documentation."""
    return {"docs": [], "message": "Public compliance docs — Evangelist only"}


# ===========================================================================
# AUDITOR ENDPOINTS — require audit:* scopes
# ===========================================================================

@router.get("/audit/trail")
async def audit_trail(
    session: UserSession = Depends(require_scope(APIScope.AUDIT_TRAIL)),
):
    """Auditor only — full audit trail access."""
    return {"trail": [], "message": "Full audit trail — Auditor only"}


@router.get("/audit/evidence/{record_id}")
async def get_evidence(
    record_id: str,
    request: Request,
    session: UserSession = Depends(require_scope(APIScope.AUDIT_EVIDENCE)),
    db: AsyncSession = Depends(get_db),
):
    """
    Auditor only — evidence retrieval.
    Also checks data sensitivity ceiling (RESTRICTED level required).
    """
    has_access = await check_data_sensitivity(
        DataSensitivity.RESTRICTED, session, db, request
    )
    if not has_access:
        raise HTTPException(
            status_code=403,
            detail="Your data sensitivity ceiling is insufficient for evidence access",
        )
    return {"evidence_id": record_id, "message": "Evidence data — Auditor only"}


@router.get("/audit/export")
async def export_audit_data(
    requested_rows: int = 100,
    session: UserSession = Depends(require_scope(APIScope.AUDIT_EXPORT)),
):
    """
    Auditor — export with row limit enforcement.
    The persona's max_export_rows caps the actual export.
    """
    actual_rows = enforce_export_limit(session, requested_rows)
    return {
        "requested": requested_rows,
        "actual_limit": actual_rows,
        "persona_max": session.max_export_rows,
        "message": f"Exporting up to {actual_rows} rows",
    }


# ===========================================================================
# CROSS-PERSONA — shared endpoints
# ===========================================================================

@router.get("/risk/overview")
async def risk_overview(
    session: UserSession = Depends(
        require_any_scope(
            APIScope.RISK_DASHBOARD,
            APIScope.FORECAST_READ,
            APIScope.AUDIT_TRAIL,
        )
    ),
):
    """
    Multiple personas have risk:dashboard in their scope set:
    Forecaster, Enabler, and Auditor can all see the risk overview.
    Evangelist cannot.
    """
    return {
        "risk_summary": {},
        "message": "Risk overview — Forecaster, Enabler, or Auditor",
    }


@router.get("/profile/me")
async def my_profile(
    session: UserSession = Depends(require_scope(APIScope.PROFILE_SELF)),
):
    """All personas have profile:self — everyone can see their own profile."""
    return {
        "user_id": str(session.user_id),
        "tenant_id": str(session.tenant_id),
        "scopes": session.effective_scopes,
        "views": session.effective_views,
    }
