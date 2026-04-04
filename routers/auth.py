"""
Authentication routes.

POST /api/v1/auth/token     — login → JWT
POST /api/v1/auth/register  — super_admin creates a new user
GET  /api/v1/auth/me        — current user info
POST /api/v1/tenants        — super_admin creates a tenant
GET  /api/v1/tenants        — super_admin lists tenants
"""
from __future__ import annotations

import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from auth import (
    authenticate_user,
    create_access_token,
    get_current_user,
    hash_password,
    require_role,
)
from database import get_db
from models import Tenant, User
from schemas import (
    LoginIn,
    TenantCreateIn,
    TenantOut,
    TokenOut,
    UserCreateIn,
    UserOut,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
tenants_router = APIRouter(prefix="/api/v1/tenants", tags=["tenants"])


@router.post("/token", response_model=TokenOut)
def login(payload: LoginIn, db: Annotated[Session, Depends(get_db)]) -> TokenOut:
    """Exchange email + password for a JWT access token."""
    user = authenticate_user(db, payload.email, payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(user)
    logger.info("User %s logged in (role=%s)", user.email, user.role)
    return TokenOut(access_token=token)


@router.post(
    "/register",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("super_admin"))],
)
def register_user(
    payload: UserCreateIn,
    db: Annotated[Session, Depends(get_db)],
    _current: Annotated[User, Depends(get_current_user)],
) -> UserOut:
    """Super admin creates a new user within a tenant."""
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Email {payload.email!r} is already registered",
        )
    tenant = db.get(Tenant, payload.tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant {payload.tenant_id} not found",
        )
    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role=payload.role,
        tenant_id=payload.tenant_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info("Created user %s (role=%s, tenant=%s)", user.email, user.role, user.tenant_id)
    return UserOut.model_validate(user)


@router.get("/me", response_model=UserOut)
def me(current: Annotated[User, Depends(get_current_user)]) -> UserOut:
    """Return the currently authenticated user."""
    return UserOut.model_validate(current)


# ─────────────────────────────────────────────────────────────────────────────
# Tenant management (super_admin only)
# ─────────────────────────────────────────────────────────────────────────────


@tenants_router.post(
    "",
    response_model=TenantOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("super_admin"))],
)
def create_tenant(
    payload: TenantCreateIn,
    db: Annotated[Session, Depends(get_db)],
    _current: Annotated[User, Depends(get_current_user)],
) -> TenantOut:
    """Provision a new tenant (super_admin only)."""
    existing = db.query(Tenant).filter(Tenant.slug == payload.slug).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Tenant slug {payload.slug!r} already exists",
        )
    tenant = Tenant(name=payload.name, slug=payload.slug)
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    logger.info("Provisioned tenant %s (%s)", tenant.name, tenant.slug)
    return TenantOut.model_validate(tenant)


@tenants_router.get(
    "",
    response_model=list[TenantOut],
    dependencies=[Depends(require_role("super_admin"))],
)
def list_tenants(
    db: Annotated[Session, Depends(get_db)],
    _current: Annotated[User, Depends(get_current_user)],
) -> list[TenantOut]:
    """List all tenants (super_admin only)."""
    return [TenantOut.model_validate(t) for t in db.query(Tenant).all()]
