"""
SARO — Auth API
Magic link login, token generation, and session management.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.models import get_db, User
from app.schemas.schemas import MagicLinkRequest
from app.middleware.rbac import create_token

logger = logging.getLogger("saro.auth")
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/magic-link")
async def request_magic_link(req: MagicLinkRequest, db: Session = Depends(get_db)):
    """
    Send a magic link to the user's email.
    In production: integrates with SendGrid. Here: returns token directly for dev.
    """
    user = db.query(User).filter(User.email == req.email, User.is_active == True).first()
    if not user:
        # Don't reveal whether email exists (security)
        return {"message": "If this email is registered, a magic link has been sent."}

    token = create_token(user, expires_seconds=1800)  # 30 min

    # In production: send_magic_link(req.email, f"{FRONTEND_URL}/login?token={token}")
    logger.info(f"Magic link generated for {req.email}")

    # Dev mode: return token directly
    return {
        "message": "Magic link sent (dev mode: token included)",
        "token": token,
        "roles": user.roles,
        "primary_role": user.primary_role,
    }


@router.post("/login")
async def login_with_token(token: str, db: Session = Depends(get_db)):
    """
    Validate a magic link token and return a session JWT.
    """
    from app.middleware.rbac import decode_token
    payload = decode_token(token)

    user = db.query(User).filter(User.user_id == payload["user_id"]).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid or deactivated user")

    # Issue a longer-lived session token
    session_token = create_token(user, expires_seconds=86400)  # 24h

    from datetime import datetime, timezone
    user.last_login = datetime.now(timezone.utc)
    db.commit()

    return {
        "token": session_token,
        "user_id": str(user.user_id),
        "email": user.email,
        "roles": user.roles,
        "primary_role": user.primary_role,
        "is_admin": user.is_admin,
    }
