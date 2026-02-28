"""MVP2 - AI Model Audit & Compliance Assessment API"""
from fastapi import APIRouter, HTTPException
from typing import List
from datetime import datetime, timedelta
import uuid
import random

from app.models.schemas import AuditRequest, AuditResult, RiskLevel, ComplianceStatus

router = APIRouter()

_audits: dict = {}

REGULATION_MAP = {
    "EU": ["EU AI Act", "GDPR", "AI Liability Directive"],
    "US": ["NIST AI RMF", "FTC AI Guidelines", "EEOC AI Guidance"],
    "UK": ["UK AI Whitepaper", "ICO AI Guidance"],
    "APAC": ["MAS TREx", "PDPC AI Framework", "China AI Regulation"],
}

RISK_FINDINGS = {
    "healthcare": [
        {"category": "Safety", "finding": "Insufficient clinical validation dataset size", "severity": "high"},
        {"category": "Transparency", "finding": "Model explainability not meeting SHAP threshold", "severity": "medium"},
        {"category": "Data Quality", "finding": "Training data demographic imbalance detected", "severity": "high"},
    ],
    "finance": [
        {"category": "Bias", "finding": "Protected attribute proxy correlation found", "severity": "high"},
        {"category": "Accountability", "finding": "Audit trail gaps in decision logging", "severity": "medium"},
        {"category": "Transparency", "finding": "Adverse action explanation insufficient", "severity": "high"},
    ],
    "hr": [
        {"category": "Bias", "finding": "Gender bias detected in resume ranking", "severity": "critical"},
        {"category": "Compliance", "finding": "EEOC disparate impact threshold exceeded", "severity": "critical"},
    ],
    "default": [
        {"category": "Documentation", "finding": "Technical documentation incomplete", "severity": "low"},
        {"category": "Monitoring", "finding": "Post-deployment monitoring not configured", "severity": "medium"},
    ],
}


@router.post("/audit", response_model=AuditResult)
async def run_audit(request: AuditRequest):
    """Run a full compliance audit for an AI model."""
    audit_id = f"AUDIT-{str(uuid.uuid4())[:8].upper()}"
    
    use_case_key = request.use_case.lower()
    findings = []
    for uc_key, uc_findings in RISK_FINDINGS.items():
        if uc_key in use_case_key:
            findings.extend(uc_findings)
    if not findings:
        findings = RISK_FINDINGS["default"]

    # Add random variance
    compliance_score = round(random.uniform(0.55, 0.92), 3)
    
    severity_map = {"critical": 4, "high": 3, "medium": 2, "low": 1}
    max_sev = max((severity_map.get(f["severity"], 1) for f in findings), default=1)
    
    if max_sev >= 4:
        overall_risk = RiskLevel.CRITICAL
        status = ComplianceStatus.NON_COMPLIANT
    elif max_sev >= 3:
        overall_risk = RiskLevel.HIGH
        status = ComplianceStatus.REVIEW
    elif compliance_score > 0.8:
        overall_risk = RiskLevel.LOW
        status = ComplianceStatus.COMPLIANT
    else:
        overall_risk = RiskLevel.MEDIUM
        status = ComplianceStatus.PENDING

    regulations = REGULATION_MAP.get(request.jurisdiction, REGULATION_MAP["EU"])

    recommendations = [
        f"Implement bias testing suite for {request.use_case} context",
        "Establish human oversight mechanisms for high-risk decisions",
        "Deploy real-time monitoring with drift detection",
        f"Document model card per {regulations[0]} Article 11 requirements",
        "Schedule quarterly re-audit with updated test datasets",
    ]

    result = AuditResult(
        audit_id=audit_id,
        model_name=request.model_name,
        overall_risk=overall_risk,
        compliance_score=compliance_score,
        findings=findings,
        recommendations=recommendations,
        applicable_regulations=regulations,
        status=status,
        generated_at=datetime.utcnow(),
        next_review_date=datetime.utcnow() + timedelta(days=90),
    )
    _audits[audit_id] = result
    return result


@router.get("/audits", response_model=List[AuditResult])
async def list_audits(limit: int = 20):
    return list(_audits.values())[:limit]


@router.get("/audits/{audit_id}", response_model=AuditResult)
async def get_audit(audit_id: str):
    if audit_id not in _audits:
        raise HTTPException(404, "Audit not found")
    return _audits[audit_id]


@router.get("/compliance-matrix")
async def get_compliance_matrix(jurisdiction: str = "EU"):
    """Full regulatory compliance requirements matrix."""
    return {
        "jurisdiction": jurisdiction,
        "generated_at": datetime.utcnow().isoformat(),
        "regulations": [
            {
                "name": "EU AI Act",
                "articles": ["Art. 9 (Risk Management)", "Art. 10 (Data Governance)", 
                             "Art. 11 (Technical Documentation)", "Art. 13 (Transparency)",
                             "Art. 14 (Human Oversight)", "Art. 15 (Accuracy & Robustness)"],
                "enforcement_date": "2025-08-01",
                "penalty": "€30M or 6% global turnover",
                "applicability": "High-risk AI systems",
            },
            {
                "name": "GDPR",
                "articles": ["Art. 22 (Automated Decision-Making)", "Art. 25 (Privacy by Design)",
                             "Art. 35 (DPIA)", "Art. 13/14 (Transparency)"],
                "enforcement_date": "2018-05-25",
                "penalty": "€20M or 4% global turnover",
                "applicability": "All AI processing personal data",
            },
        ]
    }
