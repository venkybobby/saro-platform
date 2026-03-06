"""
SARO — Persona API
Role-limited endpoints for persona views, metrics, and role switching (FR-005, FR-007).
"""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.models import get_db, User, PersonaPermission, AuditLog
from app.schemas.schemas import PermissionEntry, PersonaView, RoleSwitchRequest, UserResponse
from app.middleware.rbac import get_current_user, require_feature
from app.services.persona_metrics import PERSONA_METRICS

logger = logging.getLogger("saro.persona")
router = APIRouter(prefix="/persona", tags=["Persona Views"])


# ---------------------------------------------------------------------------
# FR-005: Get current persona's allowed features + metrics
# ---------------------------------------------------------------------------
@router.get("/view", response_model=PersonaView)
async def get_persona_view(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns the current user's persona view: allowed features and metrics.
    This is the primary endpoint the UI calls after login to render tabs/cards.
    """
    primary_role = current_user["primary_role"]

    # Get allowed features (not denied)
    permissions = db.query(PersonaPermission).filter(
        PersonaPermission.role == primary_role,
        PersonaPermission.access_level != "denied",
    ).order_by(PersonaPermission.tab_group).all()

    features = [PermissionEntry.model_validate(p) for p in permissions]
    metrics = PERSONA_METRICS.get(primary_role, [])

    # Audit the view load
    db.add(AuditLog(
        user_id=current_user["user_id"],
        tenant_id=current_user["tenant_id"],
        action="persona_view_load",
        resource=primary_role,
        details={"features_count": len(features)},
    ))
    db.commit()

    return PersonaView(role=primary_role, features=features, metrics=metrics)


# ---------------------------------------------------------------------------
# Multi-role switching
# ---------------------------------------------------------------------------
@router.post("/switch-role", response_model=PersonaView)
async def switch_role(
    req: RoleSwitchRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Switch the user's active persona (primary_role).
    Only allowed if the target role is in their assigned roles array.
    """
    user: User = current_user["_db_user"]

    if req.primary_role not in user.roles:
        raise HTTPException(
            status_code=403,
            detail=f"Role '{req.primary_role}' not assigned to you. Your roles: {user.roles}"
        )

    user.primary_role = req.primary_role
    db.add(AuditLog(
        user_id=str(user.user_id),
        tenant_id=str(user.tenant_id),
        action="role_switch",
        details={"from": current_user["primary_role"], "to": req.primary_role},
    ))
    db.commit()
    db.refresh(user)

    # Return new persona view
    permissions = db.query(PersonaPermission).filter(
        PersonaPermission.role == req.primary_role,
        PersonaPermission.access_level != "denied",
    ).order_by(PersonaPermission.tab_group).all()

    return PersonaView(
        role=req.primary_role,
        features=[PermissionEntry.model_validate(p) for p in permissions],
        metrics=PERSONA_METRICS.get(req.primary_role, []),
    )


# ---------------------------------------------------------------------------
# Feature-gated endpoints (FR-FOR-01 through FR-EVA-02)
# ---------------------------------------------------------------------------
@router.get("/features/regulatory-simulations")
async def regulatory_simulations(
    current_user: dict = Depends(require_feature("regulatory_simulations")),
):
    """Forecaster-only: Run regulatory gap simulations."""
    return {
        "feature": "regulatory_simulations",
        "access_level": current_user.get("_access_level", "full"),
        "data": {"message": "Simulation engine ready", "max_horizon_months": 12},
    }


@router.get("/features/incident-audit-logs")
async def incident_audit_logs(
    current_user: dict = Depends(require_feature("incident_audit_logs")),
    db: Session = Depends(get_db),
):
    """Autopsier-only: Access incident audit logs."""
    access = current_user.get("_access_level", "full")
    # Summary vs full based on access level
    if access == "summary":
        return {"feature": "incident_audit_logs", "access_level": "summary",
                "data": {"total_findings": 142, "critical": 12, "message": "Summary view only"}}
    return {"feature": "incident_audit_logs", "access_level": "full",
            "data": {"message": "Full audit log access", "total_findings": 142}}


@router.get("/features/remediation-workflow")
async def remediation_workflow(
    current_user: dict = Depends(require_feature("remediation_workflow")),
):
    """Enabler-only: Access remediation workflow."""
    return {
        "feature": "remediation_workflow",
        "access_level": current_user.get("_access_level", "full"),
        "data": {"active_plans": 23, "critical_pending": 4, "message": "Remediation engine ready"},
    }


@router.get("/features/ethics-trust-reports")
async def ethics_trust_reports(
    current_user: dict = Depends(require_feature("ethics_trust_reports")),
):
    """Evangelist-only: Generate ethics/trust reports."""
    access = current_user.get("_access_level", "full")
    return {
        "feature": "ethics_trust_reports",
        "access_level": access,
        "data": {"standards": ["ISO 42001", "EU AI Act", "NIST RMF"], "message": "Report generator ready"},
    }


@router.get("/features/policy-chat")
async def policy_chat(
    current_user: dict = Depends(require_feature("policy_chat")),
):
    """Evangelist-only: Policy chat agent."""
    return {
        "feature": "policy_chat",
        "access_level": current_user.get("_access_level", "full"),
        "data": {"message": "Claude-powered policy chat ready", "model": "claude-sonnet-4-20250514"},
    }


@router.get("/features/upload-input")
async def upload_input(
    current_user: dict = Depends(require_feature("upload_input")),
):
    """Enabler-only: Upload/input tools."""
    return {
        "feature": "upload_input",
        "access_level": current_user.get("_access_level", "full"),
        "data": {"message": "Upload endpoint ready", "max_size_mb": 50},
    }
