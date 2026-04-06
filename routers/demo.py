"""
Demo / Trial Signup routes.

POST /api/v1/demo/signup           — public, no auth required
GET  /api/v1/demo/requests         — super_admin only: list all requests
PATCH /api/v1/demo/requests/{id}   — super_admin only: update status
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from auth import get_current_user, require_role
from database import get_db
from models import DemoRequest
from schemas import DemoRequestIn, DemoRequestOut, DemoRequestStatusUpdateIn

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/demo", tags=["demo"])


@router.post(
    "/signup",
    response_model=DemoRequestOut,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a demo / trial signup request",
    description=(
        "Public endpoint — no authentication required. "
        "Stores the contact details for follow-up. "
        "Duplicate emails (status pending/contacted) return the existing record."
    ),
)
def demo_signup(
    payload: DemoRequestIn,
    db: Annotated[Session, Depends(get_db)],
) -> DemoRequestOut:
    """Accept a demo signup request from a prospective customer."""
    # Prevent duplicate active submissions from the same email
    existing = (
        db.query(DemoRequest)
        .filter(DemoRequest.email == payload.email)
        .order_by(DemoRequest.created_at.desc())
        .first()
    )
    if existing and existing.status in ("pending", "contacted"):
        logger.info(
            "Duplicate demo request from %s (existing id=%s, status=%s)",
            payload.email, existing.id, existing.status,
        )
        return DemoRequestOut.model_validate(existing)

    record = DemoRequest(
        first_name=payload.first_name,
        last_name=payload.last_name,
        email=payload.email,
        contact_number=payload.contact_number,
        company_name=payload.company_name,
        message=payload.message,
        status="pending",
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    logger.info(
        "New demo request: %s %s <%s> (company=%s)",
        payload.first_name, payload.last_name, payload.email,
        payload.company_name or "—",
    )
    return DemoRequestOut.model_validate(record)


@router.get(
    "/requests",
    response_model=list[DemoRequestOut],
    dependencies=[Depends(require_role("super_admin"))],
    summary="List all demo signup requests (super_admin only)",
)
def list_demo_requests(
    db: Annotated[Session, Depends(get_db)],
    _current=Depends(get_current_user),
    status_filter: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> list[DemoRequestOut]:
    """Return all demo requests, optionally filtered by status."""
    q = db.query(DemoRequest).order_by(DemoRequest.created_at.desc())
    if status_filter:
        q = q.filter(DemoRequest.status == status_filter)
    rows = q.limit(limit).offset(offset).all()
    return [DemoRequestOut.model_validate(r) for r in rows]


@router.patch(
    "/requests/{request_id}",
    response_model=DemoRequestOut,
    dependencies=[Depends(require_role("super_admin"))],
    summary="Update demo request status (super_admin only)",
)
def update_demo_request(
    request_id: str,
    payload: DemoRequestStatusUpdateIn,
    db: Annotated[Session, Depends(get_db)],
    _current=Depends(get_current_user),
) -> DemoRequestOut:
    """Update the status of a demo request (e.g., mark as contacted)."""
    try:
        rid = uuid.UUID(request_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid request_id — must be a UUID")
    record = db.get(DemoRequest, rid)
    if not record:
        raise HTTPException(status_code=404, detail="Demo request not found")
    record.status = payload.status
    record.updated_at = datetime.now(tz=timezone.utc)
    db.commit()
    db.refresh(record)
    logger.info("Demo request %s updated to status=%s", rid, payload.status)
    return DemoRequestOut.model_validate(record)
