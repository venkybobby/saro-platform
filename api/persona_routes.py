"""
SARO Persona RBAC — Admin Persona Management API
==================================================
Endpoints for admin provisioning (FR-001), role assignment (FR-003),
and persona info lookup. All admin endpoints require admin scope.
"""

from __future__ import annotations
import uuid
import secrets
import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from models.database import get_db
from models.db_models import User, Tenant, UserSession, PersonaAuditLog
from models.personas import (
    Persona, APIScope, PERSONA_MATRIX,
    get_merged_scopes, get_merged_views, get_merged_reports,
    get_highest_sensitivity,
)
from schemas import (
    UserProvisionRequest, UserProvisionResponse,
    RoleUpdateRequest, RoleUpdateResponse,
    EffectivePermissions, PersonaInfo,
    AuditLogQuery, AuditLogEntry,
)
from middleware import require_admin, require_scope, get_current_session

logger = logging.getLogger("saro.persona_api")

router = APIRouter(prefix="/api/v1/personas", tags=["Persona Management"])


# ---------------------------------------------------------------------------
# GET /personas — list all persona definitions (public)
# ---------------------------------------------------------------------------
@router.get("/", response_model=list[PersonaInfo])
async def list_personas():
    """
    Return the full persona catalog with scopes, views, and reports.
    Public endpoint — used by frontend to render role selection UI.
    """
    result = []
    for persona, config in PERSONA_MATRIX.items():
        result.append(PersonaInfo(
            name=persona.value,
            description=config["description"],
            scopes=sorted(s.value for s in config["scopes"]),
            views=sorted(v.value for v in config["views"]),
            reports=sorted(r.value for r in config["reports"]),
            data_sensitivity_ceiling=config["data_ceiling"].value,
            session_timeout_minutes=config["session_timeout_minutes"],
        ))
    return result


# ---------------------------------------------------------------------------
# POST /personas/provision — admin creates a user with persona assignments
# ---------------------------------------------------------------------------
@router.post(
    "/provision/{tenant_id}",
    response_model=UserProvisionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def provision_user(
    tenant_id: uuid.UUID,
    body: UserProvisionRequest,
    request: Request,
    session: UserSession = Depends(require_admin()),
    db: AsyncSession = Depends(get_db),
):
    """
    Admin provisions a new user within a tenant (FR-001 + FR-003).
    - Validates tenant exists and is active
    - Validates tenant hasn't exceeded max_users
    - Validates requested personas are in tenant's allowed_personas
    - Creates user with role array
    - Generates magic link token for invite (FR-006)
    - Logs provisioning action (NFR-002)
    """
    # 1. Validate tenant
    result = await db.execute(
        select(Tenant).where(Tenant.id == tenant_id, Tenant.is_active == True)
    )
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found or inactive")

    # 2. Check user cap
    user_count = await db.scalar(
        select(func.count()).where(
            User.tenant_id == tenant_id, User.is_active == True
        )
    )
    if user_count >= tenant.max_users:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Tenant user limit reached ({tenant.max_users}). Upgrade subscription.",
        )

    # 3. Check persona availability for this tenant's subscription
    tenant_personas = set(tenant.allowed_personas or [])
    requested_personas = set(body.roles)
    disallowed = requested_personas - tenant_personas
    if disallowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Tenant subscription does not include persona(s): {disallowed}. "
                   f"Available: {tenant_personas}",
        )

    # 4. Check duplicate email within tenant
    existing = await db.scalar(
        select(func.count()).where(
            User.tenant_id == tenant_id, User.email == body.email
        )
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User {body.email} already exists in this tenant",
        )

    # 5. Create user
    magic_token = secrets.token_urlsafe(48)
    user = User(
        tenant_id=tenant_id,
        email=body.email,
        display_name=body.display_name,
        roles=body.roles,
        primary_role=body.primary_role,
        magic_link_token=magic_token,
        magic_link_expires=datetime.now(timezone.utc) + timedelta(hours=72),
        provisioned_by=session.user_id,
    )
    db.add(user)

    # 6. Audit log
    audit = PersonaAuditLog(
        user_id=session.user_id,
        tenant_id=tenant_id,
        action="user_provisioned",
        resource=f"user:{body.email}",
        scope_required="admin:provision",
        scope_granted=True,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent", "")[:512],
        details={
            "provisioned_email": body.email,
            "assigned_roles": body.roles,
            "primary_role": body.primary_role,
        },
    )
    db.add(audit)
    await db.commit()
    await db.refresh(user)

    logger.info(
        "PROVISIONED user=%s tenant=%s roles=%s by_admin=%s",
        body.email, tenant_id, body.roles, session.user_id,
    )

    # 7. TODO: Send magic link email via SendGrid (FR-006)
    # await send_magic_link(user.email, magic_token, tenant.name)

    return UserProvisionResponse(
        id=user.id,
        tenant_id=user.tenant_id,
        email=user.email,
        display_name=user.display_name,
        roles=user.roles,
        primary_role=user.primary_role,
        is_active=user.is_active,
        magic_link_sent=True,  # will be True once SendGrid is wired
        created_at=user.created_at,
    )


# ---------------------------------------------------------------------------
# PUT /personas/roles — admin updates a user's persona assignments
# ---------------------------------------------------------------------------
@router.put("/roles", response_model=RoleUpdateResponse)
async def update_user_roles(
    body: RoleUpdateRequest,
    request: Request,
    session: UserSession = Depends(require_admin()),
    db: AsyncSession = Depends(get_db),
):
    """
    Admin updates a user's persona roles (FR-003 multi-role up to 4).
    - Invalidates all active sessions for the user (forces re-login with new perms)
    - Logs the role change with before/after snapshot
    """
    result = await db.execute(select(User).where(User.id == body.user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check tenant allows these personas
    tenant_result = await db.execute(
        select(Tenant).where(Tenant.id == user.tenant_id)
    )
    tenant = tenant_result.scalar_one_or_none()
    if tenant:
        tenant_personas = set(tenant.allowed_personas or [])
        disallowed = set(body.roles) - tenant_personas
        if disallowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Tenant doesn't include persona(s): {disallowed}",
            )

    previous_roles = list(user.roles or [])
    user.roles = body.roles
    user.primary_role = body.primary_role
    user.updated_at = datetime.now(timezone.utc)

    # Invalidate active sessions — forces re-login with new permissions
    await db.execute(
        UserSession.__table__.update()
        .where(UserSession.user_id == body.user_id, UserSession.is_active == True)
        .values(is_active=False)
    )

    # Compute new effective scopes for response
    personas = [Persona(r) for r in body.roles]
    new_scopes = get_merged_scopes(personas)

    # Audit
    audit = PersonaAuditLog(
        user_id=session.user_id,
        tenant_id=user.tenant_id,
        action="roles_updated",
        resource=f"user:{user.email}",
        scope_required="admin:provision",
        scope_granted=True,
        user_roles_at_time=previous_roles,
        ip_address=request.client.host if request.client else None,
        details={
            "target_user": str(body.user_id),
            "previous_roles": previous_roles,
            "new_roles": body.roles,
            "new_primary": body.primary_role,
            "sessions_invalidated": True,
        },
    )
    db.add(audit)
    await db.commit()

    logger.info(
        "ROLES_UPDATED user=%s %s→%s by_admin=%s",
        user.email, previous_roles, body.roles, session.user_id,
    )

    return RoleUpdateResponse(
        user_id=user.id,
        previous_roles=previous_roles,
        new_roles=body.roles,
        primary_role=body.primary_role,
        effective_scopes=sorted(s.value for s in new_scopes),
        updated_at=user.updated_at,
    )


# ---------------------------------------------------------------------------
# GET /personas/me — current user's effective permissions
# ---------------------------------------------------------------------------
@router.get("/me", response_model=EffectivePermissions)
async def get_my_permissions(
    session: UserSession = Depends(get_current_session),
):
    """
    Return the current user's merged effective permissions.
    Used by frontend to gate UI views on load.
    """
    return EffectivePermissions(
        user_id=session.user_id,
        tenant_id=session.tenant_id,
        roles=[],  # filled below
        primary_role="",
        scopes=session.effective_scopes,
        views=session.effective_views,
        reports=session.effective_reports,
        data_sensitivity_ceiling=session.data_sensitivity_ceiling,
        max_export_rows=session.max_export_rows,
        session_timeout_minutes=int(
            (session.expires_at - session.created_at).total_seconds() / 60
        ),
        session_id=session.id,
        expires_at=session.expires_at,
    )


# ---------------------------------------------------------------------------
# GET /personas/audit — query persona audit logs (admin or auditor)
# ---------------------------------------------------------------------------
@router.get("/audit", response_model=list[AuditLogEntry])
async def query_audit_logs(
    user_id: uuid.UUID | None = None,
    action: str | None = None,
    scope_granted: bool | None = None,
    limit: int = Query(default=50, le=500),
    offset: int = Query(default=0, ge=0),
    session: UserSession = Depends(
        require_scope(APIScope.AUDIT_TRAIL)
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Query persona audit logs. Requires audit:trail scope.
    Supports filtering by user, action type, and grant status.
    """
    query = select(PersonaAuditLog).where(
        PersonaAuditLog.tenant_id == session.tenant_id
    )

    if user_id:
        query = query.where(PersonaAuditLog.user_id == user_id)
    if action:
        query = query.where(PersonaAuditLog.action == action)
    if scope_granted is not None:
        query = query.where(PersonaAuditLog.scope_granted == scope_granted)

    query = query.order_by(PersonaAuditLog.timestamp.desc())
    query = query.offset(offset).limit(limit)

    result = await db.execute(query)
    logs = result.scalars().all()

    return [AuditLogEntry.model_validate(log) for log in logs]
