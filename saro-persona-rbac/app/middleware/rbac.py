"""
SARO — RBAC Middleware & Dependencies
Core enforcement layer for persona-limited views (FR-005).
Validates JWT tokens, checks role permissions, logs access attempts.
"""

import os
import time
import logging
from typing import List, Optional
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.models import get_db, User, PersonaPermission, AuditLog

logger = logging.getLogger("saro.rbac")

SECRET_KEY = os.getenv("SARO_JWT_SECRET", "saro-dev-secret-change-in-prod")
ALGORITHM = "HS256"
ADMIN_EMAILS = set(os.getenv("SARO_ADMIN_EMAILS", "admin@saro.ai").split(","))
ADMIN_IP_ALLOWLIST = set(os.getenv("SARO_ADMIN_IPS", "127.0.0.1,::1").split(","))

security = HTTPBearer(auto_error=False)


# ---------------------------------------------------------------------------
# Token Helpers
# ---------------------------------------------------------------------------
def create_token(user: User, expires_seconds: int = 86400) -> str:
    payload = {
        "user_id": str(user.user_id),
        "tenant_id": str(user.tenant_id),
        "email": user.email,
        "roles": user.roles,
        "primary_role": user.primary_role,
        "is_admin": user.is_admin,
        "exp": time.time() + expires_seconds,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("exp", 0) < time.time():
            raise HTTPException(status_code=401, detail="Token expired")
        return payload
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")


# ---------------------------------------------------------------------------
# FastAPI Dependencies
# ---------------------------------------------------------------------------
async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> dict:
    """Extract and validate current user from JWT. Returns token payload."""
    if not credentials:
        raise HTTPException(status_code=401, detail="Authentication required")

    payload = decode_token(credentials.credentials)
    # Verify user still exists and is active
    user = db.query(User).filter(User.user_id == payload["user_id"]).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User deactivated or not found")

    payload["_db_user"] = user
    return payload


def require_roles(*allowed_roles: str):
    """Dependency factory: require user to have at least one of the specified roles."""
    async def _check(
        request: Request,
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db),
    ):
        user_roles = set(current_user.get("roles", []))
        if current_user.get("is_admin"):
            user_roles.add("admin")

        if not user_roles.intersection(set(allowed_roles)):
            # Log the denial (NFR-002)
            _log_access(db, current_user, "access_denied", request.url.path,
                        {"required": list(allowed_roles), "had": list(user_roles)},
                        request.client.host if request.client else None)
            raise HTTPException(
                status_code=403,
                detail=f"Requires one of roles: {allowed_roles}. You have: {list(user_roles)}"
            )
        return current_user
    return _check


def require_admin():
    """Dependency: require admin role + IP/email allowlist check."""
    async def _check(
        request: Request,
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db),
    ):
        if not current_user.get("is_admin"):
            _log_access(db, current_user, "admin_denied", request.url.path, None,
                        request.client.host if request.client else None)
            raise HTTPException(status_code=403, detail="Admin access required")

        client_ip = request.client.host if request.client else "unknown"
        email = current_user.get("email", "")

        # IP allowlist check (NFR-002: admin restricted to internal IPs)
        if ADMIN_IP_ALLOWLIST != {"*"} and client_ip not in ADMIN_IP_ALLOWLIST:
            if email not in ADMIN_EMAILS:
                _log_access(db, current_user, "admin_ip_denied", request.url.path,
                            {"ip": client_ip}, client_ip)
                raise HTTPException(status_code=403, detail="Admin access not allowed from this IP")

        return current_user
    return _check


def require_feature(feature_key: str):
    """Dependency factory: check persona has access to a specific feature."""
    async def _check(
        request: Request,
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db),
    ):
        primary_role = current_user.get("primary_role", "viewer")

        # Admin bypasses feature checks
        if current_user.get("is_admin"):
            return current_user

        perm = db.query(PersonaPermission).filter(
            PersonaPermission.role == primary_role,
            PersonaPermission.feature_key == feature_key,
        ).first()

        if not perm or perm.access_level == "denied":
            _log_access(db, current_user, "feature_denied", feature_key,
                        {"role": primary_role}, request.client.host if request.client else None)
            raise HTTPException(
                status_code=403,
                detail=f"Role '{primary_role}' does not have access to '{feature_key}'"
            )

        # Attach access level for downstream use (e.g., read_only vs full)
        current_user["_access_level"] = perm.access_level
        return current_user
    return _check


# ---------------------------------------------------------------------------
# Audit Helper
# ---------------------------------------------------------------------------
def _log_access(db: Session, user: dict, action: str, resource: str,
                details: Optional[dict], ip: Optional[str]):
    try:
        log = AuditLog(
            user_id=user.get("user_id"),
            tenant_id=user.get("tenant_id"),
            action=action,
            resource=resource,
            details=details,
            ip_address=ip,
        )
        db.add(log)
        db.commit()
    except Exception as e:
        logger.error(f"Audit log failed: {e}")
        db.rollback()
