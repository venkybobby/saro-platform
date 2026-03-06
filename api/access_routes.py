"""
SARO Persona RBAC — Access Control API
========================================
Endpoints for:
  - Session creation (login → compute effective permissions)
  - View access checks (frontend route gating)
  - Report access checks (FR-007)
  - Data export with row limit enforcement
"""

from __future__ import annotations
import uuid
import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.database import get_db
from models.db_models import User, Tenant, UserSession, PersonaAuditLog
from models.personas import (
    Persona, APIScope,
    get_merged_scopes, get_merged_views, get_merged_reports,
    get_highest_sensitivity, PERSONA_MATRIX,
)
from schemas import (
    EffectivePermissions,
    ViewAccessRequest, ViewAccessResponse,
    ReportAccessRequest, ReportAccessResponse,
)
from middleware import (
    get_current_session, require_scope,
    check_view_access, check_report_access,
    enforce_export_limit,
)

logger = logging.getLogger("saro.access")

router = APIRouter(prefix="/api/v1/access", tags=["Access Control"])


# ---------------------------------------------------------------------------
# POST /access/session — create session after magic link auth
# ---------------------------------------------------------------------------
@router.post("/session", response_model=EffectivePermissions)
async def create_session(
    request: Request,
    magic_token: str,
    db: AsyncSession = Depends(get_db),
):
    """
    After magic link authentication, create a session with pre-computed
    effective permissions from the user's assigned personas.

    This is the critical path where persona → permission resolution happens:
    1. Look up user by magic link token
    2. Resolve persona list → merged scopes/views/reports
    3. Apply tenant-level overrides
    4. Cache everything in user_sessions table
    5. Return session ID as bearer token
    """
    # 1. Find user by magic token
    result = await db.execute(
        select(User).where(
            User.magic_link_token == magic_token,
            User.is_active == True,
        )
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired magic link")

    if user.magic_link_expires and user.magic_link_expires < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Magic link expired")

    # 2. Resolve personas
    user_personas = [Persona(r) for r in (user.roles or [user.primary_role])]

    # 3. Compute merged permissions
    merged_scopes = get_merged_scopes(user_personas)
    merged_views = get_merged_views(user_personas)
    merged_reports = get_merged_reports(user_personas)
    sensitivity = get_highest_sensitivity(user_personas)

    # If admin, add admin scopes
    if user.is_admin:
        from models.personas import APIScope
        admin_scopes = {APIScope.ADMIN_PROVISION, APIScope.ADMIN_TENANT, APIScope.ADMIN_BILLING}
        merged_scopes = merged_scopes | frozenset(admin_scopes)

    # 4. Compute session timeout (shortest among personas, or override)
    if user.session_timeout_override:
        timeout_min = user.session_timeout_override
    else:
        timeout_min = min(
            PERSONA_MATRIX[p]["session_timeout_minutes"] for p in user_personas
        )

    # Compute max export rows (highest among personas)
    max_rows = max(
        PERSONA_MATRIX[p]["max_export_rows"] for p in user_personas
    )

    # 5. Apply tenant-level overrides
    tenant_result = await db.execute(
        select(Tenant).where(Tenant.id == user.tenant_id)
    )
    tenant = tenant_result.scalar_one_or_none()

    effective_views_list = sorted(v.value for v in merged_views)
    if tenant and tenant.custom_view_overrides:
        # Remove any views the tenant has explicitly disabled
        disabled = set(tenant.custom_view_overrides.get("disabled_views", []))
        effective_views_list = [v for v in effective_views_list if v not in disabled]

    # 6. Create session
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=timeout_min)

    session = UserSession(
        user_id=user.id,
        tenant_id=user.tenant_id,
        effective_scopes=sorted(s.value for s in merged_scopes),
        effective_views=effective_views_list,
        effective_reports=sorted(r.value for r in merged_reports),
        data_sensitivity_ceiling=sensitivity.value,
        max_export_rows=max_rows,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent", "")[:512],
        expires_at=expires_at,
    )
    db.add(session)

    # 7. Clear magic link (one-time use)
    user.magic_link_token = None
    user.magic_link_expires = None
    user.last_login_at = datetime.now(timezone.utc)
    user.last_login_ip = request.client.host if request.client else None

    # 8. Audit
    audit = PersonaAuditLog(
        user_id=user.id,
        tenant_id=user.tenant_id,
        action="session_created",
        resource="auth:login",
        scope_granted=True,
        user_roles_at_time=user.roles,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent", "")[:512],
        details={
            "personas": [p.value for p in user_personas],
            "scope_count": len(merged_scopes),
            "view_count": len(effective_views_list),
            "timeout_minutes": timeout_min,
        },
    )
    db.add(audit)
    await db.commit()
    await db.refresh(session)

    logger.info(
        "SESSION user=%s personas=%s scopes=%d views=%d timeout=%dm",
        user.email,
        [p.value for p in user_personas],
        len(merged_scopes),
        len(effective_views_list),
        timeout_min,
    )

    return EffectivePermissions(
        user_id=user.id,
        tenant_id=user.tenant_id,
        roles=user.roles,
        primary_role=user.primary_role,
        scopes=session.effective_scopes,
        views=session.effective_views,
        reports=session.effective_reports,
        data_sensitivity_ceiling=session.data_sensitivity_ceiling,
        max_export_rows=session.max_export_rows,
        session_timeout_minutes=timeout_min,
        session_id=session.id,
        expires_at=session.expires_at,
    )


# ---------------------------------------------------------------------------
# POST /access/check-view — frontend calls this to gate routes
# ---------------------------------------------------------------------------
@router.post("/check-view", response_model=ViewAccessResponse)
async def check_view(
    body: ViewAccessRequest,
    request: Request,
    session: UserSession = Depends(get_current_session),
    db: AsyncSession = Depends(get_db),
):
    """
    Frontend calls this before rendering a route.
    Returns granted=true/false with reason.
    """
    granted = await check_view_access(body.route, session, db, request)

    reason = None
    if not granted:
        reason = (
            f"Route '{body.route}' is not included in your persona permissions. "
            f"Your allowed views: {session.effective_views}"
        )

    return ViewAccessResponse(route=body.route, granted=granted, reason=reason)


# ---------------------------------------------------------------------------
# POST /access/check-report — report access gating (FR-007)
# ---------------------------------------------------------------------------
@router.post("/check-report", response_model=ReportAccessResponse)
async def check_report(
    body: ReportAccessRequest,
    request: Request,
    session: UserSession = Depends(get_current_session),
    db: AsyncSession = Depends(get_db),
):
    """
    Check if user can access a specific report type.
    FR-007: Evangelist → Ethics only; Auditor → Full trail; etc.
    """
    granted = await check_report_access(body.report_type, session, db, request)

    reason = None
    if not granted:
        reason = (
            f"Report type '{body.report_type}' not available for your personas. "
            f"Your accessible reports: {session.effective_reports}"
        )

    return ReportAccessResponse(
        report_type=body.report_type, granted=granted, reason=reason
    )


# ---------------------------------------------------------------------------
# POST /access/logout — invalidate session
# ---------------------------------------------------------------------------
@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request,
    session: UserSession = Depends(get_current_session),
    db: AsyncSession = Depends(get_db),
):
    """Invalidate the current session."""
    session.is_active = False

    audit = PersonaAuditLog(
        user_id=session.user_id,
        tenant_id=session.tenant_id,
        action="session_logout",
        resource="auth:logout",
        scope_granted=True,
        ip_address=request.client.host if request.client else None,
    )
    db.add(audit)
    await db.commit()
