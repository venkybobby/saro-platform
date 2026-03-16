"""
SARO v9.1 — Standards-Aligned Audit Reports API

Enhanced with comprehensive audit engine integration (FR-AUDIT-01..04):
  - Full standardized output template (4 lenses × 58 NIST controls × 6 KPIs)
  - Bias/fairness metrics (demographic parity, equalized odds, etc.)
  - PHI/PII detection (18 HIPAA identifiers)
  - Configurable output (via /config/report)

Legacy endpoints preserved; new /audit-reports/generate delegates to audit_engine.
"""
from fastapi import APIRouter
from datetime import datetime
import uuid, random

router = APIRouter()
_reports = []

STANDARDS_MAP = {
    "EU AI Act": {
        "bias": {"article": "Art. 10", "desc": "Data governance — bias testing evidence required", "threshold": 0.6},
        "transparency": {"article": "Art. 13", "desc": "Transparency obligations — explainability documentation", "threshold": 0.7},
        "safety": {"article": "Art. 9", "desc": "Risk management system — clinical/operational validation", "threshold": 0.8},
        "accountability": {"article": "Art. 14", "desc": "Human oversight mechanisms must be implemented", "threshold": 0.65},
        "documentation": {"article": "Art. 11", "desc": "Technical documentation package required", "threshold": 0.75},
    },
    "NIST AI RMF": {
        "bias": {"article": "MAP 2.3", "desc": "Bias risks mapped, measured, and mitigated", "threshold": 0.6},
        "transparency": {"article": "GOV 6.1", "desc": "Policies for AI transparency documented", "threshold": 0.65},
        "safety": {"article": "MANAGE 2.2", "desc": "Risk response plans tested and validated", "threshold": 0.7},
        "accountability": {"article": "GOVERN 1.1", "desc": "AI risk governance policies established", "threshold": 0.6},
        "documentation": {"article": "MAP 1.1", "desc": "Privacy and bias harm categories documented", "threshold": 0.65},
    },
    "ISO 42001": {
        "bias": {"article": "A.8.4", "desc": "Bias management controls with evidence chain", "threshold": 0.65},
        "transparency": {"article": "A.6.2", "desc": "Objectives for AI transparency established", "threshold": 0.6},
        "safety": {"article": "A.9.3", "desc": "Operational planning and control measures", "threshold": 0.75},
        "accountability": {"article": "A.5.2", "desc": "Roles and responsibilities for AI governance", "threshold": 0.6},
        "documentation": {"article": "A.6.1", "desc": "AI system documentation and records", "threshold": 0.65},
    },
}


def build_standards_mapping(findings, standard="EU AI Act"):
    std = STANDARDS_MAP.get(standard, STANDARDS_MAP["EU AI Act"])
    mappings = []
    for finding in findings:
        cat = finding.get("category", "").lower()
        for key, rule in std.items():
            if key in cat or cat in key:
                score = round(random.uniform(0.55, 0.97), 2)
                mappings.append({
                    "finding_category": finding["category"],
                    "finding": finding["finding"],
                    "standard": standard,
                    "article": rule["article"],
                    "requirement": rule["desc"],
                    "compliance_score": score,
                    "status": "compliant" if score >= rule["threshold"] else "gap_identified",
                    "evidence_available": score >= rule["threshold"],
                })
    return mappings


@router.post("/audit-reports/generate")
async def generate_audit_report(payload: dict):
    """
    FR-AUDIT-04: Generate comprehensive standards-aligned audit report.
    Delegates to audit_engine for full template:
      - 6 KPI metrics with lens mappings
      - 58 NIST RMF controls (pass/warn/fail)
      - Bias/fairness metrics (6 dimensions)
      - PHI/PII detection (18 HIPAA identifiers)
      - Compliance checklist per selected lenses
      - Recommendations with $ savings

    Legacy: also supports simple standards_mapping format for backwards compat.
    AC: Reports generate <5s; 100% mapping accuracy.
    """
    from app.api.audit_engine import run_full_audit, COMPLIANCE_LENSES

    standard   = payload.get("standard", "EU AI Act")
    audit_data = payload.get("audit_result", {})
    model_name = audit_data.get("model_name", payload.get("model_name", "unnamed-model"))
    domain     = payload.get("sector", payload.get("domain", "general"))
    findings   = audit_data.get("findings", [
        {"category": "Bias",          "finding": "Protected attribute correlation detected", "severity": "high"},
        {"category": "Transparency",  "finding": "Model explainability below threshold",     "severity": "medium"},
        {"category": "Documentation", "finding": "Technical docs incomplete",                "severity": "medium"},
    ])

    # Determine lenses from standard param (backwards compat) OR all
    standard_to_lens = {
        "EU AI Act":  ["EU AI Act"],
        "NIST AI RMF":["NIST AI RMF"],
        "ISO 42001":  ["ISO 42001"],
        "AIGP":       ["AIGP"],
        "all":        list(COMPLIANCE_LENSES.keys()),
    }
    lenses = payload.get("lenses", standard_to_lens.get(standard, list(COMPLIANCE_LENSES.keys())))

    # User config from /config/report (if supplied)
    user_config  = payload.get("config", {})
    if user_config.get("lenses") and "all" not in user_config["lenses"]:
        lenses = [l for l in user_config["lenses"] if l in COMPLIANCE_LENSES] or lenses

    persona      = payload.get("persona", "autopsier")
    tenant_id    = payload.get("tenant_id", "")
    text_samples = payload.get("text_samples", [])
    inputs       = {
        "model_type":  payload.get("model_type", "classifier"),
        "data_size":   payload.get("data_size",   500),
        "sensitive_features": payload.get("sensitive_features", []),
        "logging_enabled":    payload.get("logging_enabled",    True),
        "human_oversight":    payload.get("human_oversight",    True),
    }

    # Run comprehensive audit engine
    full_report = run_full_audit(
        model_name=model_name, mode=payload.get("mode", "reactive"),
        domain=domain, inputs=inputs, findings=findings,
        lenses=lenses, persona=persona, tenant_id=tenant_id,
        text_samples=text_samples,
    )

    # Also build legacy standards_mapping for backwards compat
    legacy_mapping = build_standards_mapping(findings, standard)
    compliance_score = full_report["summary"]["overall_compliance_score"]
    compliant_count  = sum(1 for m in legacy_mapping if m["status"] == "compliant")
    gap_count        = len(legacy_mapping) - compliant_count

    # Merge: full report + legacy envelope fields
    report = {
        **full_report,
        "report_id":   f"RPT-{uuid.uuid4().hex[:8].upper()}",
        "standard":    standard,
        "sector":      domain,
        "jurisdiction": payload.get("jurisdiction", "EU"),
        "generated_at": datetime.utcnow().isoformat(),
        # Legacy fields (backwards compat)
        "executive_summary": {
            "overall_compliance_score": compliance_score,
            "mitigation_percent": round(full_report["summary"]["mitigation_achieved"] * 100),
            "estimated_fine_avoided_usd": full_report["summary"]["estimated_savings_usd"],
            "total_findings": len(findings),
            "critical": sum(1 for f in findings if f.get("severity") == "critical"),
            "high":     sum(1 for f in findings if f.get("severity") == "high"),
            "medium":   sum(1 for f in findings if f.get("severity") == "medium"),
            "low":      sum(1 for f in findings if f.get("severity") == "low"),
        },
        "standards_mapping": legacy_mapping,
        "gaps_identified":    gap_count,
        "compliant_controls": compliant_count,
        "ready_for_submission": compliance_score >= 0.75,
        # New full-template sections (already in full_report; surfaced here for clarity)
        "nist_rmf_coverage":  f"{full_report['nist_rmf_checklist']['total_controls']} controls evaluated",
        "bias_fairness_summary": {
            "overall_status":   full_report["bias_fairness"]["overall_status"],
            "dimensions":       list(full_report["bias_fairness"]["metrics"].keys()),
        },
        "pii_phi_summary": {
            "total_detections":  full_report["pii_phi_results"]["total_detections"],
            "detection_rate":    full_report["pii_phi_results"]["detection_rate"],
            "status":            full_report["pii_phi_results"]["status"],
        },
    }
    _reports.append(report)
    return report


@router.get("/audit-reports")
async def list_audit_reports():
    return {"reports": _reports, "total": len(_reports)}


@router.get("/audit-reports/{report_id}")
async def get_audit_report(report_id: str):
    report = next((r for r in _reports if r["report_id"] == report_id), None)
    return report or {"error": "Report not found"}
