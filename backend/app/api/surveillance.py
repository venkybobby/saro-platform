"""Ethics & Surveillance Risk Module - from AI Surveillance Demo spec"""
from fastapi import APIRouter
from datetime import datetime
import uuid
import random

router = APIRouter()

SURVEILLANCE_PATTERNS = {
    "biometric_id": ["facial recognition", "fingerprint", "retina scan", "voice print", "gait analysis"],
    "mass_surveillance": ["bulk data collection", "population monitoring", "tracking without consent", "social scoring"],
    "emotion_recognition": ["emotion detection", "sentiment tracking", "mood analysis", "psychological profiling"],
    "location_tracking": ["GPS tracking", "movement pattern", "location history", "geofencing without consent"],
    "predictive_policing": ["crime prediction", "pre-crime", "behavioral prediction", "threat scoring"],
}

GDPR_ARTICLES = {
    "biometric_id": ["Art. 9 (Special Category Data)", "Art. 22 (Automated Decision-Making)"],
    "mass_surveillance": ["Art. 5 (Data Minimisation)", "Art. 6 (Lawful Basis)", "Art. 25 (Privacy by Design)"],
    "emotion_recognition": ["Art. 9 (Special Category)", "Art. 13 (Transparency)"],
    "location_tracking": ["Art. 6 (Lawful Basis)", "Art. 17 (Right to Erasure)"],
    "predictive_policing": ["Art. 22 (Automated Decisions)", "Art. 35 (DPIA Required)"],
}

EU_AI_ACT_PROHIBITED = ["biometric_id", "mass_surveillance", "emotion_recognition", "predictive_policing"]


@router.post("/ethics/surveillance-scan")
async def scan_for_surveillance_risks(payload: dict):
    """Scan AI system description for surveillance and ethics risks."""
    scan_id = f"ETH-{str(uuid.uuid4())[:8].upper()}"
    text = payload.get("description", payload.get("text", "")).lower()
    system_name = payload.get("system_name", "unnamed-system")

    findings = []
    eu_ai_act_prohibited = False

    for risk_type, patterns in SURVEILLANCE_PATTERNS.items():
        matched = [p for p in patterns if p in text]
        if matched:
            prohibited = risk_type in EU_AI_ACT_PROHIBITED
            if prohibited:
                eu_ai_act_prohibited = True
            findings.append({
                "risk_type": risk_type.replace("_", " ").title(),
                "matched_patterns": matched,
                "severity": "critical" if prohibited else "high",
                "eu_ai_act_prohibited": prohibited,
                "applicable_regulations": GDPR_ARTICLES.get(risk_type, []),
                "remediation": f"{'EU AI Act Art. 5 PROHIBITS this use case. System cannot be deployed in EU.' if prohibited else 'Implement explicit consent, data minimisation, and DPIA before deployment.'}",
            })

    overall_risk = "PROHIBITED" if eu_ai_act_prohibited else ("HIGH" if findings else "LOW")

    return {
        "scan_id": scan_id,
        "system_name": system_name,
        "overall_risk": overall_risk,
        "eu_ai_act_prohibited": eu_ai_act_prohibited,
        "findings_count": len(findings),
        "findings": findings,
        "compliance_verdict": "NON_COMPLIANT" if findings else "COMPLIANT",
        "requires_dpia": len(findings) > 0,
        "requires_human_oversight": len(findings) > 0,
        "scanned_at": datetime.utcnow().isoformat(),
    }


@router.get("/ethics/prohibited-use-cases")
async def get_prohibited_use_cases():
    return {
        "source": "EU AI Act Article 5",
        "effective_date": "2024-08-01",
        "prohibited": [
            {"category": "Biometric Categorisation", "description": "Using biometrics to infer race, political opinions, religious beliefs, sexual orientation", "penalty": "€30M or 6% global turnover"},
            {"category": "Social Scoring", "description": "AI systems scoring people based on social behaviour by public authorities", "penalty": "€30M or 6% global turnover"},
            {"category": "Real-time Remote Biometric ID", "description": "Real-time remote biometric identification in public spaces for law enforcement", "penalty": "€30M or 6% global turnover"},
            {"category": "Emotion Recognition", "description": "AI inferring emotions of natural persons in workplace or education", "penalty": "€30M or 6% global turnover"},
            {"category": "Manipulation", "description": "AI using subliminal techniques or exploiting vulnerabilities to distort behaviour", "penalty": "€30M or 6% global turnover"},
            {"category": "Predictive Policing", "description": "Risk assessments for criminal offences based solely on profiling", "penalty": "€30M or 6% global turnover"},
        ],
    }


@router.post("/ethics/dpia-generate")
async def generate_dpia(payload: dict):
    """Generate a Data Protection Impact Assessment."""
    return {
        "dpia_id": f"DPIA-{str(uuid.uuid4())[:8].upper()}",
        "system_name": payload.get("system_name", "unnamed"),
        "sections": [
            {"title": "1. Description of Processing", "status": "complete", "notes": "Automated based on system description"},
            {"title": "2. Necessity & Proportionality", "status": "complete", "notes": "Assessment against GDPR Art. 5 principles"},
            {"title": "3. Risk to Rights & Freedoms", "status": "complete", "notes": "Identified risks to data subjects"},
            {"title": "4. Measures to Address Risk", "status": "complete", "notes": "Technical and organisational measures"},
            {"title": "5. DPO Consultation", "status": "required", "notes": "Must be reviewed by Data Protection Officer"},
            {"title": "6. Supervisory Authority Consultation", "status": "conditional", "notes": "Required if residual risk remains high"},
        ],
        "risk_level": payload.get("risk_level", "high"),
        "dpa_consultation_required": True,
        "generated_at": datetime.utcnow().isoformat(),
    }
