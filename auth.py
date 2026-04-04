"""
JWT-based authentication and RBAC for SARO.

Roles:
  super_admin — provisions tenants, manages users, configures defaults.
  operator    — submits batches, runs audits, views reports.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from database import get_db
from models import User

logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────
# Lazy helpers — read env vars at call time, not import time.
# This prevents KeyError crashes during Koyeb startup before secrets are injected.

def _secret_key() -> str:
    key = os.environ.get("JWT_SECRET_KEY")
    if not key:
        raise RuntimeError(
            "JWT_SECRET_KEY environment variable is not set. "
            "Add it as a Koyeb secret or set it in your .env file."
        )
    return key


def _algorithm() -> str:
    return os.environ.get("JWT_ALGORITHM", "HS256")


def _expire_minutes() -> int:
    return int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))


_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
_bearer = HTTPBearer(auto_error=True)


# ── Password helpers ──────────────────────────────────────────────────────────


def hash_password(plain: str) -> str:
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_context.verify(plain, hashed)


# ── Token helpers ─────────────────────────────────────────────────────────────


def create_access_token(user: User) -> str:
    """Create a signed JWT containing user identity and role."""
    expire = datetime.now(tz=timezone.utc) + timedelta(minutes=_expire_minutes())
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role,
        "tenant_id": str(user.tenant_id),
        "exp": expire,
    }
    return jwt.encode(payload, _secret_key(), algorithm=_algorithm())


def _decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, _secret_key(), algorithms=[_algorithm()])
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


# ── FastAPI dependencies ───────────────────────────────────────────────────────


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_bearer)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """
    Validate the Bearer token and return the authenticated User row.

    Raises 401 if the token is invalid/expired, 403 if the user is inactive.
    """
    payload = _decode_token(credentials.credentials)
    user_id: str | None = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Malformed token")

    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")
    return user


def require_role(*roles: str):
    """
    Factory that returns a FastAPI dependency enforcing one of the given roles.

    Usage:
        @router.post("/admin/...", dependencies=[Depends(require_role("super_admin"))])
    """

    async def _check(
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{current_user.role}' is not authorised for this action. "
                f"Required: {roles}",
            )
        return current_user

    return _check


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    """Return the User if credentials are valid, else None."""
    user = db.query(User).filter(User.email == email).first()
    if user is None or not verify_password(password, user.hashed_password):
        return None
    return user
