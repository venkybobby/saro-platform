"""
SARO — Admin Provisioning API
Endpoints for tenant/user/role provisioning (FR-001 → FR-004).
All routes require admin authentication.
"""

import uuid
import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.models import get_db, Tenant, TenantConfig, User, AuditLog
from app.schemas.schemas import (
    TenantCreate, TenantResponse, UserProvision, UserResponse, OnboardRequest, OnboardResponse
)
from app.middleware.rbac import require_admin, create_token

logger = logging.getLogger("saro.admin")
router = APIRouter(prefix="/admin", tags=["Admin Provisioning"])


# ---------------------------------------------------------------------------
# FR-002: Tenant Creation
# ---------------------------------------------------------------------------
@router.post("/tenants", response_model=TenantResponse)
async def create_tenant(
    req: TenantCreate,
    current_user: dict = Depends(require_admin()),
    db: Session = Depends(get_db),
):
    """Admin creates a new tenant with default config."""
    tenant = Tenant(
        name=req.name,
        sector=req.sector,
    )
    db.add(tenant)
    db.flush()

    config = TenantConfig(
        tenant_id=tenant.tenant_id,
        default_roles=req.default_roles,
        tier=req.tier,
    )
    db.add(config)

    # Audit log
    db.add(AuditLog(
        user_id=current_user["user_id"],
        tenant_id=str(tenant.tenant_id),
        action="create_tenant",
        details={"tenant_name": req.name, "sector": req.sector, "tier": req.tier},
    ))
    db.commit()
    db.refresh(tenant)

    return TenantResponse(
        tenant_id=tenant.tenant_id,
        name=tenant.name,
        sector=tenant.sector,
        status=tenant.status,
        tier=config.tier,
        default_roles=config.default_roles,
        created_at=tenant.created_at,
    )


@router.get("/tenants", response_model=List[TenantResponse])
async def list_tenants(
    current_user: dict = Depends(require_admin()),
    db: Session = Depends(get_db),
):
    """List all tenants with their configs."""
    tenants = db.query(Tenant).all()
    results = []
    for t in tenants:
        cfg = t.config
        results.append(TenantResponse(
            tenant_id=t.tenant_id,
            name=t.name,
            sector=t.sector,
            status=t.status,
            tier=cfg.tier if cfg else "trial",
            default_roles=cfg.default_roles if cfg else ["forecaster"],
            created_at=t.created_at,
        ))
    return results


# ---------------------------------------------------------------------------
# FR-003: User Invite & Role Assignment
# ---------------------------------------------------------------------------
@router.post("/tenants/{tenant_id}/users", response_model=UserResponse)
async def provision_user(
    tenant_id: str,
    req: UserProvision,
    current_user: dict = Depends(require_admin()),
    db: Session = Depends(get_db),
):
    """Admin provisions a user under a tenant with roles."""
    # Verify tenant exists
    tenant = db.query(Tenant).filter(Tenant.tenant_id == str(tenant_id)).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Check max roles from tenant config
    config = tenant.config
    if config and len(req.roles) > config.max_roles_per_user:
        raise HTTPException(
            status_code=400,
            detail=f"Max {config.max_roles_per_user} roles allowed for this tenant"
        )

    # Check duplicate
    existing = db.query(User).filter(
        User.tenant_id == str(tenant_id), User.email == req.email
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="User already exists in this tenant")

    user = User(
        tenant_id=tenant_id,
        email=req.email,
        roles=req.roles,
        primary_role=req.primary_role or req.roles[0],
        is_admin=req.is_admin,
    )
    db.add(user)

    # Audit
    db.add(AuditLog(
        user_id=current_user["user_id"],
        tenant_id=str(tenant_id),
        action="provision_user",
        details={"email": req.email, "roles": req.roles},
    ))
    db.commit()
    db.refresh(user)

    # In production: send magic link via SendGrid here
    logger.info(f"Provisioned {req.email} → tenant {tenant_id} with roles {req.roles}")

    return UserResponse.model_validate(user)


@router.get("/tenants/{tenant_id}/users", response_model=List[UserResponse])
async def list_tenant_users(
    tenant_id: str,
    current_user: dict = Depends(require_admin()),
    db: Session = Depends(get_db),
):
    """List all users in a tenant."""
    users = db.query(User).filter(User.tenant_id == str(tenant_id)).all()
    return [UserResponse.model_validate(u) for u in users]


@router.patch("/users/{user_id}/roles", response_model=UserResponse)
async def update_user_roles(
    user_id: uuid.UUID,
    req: UserProvision,
    current_user: dict = Depends(require_admin()),
    db: Session = Depends(get_db),
):
    """Admin updates a user's roles."""
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.roles = req.roles
    user.primary_role = req.primary_role or req.roles[0]

    db.add(AuditLog(
        user_id=current_user["user_id"],
        tenant_id=str(user.tenant_id),
        action="update_roles",
        details={"target_user": str(user_id), "new_roles": req.roles},
    ))
    db.commit()
    db.refresh(user)
    return UserResponse.model_validate(user)
