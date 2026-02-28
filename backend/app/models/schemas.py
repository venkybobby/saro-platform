"""SARO Platform - Core Data Models"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ComplianceStatus(str, Enum):
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PENDING = "pending"
    REVIEW = "review"


class DocumentIn(BaseModel):
    title: str
    content: str
    source: Optional[str] = None
    doc_type: Optional[str] = "regulation"
    jurisdiction: Optional[str] = "EU"
    tags: Optional[List[str]] = []


class DocumentOut(BaseModel):
    id: str
    title: str
    content_summary: str
    entities: List[str] = []
    risk_tags: List[Dict[str, Any]] = []
    jurisdiction: str
    ingested_at: datetime
    risk_score: float


class AuditRequest(BaseModel):
    model_name: str
    model_version: str
    use_case: str
    jurisdiction: str = "EU"
    risk_category: RiskLevel = RiskLevel.MEDIUM
    training_data_description: Optional[str] = None
    deployment_context: Optional[str] = None


class AuditResult(BaseModel):
    audit_id: str
    model_name: str
    overall_risk: RiskLevel
    compliance_score: float
    findings: List[Dict[str, Any]]
    recommendations: List[str]
    applicable_regulations: List[str]
    status: ComplianceStatus
    generated_at: datetime
    next_review_date: datetime


class GuardrailCheck(BaseModel):
    request_id: str
    model_id: str
    input_text: Optional[str] = None
    output_text: Optional[str] = None
    context: Optional[Dict[str, Any]] = {}


class GuardrailResult(BaseModel):
    request_id: str
    passed: bool
    blocked: bool
    violations: List[Dict[str, Any]] = []
    risk_score: float
    latency_ms: float
    timestamp: datetime


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
