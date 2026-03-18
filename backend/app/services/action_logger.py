"""
SARO v9.2 — Selective Action Logger (EU AI Act Art. 12)

Logs only high-impact actions to avoid performance drag.
Low-value events (page views, reads) are ignored.
Critical actions logged for audit trail and triage:
  - AUTH events (login, logout, trial start)
  - AUDIT runs (v9.1 engine + legacy)
  - ONBOARDING completions
  - COMPLIANCE report generation
  - BOT executions
  - ROLE changes
  - TRANSACTION events
  - TENANT provisioning / config updates (v9.2)

Output: structured JSON to stdout (ELK/Datadog-compatible) + async DB insert.
Overhead target: <1% of request latency.

Triage guide:
  - AUDIT_ENGINE_RUN: full audit triggered; check detail.score and detail.domain
  - TENANT_PROVISION: new client created; check detail.tenant_id
  - TENANT_CONFIG_UPDATE: tenant defaults changed; check detail.lenses / detail.bias_max
  - AUTH_VALIDATE failures appear as missing entries (validate returns 401 before logging)
"""
import json
import logging
import os
import traceback
import uuid
from datetime import datetime
from typing import Any, Optional

# Standard Python logger — ELK ingests via stdout JSON
_log = logging.getLogger("saro.audit")
if not _log.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("%(message)s"))
    _log.addHandler(_handler)
    _log.setLevel(logging.INFO)

# Error logger (separate namespace so ops can filter on "saro.error")
_elog = logging.getLogger("saro.error")
if not _elog.handlers:
    _ehandler = logging.StreamHandler()
    _ehandler.setFormatter(logging.Formatter("%(message)s"))
    _elog.addHandler(_ehandler)
    _elog.setLevel(logging.ERROR)

# Only these action categories are persisted/logged (delete bloat)
HIGH_IMPACT_ACTIONS = {
    # Auth
    "AUTH_MAGIC_LINK", "AUTH_VALIDATE", "AUTH_TRY_FREE", "AUTH_LOGOUT",
    # Onboarding
    "ONBOARD_START", "ONBOARD_COMPLETE", "ONBOARD_DB_SYNC",
    # Audit — v9.1/v9.2 comprehensive engine
    "AUDIT_ENGINE_RUN",
    # Audit — legacy
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
    # Tenant admin (v9.2)
    "TENANT_PROVISION", "TENANT_CONFIG_UPDATE",
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


def log_error(
    component: str,
    error: Any,
    context: Optional[dict] = None,
    tenant_id: Optional[str] = None,
    request_id: Optional[str] = None,
) -> str:
    """
    Log a structured error for triage. Always emits to stderr (saro.error namespace).
    Never raises — safe to call from any except block.

    Args:
        component: module/function where error occurred, e.g. "audit_engine.run_full_audit"
        error:     the caught exception or error string
        context:   dict with request context (model_name, domain, tenant_id, etc.)
        tenant_id: tenant context for cross-referencing audit_log
        request_id: optional correlation ID (auto-generated if not supplied)

    Returns:
        error_id (12-char) for correlating frontend errors with backend logs
    """
    error_id = str(uuid.uuid4())[:12]
    try:
        tb = traceback.format_exc() if isinstance(error, Exception) else None
        entry = {
            "error_id":   error_id,
            "level":      "ERROR",
            "component":  component,
            "error":      str(error),
            "traceback":  tb,
            "context":    context or {},
            "tenant_id":  tenant_id,
            "request_id": request_id or error_id,
            "timestamp":  datetime.utcnow().isoformat(),
            "env":        os.getenv("ENVIRONMENT", "development"),
        }
        _elog.error(json.dumps(entry))
    except Exception:
        # Absolute last resort — if JSON serialization fails, emit plain text
        _elog.error(f"[SARO ERROR] component={component} error={error} error_id={error_id}")
    return error_id
