"""SARO Platform v8.0 — Core Data Models
Updated to match all spec requirements (FR-001 through FR-018)
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class RiskLevel(str, Enum):
    LOW      = "low"
    MEDIUM   = "medium"
    HIGH     = "high"
    CRITICAL = "critical"


class ComplianceStatus(str, Enum):
    COMPLIANT     = "compliant"
    NON_COMPLIANT = "non_compliant"
    PENDING       = "pending"
    REVIEW        = "review"


# ── FR-001: Regulatory Document Ingestion ────────────────────────────
class DocumentIn(BaseModel):
    title: str
    content: str
    source: Optional[str] = None
    doc_type: Optional[str] = "regulation"
    jurisdiction: Optional[str] = "EU"
    tags: Optional[List[str]] = []

    model_config = {"protected_namespaces": ()}


class DocumentOut(BaseModel):
    id: str
    title: str
    content_hash: str = ""
    jurisdiction: str = "EU"
    doc_type: str = "regulation"
    entities_found: List[str] = []
    risk_tags: List[Dict[str, Any]] = []
    risk_score: float = 0.0
    risk_level: RiskLevel = RiskLevel.LOW
    # FR-003: Bayesian forecasting fields
    gap_probability_90d: float = 0.0
    gap_probability_ci: List[float] = [0.0, 0.0]
    processed_at: str = ""
    remediation_urgency: str = "monitor"
    standards_triggered: List[str] = []

    model_config = {"protected_namespaces": ()}


# ── FR-004: Reactive Audit ────────────────────────────────────────────
class AuditRequest(BaseModel):
    model_name: str
    model_version: str = "1.0"
    use_case: str
    jurisdiction: str = "EU"
    risk_category: RiskLevel = RiskLevel.MEDIUM
    training_data_description: Optional[str] = None
    deployment_context: Optional[str] = None

    model_config = {"protected_namespaces": ()}


class AuditResult(BaseModel):
    audit_id: str
    model_name: str
    use_case: str = ""
    jurisdiction: str = "EU"
    regulations_checked: List[str] = []
    compliance_score: float
    status: ComplianceStatus
    risk_level: RiskLevel
    findings: List[Dict[str, Any]] = []
    recommendations: List[str] = []
    next_audit_date: str = ""
    audit_date: str = ""

    model_config = {"protected_namespaces": ()}


# ── FR-007: AI Guardrails ─────────────────────────────────────────────
class GuardrailCheck(BaseModel):
    request_id: str
    model_id: str
    input_text: Optional[str] = None
    output_text: Optional[str] = None
    context: Optional[Dict[str, Any]] = {}

    model_config = {"protected_namespaces": ()}


class GuardrailResult(BaseModel):
    request_id: str
    passed: bool
    blocked: bool
    violations: List[Dict[str, Any]] = []
    risk_score: float
    latency_ms: float
    timestamp: datetime

    model_config = {"protected_namespaces": ()}


# ── FR-011: Multi-Tenant ──────────────────────────────────────────────
class TenantCreate(BaseModel):
    name: str
    plan: str = "professional"
    industry: str
    contact_email: str
    jurisdictions: List[str] = ["EU", "US"]


class TenantOut(BaseModel):
    tenant_id: str
    name: str
    plan: str
    api_key: str
    status: str
    created_at: datetime
    monthly_usage: Dict[str, int] = {}


# ── Alerts & Dashboard ────────────────────────────────────────────────
class RegulatoryAlert(BaseModel):
    alert_id: str
    regulation: str
    jurisdiction: str
    severity: RiskLevel
    title: str
    description: str
    affected_systems: List[str]
    deadline: Optional[datetime]
    created_at: datetime


class DashboardMetrics(BaseModel):
    total_documents: int
    total_audits: int
    active_tenants: int
    guardrail_blocks_today: int
    compliance_score_avg: float
    risk_distribution: Dict[str, int]
    recent_alerts: List[RegulatoryAlert]
    mvp_status: Dict[str, str]
    system_health: Dict[str, str]
