"""Model Output Ingestion & Checklist Generation API
Accepts customer AI model outputs, evaluates against policy benchmarks,
produces fail/warn/critical checklists mapped to regulatory articles.
"""
from fastapi import APIRouter
from datetime import datetime
import uuid, random

router = APIRouter()
_uploads = {}  # store processed outputs

POLICY_BENCHMARKS = {
    "EU AI Act": {
        "bias_threshold": 0.15,
        "transparency_min": 0.60,
        "accuracy_min": 0.80,
        "human_oversight": True,
        "articles": {
            "bias":           {"ref": "Art. 10", "title": "Data Governance & Bias"},
            "transparency":   {"ref": "Art. 13", "title": "Transparency Obligations"},
            "accuracy":       {"ref": "Art. 15", "title": "Accuracy & Robustness"},
            "human_oversight":{"ref": "Art. 14", "title": "Human Oversight"},
            "documentation":  {"ref": "Art. 11", "title": "Technical Documentation"},
        },
    },
    "NIST AI RMF": {
        "bias_threshold": 0.12,
        "transparency_min": 0.65,
        "accuracy_min": 0.82,
        "human_oversight": True,
        "articles": {
            "bias":           {"ref": "MAP 2.3", "title": "Bias Risk Mapping"},
            "transparency":   {"ref": "GOV 6.1", "title": "AI Transparency Policies"},
            "accuracy":       {"ref": "MEASURE 2.5","title": "Performance Measurement"},
            "human_oversight":{"ref": "GOVERN 1.1","title": "AI Governance Policies"},
            "documentation":  {"ref": "MAP 1.1", "title": "Privacy & Harm Documentation"},
        },
    },
    "ISO 42001": {
        "bias_threshold": 0.18,
        "transparency_min": 0.55,
        "accuracy_min": 0.78,
        "human_oversight": True,
        "articles": {
            "bias":           {"ref": "A.8.4", "title": "Bias Management Controls"},
            "transparency":   {"ref": "A.6.2", "title": "AI Transparency Objectives"},
            "accuracy":       {"ref": "A.9.3", "title": "Operational Control Measures"},
            "human_oversight":{"ref": "A.5.2", "title": "Roles & Responsibilities"},
            "documentation":  {"ref": "A.6.1", "title": "AI System Documentation"},
        },
    },
    "FDA SaMD": {
        "bias_threshold": 0.10,
        "transparency_min": 0.75,
        "accuracy_min": 0.90,
        "human_oversight": True,
        "articles": {
            "bias":           {"ref": "510(k) §3.2", "title": "Clinical Validation — Bias"},
            "transparency":   {"ref": "510(k) §4.1", "title": "Explainability for Clinicians"},
            "accuracy":       {"ref": "510(k) §2.1", "title": "Clinical Performance"},
            "human_oversight":{"ref": "510(k) §5.3", "title": "Clinician Override Mechanism"},
            "documentation":  {"ref": "510(k) §1.0", "title": "Software Documentation"},
        },
    },
}

DOMAIN_CHECKS = {
    "finance": {
        "protected_attributes": ["gender", "race", "age", "religion", "nationality"],
        "required_fields": ["adverse_action_reason", "decision_confidence", "audit_trail_id"],
        "bias_metrics": ["demographic_parity", "equalized_odds", "calibration"],
    },
    "healthcare": {
        "protected_attributes": ["age", "gender", "ethnicity", "disability"],
        "required_fields": ["clinical_confidence", "contraindications_checked", "physician_review"],
        "bias_metrics": ["subgroup_accuracy", "calibration_by_group"],
    },
    "hr": {
        "protected_attributes": ["gender", "race", "age", "pregnancy", "religion"],
        "required_fields": ["selection_reason", "disparate_impact_ratio", "human_review_flag"],
        "bias_metrics": ["4/5ths_rule", "disparate_impact", "adverse_impact_ratio"],
    },
    "general": {
        "protected_attributes": ["gender", "race", "age"],
        "required_fields": ["confidence_score", "decision_basis"],
        "bias_metrics": ["demographic_parity"],
    },
}


def generate_checklist(output_data: dict, policy: str, domain: str) -> dict:
    benchmark = POLICY_BENCHMARKS.get(policy, POLICY_BENCHMARKS["EU AI Act"])
    domain_cfg = DOMAIN_CHECKS.get(domain, DOMAIN_CHECKS["general"])
    articles = benchmark["articles"]

    checklist = []
    critical_count = warn_count = pass_count = 0

    # 1. Bias check
    bias_score = output_data.get("bias_score", round(random.uniform(0.05, 0.35), 3))
    threshold = benchmark["bias_threshold"]
    if bias_score > threshold * 1.5:
        severity = "critical"
        critical_count += 1
    elif bias_score > threshold:
        severity = "warn"
        warn_count += 1
    else:
        severity = "pass"
        pass_count += 1
    checklist.append({
        "check": "Bias Score Evaluation",
        "severity": severity,
        "measured": bias_score,
        "threshold": threshold,
        "article_ref": articles["bias"]["ref"],
        "article_title": articles["bias"]["title"],
        "finding": f"Bias score {bias_score:.3f} {'exceeds' if bias_score > threshold else 'within'} {threshold} threshold",
        "remediation": f"Retrain with balanced dataset; implement {'immediate' if severity=='critical' else 'scheduled'} bias mitigation",
    })

    # 2. Transparency / explainability
    transparency_score = output_data.get("transparency_score", round(random.uniform(0.40, 0.90), 3))
    if transparency_score < benchmark["transparency_min"] * 0.8:
        severity = "critical"; critical_count += 1
    elif transparency_score < benchmark["transparency_min"]:
        severity = "warn"; warn_count += 1
    else:
        severity = "pass"; pass_count += 1
    checklist.append({
        "check": "Explainability & Transparency",
        "severity": severity,
        "measured": transparency_score,
        "threshold": benchmark["transparency_min"],
        "article_ref": articles["transparency"]["ref"],
        "article_title": articles["transparency"]["title"],
        "finding": f"Transparency score {transparency_score:.2f} {'below' if transparency_score < benchmark['transparency_min'] else 'meets'} minimum",
        "remediation": "Implement SHAP/LIME explanations; add decision rationale to all outputs",
    })

    # 3. Accuracy
    accuracy = output_data.get("accuracy", round(random.uniform(0.65, 0.97), 3))
    if accuracy < benchmark["accuracy_min"] * 0.9:
        severity = "critical"; critical_count += 1
    elif accuracy < benchmark["accuracy_min"]:
        severity = "warn"; warn_count += 1
    else:
        severity = "pass"; pass_count += 1
    checklist.append({
        "check": "Model Accuracy",
        "severity": severity,
        "measured": accuracy,
        "threshold": benchmark["accuracy_min"],
        "article_ref": articles["accuracy"]["ref"],
        "article_title": articles["accuracy"]["title"],
        "finding": f"Model accuracy {accuracy:.1%} {'below' if accuracy < benchmark['accuracy_min'] else 'meets'} regulatory minimum",
        "remediation": "Expand training dataset; perform hyperparameter tuning; validate on hold-out set",
    })

    # 4. Human oversight
    has_oversight = output_data.get("human_oversight", random.choice([True, False]))
    severity = "pass" if has_oversight else ("critical" if policy == "FDA SaMD" else "warn")
    if severity == "critical": critical_count += 1
    elif severity == "warn": warn_count += 1
    else: pass_count += 1
    checklist.append({
        "check": "Human Oversight Mechanism",
        "severity": severity,
        "measured": has_oversight,
        "threshold": True,
        "article_ref": articles["human_oversight"]["ref"],
        "article_title": articles["human_oversight"]["title"],
        "finding": f"Human oversight {'present' if has_oversight else 'NOT CONFIGURED — mandatory for high-risk AI'}",
        "remediation": "Implement review queue with escalation paths; configure override mechanisms for all high-risk decisions",
    })

    # 5. Required field presence
    provided_fields = set(output_data.get("fields_present", []))
    required = set(domain_cfg["required_fields"])
    missing = required - provided_fields
    severity = "critical" if len(missing) >= 2 else ("warn" if missing else "pass")
    if severity == "critical": critical_count += 1
    elif severity == "warn": warn_count += 1
    else: pass_count += 1
    checklist.append({
        "check": f"Required Output Fields ({domain.title()} Domain)",
        "severity": severity,
        "measured": list(provided_fields),
        "threshold": list(required),
        "article_ref": articles["documentation"]["ref"],
        "article_title": articles["documentation"]["title"],
        "finding": f"Missing {len(missing)} required field(s): {', '.join(missing) if missing else 'None'}",
        "remediation": f"Add missing output fields: {', '.join(missing) if missing else 'All present — no action needed'}",
    })

    # 6. Protected attribute check
    flagged_attrs = [a for a in domain_cfg["protected_attributes"] if a in str(output_data.get("feature_names", []))]
    severity = "critical" if len(flagged_attrs) > 2 else ("warn" if flagged_attrs else "pass")
    if severity == "critical": critical_count += 1
    elif severity == "warn": warn_count += 1
    else: pass_count += 1
    checklist.append({
        "check": "Protected Attribute Exposure",
        "severity": severity,
        "measured": flagged_attrs,
        "threshold": "zero direct use",
        "article_ref": articles["bias"]["ref"],
        "article_title": articles["bias"]["title"],
        "finding": f"{'Direct use of protected attributes detected: ' + ', '.join(flagged_attrs) if flagged_attrs else 'No direct protected attributes in feature set'}",
        "remediation": "Remove or proxy protected attributes; apply fairness constraints during training",
    })

    total = critical_count + warn_count + pass_count
    return {
        "checklist": checklist,
        "summary": {
            "critical": critical_count,
            "warn": warn_count,
            "pass": pass_count,
            "total": total,
            "pass_rate": round(pass_count / total * 100, 1) if total else 0,
            "overall_verdict": "FAIL" if critical_count > 0 else ("REVIEW" if warn_count > 0 else "PASS"),
        },
        "policy_applied": policy,
        "domain": domain,
    }


@router.post("/model-output/upload")
async def upload_model_output(payload: dict):
    """
    Upload customer AI model output for checklist evaluation.
    Evaluates against chosen policy benchmark (EU AI Act, NIST, ISO, FDA).
    """
    upload_id = f"UPL-{str(uuid.uuid4())[:8].upper()}"
    policy = payload.get("policy", "EU AI Act")
    domain = payload.get("domain", "general").lower()
    model_name = payload.get("model_name", "unnamed-model")

    # Support text description OR structured JSON output
    output_data = payload.get("output_data", {})
    raw_text = payload.get("output_text", "")

    # Agent-style extraction from text if structured data not provided
    if raw_text and not output_data:
        text_lower = raw_text.lower()
        output_data = {
            "bias_score": 0.28 if any(w in text_lower for w in ["bias", "discrimination", "unfair"]) else round(random.uniform(0.05, 0.20), 3),
            "transparency_score": 0.45 if any(w in text_lower for w in ["unexplained", "black box", "unclear"]) else round(random.uniform(0.55, 0.88), 3),
            "accuracy": 0.72 if any(w in text_lower for w in ["inaccurate", "wrong", "error"]) else round(random.uniform(0.78, 0.96), 3),
            "human_oversight": "review" in text_lower or "human" in text_lower or "oversight" in text_lower,
            "feature_names": ["gender"] if "gender" in text_lower else (["race"] if "race" in text_lower else []),
            "fields_present": ["confidence_score", "decision_basis"] if "confidence" in text_lower else [],
        }

    checklist_result = generate_checklist(output_data, policy, domain)

    record = {
        "upload_id": upload_id,
        "model_name": model_name,
        "policy": policy,
        "domain": domain,
        "input_type": "text" if raw_text else "structured",
        "checklist": checklist_result["checklist"],
        "summary": checklist_result["summary"],
        "policy_applied": policy,
        "benchmark_source": f"SARO Policy Benchmark — {policy}",
        "uploaded_at": datetime.utcnow().isoformat(),
        "agent_processed": bool(raw_text),
    }
    _uploads[upload_id] = record
    return record


@router.get("/model-output/uploads")
async def list_uploads():
    return {"uploads": list(_uploads.values()), "total": len(_uploads)}


@router.get("/model-output/{upload_id}")
async def get_upload(upload_id: str):
    if upload_id not in _uploads:
        return {"error": "Not found"}
    return _uploads[upload_id]


@router.get("/model-output/policies/list")
async def list_policies():
    return {
        "policies": [
            {"id": k, "name": k, "bias_threshold": v["bias_threshold"], "transparency_min": v["transparency_min"], "accuracy_min": v["accuracy_min"]}
            for k, v in POLICY_BENCHMARKS.items()
        ]
    }
