"""
SARO Persona RBAC — Middleware & Dependencies
===============================================
FastAPI dependencies that enforce persona-level access control on every request.
Ties to FR-005 (Persona Limitation) and NFR-002 (Security audit logging).

Usage in routes:
    @router.get("/forecast/scenarios")
    async def get_scenarios(
        perms: EffectivePermissions = Depends(require_scope(APIScope.FORECAST_SCENARIO))
    ):
        ...
"""

from __future__ import annotations
import uuid
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Callable
from functools import wraps

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.database import get_db
from models.db_models import User, Tenant, UserSession, PersonaAuditLog
from models.personas import (
    Persona, APIScope, ViewGroup, ReportType, DataSensitivity,
    PERSONA_MATRIX,
    get_merged_scopes, get_merged_views, get_merged_reports,
    get_highest_sensitivity, check_scope,
)

logger = logging.getLogger("saro.rbac")
security = HTTPBearer(auto_error=False)


# ---------------------------------------------------------------------------
# Session resolution — load effective permissions from DB session cache
# ---------------------------------------------------------------------------
async def get_current_session(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> UserSession:
    """
    Resolve the current user session from the bearer token.
    The token is the session UUID issued at login.
    Returns the cached UserSession with pre-computed effective permissions.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        session_id = uuid.UUID(credentials.credentials)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session token format",
        )

    result = await db.execute(
        select(UserSession).where(
            UserSession.id == session_id,
            UserSession.is_active == True,
        )
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session not found or inactive",
        )

    if session.expires_at < datetime.now(timezone.utc):
        session.is_active = False
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired — please re-authenticate",
        )

    return session


# ---------------------------------------------------------------------------
# Core permission check dependencies
# ---------------------------------------------------------------------------
def require_scope(scope: APIScope):
    """
    FastAPI dependency factory — returns a dependency that enforces a specific scope.

    Usage:
        @router.get("/forecast")
        async def get_forecast(
            session: UserSession = Depends(require_scope(APIScope.FORECAST_READ))
        ):
            ...
    """
    async def _check(
        request: Request,
        session: UserSession = Depends(get_current_session),
        db: AsyncSession = Depends(get_db),
    ) -> UserSession:
        granted = scope.value in session.effective_scopes

        # Audit log every check (NFR-002)
        audit = PersonaAuditLog(
            user_id=session.user_id,
            tenant_id=session.tenant_id,
            action="scope_check",
            resource=str(request.url.path),
            scope_required=scope.value,
            scope_granted=granted,
            user_roles_at_time=None,  # already in session
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent", "")[:512],
            details={"method": request.method, "scope": scope.value},
        )
        db.add(audit)
        await db.commit()

        if not granted:
            logger.warning(
                "DENIED scope=%s user=%s path=%s",
                scope.value, session.user_id, request.url.path,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "insufficient_scope",
                    "required": scope.value,
                    "message": f"Your assigned personas do not include the '{scope.value}' permission.",
                    "hint": "Contact your admin to update your role assignment.",
                },
            )

        return session

    return _check


def require_any_scope(*scopes: APIScope):
    """Require at least ONE of the listed scopes (OR logic)."""
    async def _check(
        request: Request,
        session: UserSession = Depends(get_current_session),
        db: AsyncSession = Depends(get_db),
    ) -> UserSession:
        user_scopes = set(session.effective_scopes)
        required = {s.value for s in scopes}
        granted = bool(user_scopes & required)

        audit = PersonaAuditLog(
            user_id=session.user_id,
            tenant_id=session.tenant_id,
            action="scope_check_any",
            resource=str(request.url.path),
            scope_required=",".join(s.value for s in scopes),
            scope_granted=granted,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent", "")[:512],
            details={"method": request.method, "required_any": list(required)},
        )
        db.add(audit)
        await db.commit()

        if not granted:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "insufficient_scope",
                    "required_any": [s.value for s in scopes],
                    "message": "None of the required permissions are assigned to your personas.",
                },
            )

        return session

    return _check


def require_admin():
    """Restrict endpoint to admin users only (FR-001 admin provisioning)."""
    async def _check(
        request: Request,
        session: UserSession = Depends(get_current_session),
        db: AsyncSession = Depends(get_db),
    ) -> UserSession:
        is_admin = "admin:provision" in session.effective_scopes

        audit = PersonaAuditLog(
            user_id=session.user_id,
            tenant_id=session.tenant_id,
            action="admin_check",
            resource=str(request.url.path),
            scope_required="admin:provision",
            scope_granted=is_admin,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent", "")[:512],
        )
        db.add(audit)
        await db.commit()

        if not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "admin_required",
                    "message": "This endpoint requires admin privileges.",
                },
            )

        return session

    return _check


# ---------------------------------------------------------------------------
# View access check — for frontend route gating
# ---------------------------------------------------------------------------
async def check_view_access(
    route: str,
    session: UserSession,
    db: AsyncSession,
    request: Request,
) -> bool:
    """Check if a user's session permits access to a frontend view route."""
    granted = any(
        route.startswith(allowed_view) for allowed_view in session.effective_views
    )

    audit = PersonaAuditLog(
        user_id=session.user_id,
        tenant_id=session.tenant_id,
        action="view_access",
        resource=route,
        scope_granted=granted,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent", "")[:512],
        details={"route": route},
    )
    db.add(audit)
    await db.commit()

    return granted


# ---------------------------------------------------------------------------
# Report access check — for FR-007 persona-limited reports
# ---------------------------------------------------------------------------
async def check_report_access(
    report_type: str,
    session: UserSession,
    db: AsyncSession,
    request: Request,
) -> bool:
    """Check if a user's session permits access to a specific report type."""
    granted = report_type in session.effective_reports

    audit = PersonaAuditLog(
        user_id=session.user_id,
        tenant_id=session.tenant_id,
        action="report_access",
        resource=f"report:{report_type}",
        scope_granted=granted,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent", "")[:512],
        details={"report_type": report_type},
    )
    db.add(audit)
    await db.commit()

    return granted


# ---------------------------------------------------------------------------
# Data sensitivity gate
# ---------------------------------------------------------------------------
async def check_data_sensitivity(
    required_level: DataSensitivity,
    session: UserSession,
    db: AsyncSession,
    request: Request,
) -> bool:
    """Check if user's data sensitivity ceiling permits this access level."""
    granted = session.data_sensitivity_ceiling >= required_level.value

    audit = PersonaAuditLog(
        user_id=session.user_id,
        tenant_id=session.tenant_id,
        action="sensitivity_check",
        resource=str(request.url.path),
        scope_granted=granted,
        ip_address=request.client.host if request.client else None,
        details={
            "required_level": required_level.name,
            "user_ceiling": session.data_sensitivity_ceiling,
        },
    )
    db.add(audit)
    await db.commit()

    return granted


# ---------------------------------------------------------------------------
# Export row limit enforcement
# ---------------------------------------------------------------------------
def enforce_export_limit(session: UserSession, requested_rows: int) -> int:
    """Clamp export row count to the persona's maximum."""
    return min(requested_rows, session.max_export_rows)
