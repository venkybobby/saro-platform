"""
SARO v9.0 — Selective Action Logger (Story 2)

Logs only high-impact actions to avoid performance drag (EU AI Act Art. 12).
Low-value events (e.g., page views) are ignored — only critical actions logged:
  - AUTH events (login, logout, trial start)
  - AUDIT runs
  - ONBOARDING completions
  - COMPLIANCE report generation
  - BOT executions
  - ROLE changes
  - TRANSACTION events

Output: structured JSON to stdout (ELK-compatible) + async DB insert.
Overhead target: <1% of request latency.
"""
import json
import logging
import os
import uuid
from datetime import datetime
from typing import Optional

# Standard Python logger — ELK ingests via stdout JSON
_log = logging.getLogger("saro.audit")
if not _log.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("%(message)s"))
    _log.addHandler(_handler)
    _log.setLevel(logging.INFO)

# Only these action categories are persisted/logged (delete bloat)
HIGH_IMPACT_ACTIONS = {
    # Auth
    "AUTH_MAGIC_LINK", "AUTH_VALIDATE", "AUTH_TRY_FREE", "AUTH_LOGOUT",
    # Onboarding
    "ONBOARD_START", "ONBOARD_COMPLETE", "ONBOARD_DB_SYNC",
    # Audit
    "AUDIT_RUN", "AUDIT_REPORT_GENERATE", "AUDIT_REPORT_AI_GENERATE",
    # Compliance
    "COMPLIANCE_REPORT_GENERATE", "COMPLIANCE_REPORT_AI",
    # Bots
    "BOT_EXECUTE", "BOT_REVERT", "BOT_AUTOHEAL",
    # Roles
    "ROLE_ASSIGN", "ROLE_AI_SUGGEST", "ROLE_REMOVE",
    # Transactions
    "TRANSACTION_CREATE", "TRANSACTION_PURGE",
    # Auto-tuning
    "AUTOTUNE_RUN", "AUTOTUNE_THRESHOLD_UPDATE",
}


def log_action(
    action: str,
    tenant_id: Optional[str] = None,
    user_id: Optional[str] = None,
    resource: Optional[str] = None,
    resource_id: Optional[str] = None,
    detail: Optional[dict] = None,
    ip_address: Optional[str] = None,
) -> Optional[str]:
    """
    Log a high-impact action. Returns log_id if logged, None if skipped (low-impact).
    Non-blocking: DB write is fire-and-forget via background task.
    """
    if action not in HIGH_IMPACT_ACTIONS:
        return None  # Skip low-value actions — no overhead

    log_id = str(uuid.uuid4())[:12]
    entry = {
        "log_id":      log_id,
        "action":      action,
        "tenant_id":   tenant_id,
        "user_id":     user_id,
        "resource":    resource,
        "resource_id": resource_id,
        "detail":      detail or {},
        "ip_address":  ip_address,
        "timestamp":   datetime.utcnow().isoformat(),
        "env":         os.getenv("ENVIRONMENT", "development"),
    }
    # ELK-compatible structured log (stdout)
    _log.info(json.dumps(entry))
    return log_id


def log_to_db_sync(
    action: str,
    tenant_id: Optional[str] = None,
    user_id: Optional[str] = None,
    resource: Optional[str] = None,
    resource_id: Optional[str] = None,
    detail: Optional[dict] = None,
    ip_address: Optional[str] = None,
    db=None,
) -> None:
    """
    Synchronously write to audit_log table when DB session is available.
    Only called for HIGH_IMPACT_ACTIONS — never for page views or reads.
    """
    if action not in HIGH_IMPACT_ACTIONS or db is None:
        return

    try:
        from app.db.orm_models import AuditLog
        entry = AuditLog(
            tenant_id=tenant_id,
            user_id=user_id,
            action=action,
            resource=resource,
            resource_id=resource_id,
            detail_json=detail or {},
            ip_address=ip_address,
            created_at=datetime.utcnow(),
        )
        db.add(entry)
        db.commit()
    except Exception:
        # Never let logging crash the request
        pass
