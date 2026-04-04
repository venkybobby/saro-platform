"""
Reports API — data endpoints consumed by the Streamlit Reports tab.

GET /api/v1/reports/summary          — aggregate stats across all tenant audits
GET /api/v1/reports/{audit_id}       — full report for one audit
GET /api/v1/reports/{audit_id}/mit   — MIT coverage detail
GET /api/v1/reports/{audit_id}/delta — fixed-delta detail
GET /api/v1/reports/{audit_id}/rules — applied rules list
GET /api/v1/reports/{audit_id}/incidents — similar incidents
"""
from __future__ import annotations

import logging
import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from auth import get_current_user, require_role
from database import get_db
from models import Audit, ScanReport, User
from schemas import (
    AppliedRuleOut,
    AuditReportOut,
    FixedDeltaOut,
    MITCoverageOut,
    SimilarIncidentOut,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/reports", tags=["reports"])


def _get_report_or_404(
    audit_id: uuid.UUID, tenant_id: uuid.UUID, db: Session
) -> dict[str, Any]:
    """Fetch and return the stored report JSON, raising 404 if missing."""
    audit = db.get(Audit, audit_id)
    if not audit or audit.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audit not found")
    if not audit.report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Report not yet generated"
        )
    return audit.report.report_json


@router.get(
    "/summary",
    dependencies=[Depends(require_role("super_admin", "operator"))],
    summary="Aggregate reporting statistics for the current tenant",
)
def reports_summary(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, Any]:
    """
    Returns aggregate metrics across all completed audits for the tenant:
      - total audits, completed, failed
      - average MIT coverage score
      - average risk score
      - fixed-delta distribution
      - top triggered domains
    """
    rows = (
        db.query(Audit, ScanReport)
        .outerjoin(ScanReport, ScanReport.audit_id == Audit.id)
        .filter(
            Audit.tenant_id == current_user.tenant_id,
            Audit.status == "completed",
        )
        .all()
    )

    total = len(rows)
    if total == 0:
        return {
            "total_audits": 0,
            "completed": 0,
            "failed": 0,
            "avg_mit_coverage": None,
            "avg_risk_score": None,
            "avg_fixed_delta": None,
        }

    mit_scores = [r.mit_coverage_score for _, r in rows if r and r.mit_coverage_score is not None]
    risk_scores = [r.overall_risk_score for _, r in rows if r and r.overall_risk_score is not None]
    deltas = [r.fixed_delta for _, r in rows if r and r.fixed_delta is not None]

    # Collect all applied rules across audits
    all_frameworks: list[str] = []
    all_domains: list[str] = []
    for _, r in rows:
        if r and r.report_json:
            for rule in r.report_json.get("applied_rules", []):
                all_frameworks.append(rule.get("framework", ""))
            for gate in r.report_json.get("gates", []):
                if gate.get("gate_id") == 3:
                    for domain, cnt in gate.get("details", {}).get("domain_counts", {}).items():
                        if cnt > 0:
                            all_domains.append(domain)

    # Top-5 frameworks
    from collections import Counter

    top_frameworks = dict(Counter(all_frameworks).most_common(5))
    top_domains = dict(Counter(all_domains).most_common(5))

    # Count failed audits
    failed_count = (
        db.query(func.count(Audit.id))
        .filter(Audit.tenant_id == current_user.tenant_id, Audit.status == "failed")
        .scalar()
        or 0
    )

    return {
        "total_audits": total,
        "completed": total,
        "failed": failed_count,
        "avg_mit_coverage": round(sum(mit_scores) / len(mit_scores), 4) if mit_scores else None,
        "avg_risk_score": round(sum(risk_scores) / len(risk_scores), 4) if risk_scores else None,
        "avg_fixed_delta": round(sum(deltas) / len(deltas), 4) if deltas else None,
        "top_triggered_frameworks": top_frameworks,
        "top_triggered_domains": top_domains,
    }


@router.get(
    "/{audit_id}",
    response_model=AuditReportOut,
    dependencies=[Depends(require_role("super_admin", "operator"))],
)
def get_full_report(
    audit_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> AuditReportOut:
    data = _get_report_or_404(audit_id, current_user.tenant_id, db)
    return AuditReportOut.model_validate(data)


@router.get(
    "/{audit_id}/mit",
    response_model=MITCoverageOut,
    dependencies=[Depends(require_role("super_admin", "operator"))],
    summary="MIT Risk Coverage detail for one audit",
)
def get_mit_coverage(
    audit_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> MITCoverageOut:
    data = _get_report_or_404(audit_id, current_user.tenant_id, db)
    return MITCoverageOut.model_validate(data["mit_coverage"])


@router.get(
    "/{audit_id}/delta",
    response_model=FixedDeltaOut,
    dependencies=[Depends(require_role("super_admin", "operator"))],
    summary="Fixed vs Not-Fixed delta for one audit",
)
def get_fixed_delta(
    audit_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> FixedDeltaOut:
    data = _get_report_or_404(audit_id, current_user.tenant_id, db)
    return FixedDeltaOut.model_validate(data["fixed_delta"])


@router.get(
    "/{audit_id}/rules",
    response_model=list[AppliedRuleOut],
    dependencies=[Depends(require_role("super_admin", "operator"))],
    summary="Applied compliance rules for one audit",
)
def get_applied_rules(
    audit_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[AppliedRuleOut]:
    data = _get_report_or_404(audit_id, current_user.tenant_id, db)
    return [AppliedRuleOut.model_validate(r) for r in data.get("applied_rules", [])]


@router.get(
    "/{audit_id}/incidents",
    response_model=list[SimilarIncidentOut],
    dependencies=[Depends(require_role("super_admin", "operator"))],
    summary="Similar historical incidents for one audit",
)
def get_similar_incidents(
    audit_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[SimilarIncidentOut]:
    data = _get_report_or_404(audit_id, current_user.tenant_id, db)
    return [SimilarIncidentOut.model_validate(i) for i in data.get("similar_incidents", [])]
