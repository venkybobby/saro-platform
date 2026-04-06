"""
SQLAlchemy ORM models for the SARO platform.

Existing tables (populated by import_*.py scripts):
  mit_risks, eu_ai_act_rules, nist_ai_rmf_controls,
  aigp_principles, governance_rules, ai_incidents

New tables added here:
  tenants, users, audits, scan_reports, audit_traces, demo_requests
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


# ─────────────────────────────────────────────────────────────────────────────
# Tenant & User (RBAC: Super Admin + Operator)
# ─────────────────────────────────────────────────────────────────────────────


class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    settings_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    users: Mapped[list[User]] = relationship(back_populates="tenant")
    audits: Mapped[list[Audit]] = relationship(back_populates="tenant")


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE")
    )
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    # Roles: "super_admin" | "operator"
    role: Mapped[str] = mapped_column(String(50), nullable=False, default="operator")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    tenant: Mapped[Tenant] = relationship(back_populates="users")
    audits: Mapped[list[Audit]] = relationship(back_populates="user")


# ─────────────────────────────────────────────────────────────────────────────
# Audits & Reports
# ─────────────────────────────────────────────────────────────────────────────


class Audit(Base):
    __tablename__ = "audits"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    batch_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    dataset_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sample_count: Mapped[int] = mapped_column(Integer, nullable=False)
    # status: "pending" | "running" | "completed" | "failed"
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    tenant: Mapped[Tenant] = relationship(back_populates="audits")
    user: Mapped[User | None] = relationship(back_populates="audits")
    report: Mapped[ScanReport | None] = relationship(
        back_populates="audit", uselist=False
    )
    traces: Mapped[list["AuditTrace"]] = relationship(
        back_populates="audit", cascade="all, delete-orphan"
    )


class ScanReport(Base):
    """Persisted full audit report (JSON blob + key scalar metrics)."""

    __tablename__ = "scan_reports"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    audit_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("audits.id", ondelete="CASCADE"),
        unique=True,
    )
    # Top-level scalar metrics (indexed for dashboarding)
    mit_coverage_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    fixed_delta: Mapped[float | None] = mapped_column(Float, nullable=True)
    overall_risk_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    # Full structured report stored as JSON
    report_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    audit: Mapped[Audit] = relationship(back_populates="report")


class AuditTrace(Base):
    """
    Granular trace record for each check performed during an audit.

    One row per gate result, domain risk signal, or compliance rule trigger.
    Drives the Remedy screen: failed/warn traces are surfaced for operator review.
    """
    __tablename__ = "audit_traces"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    audit_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("audits.id", ondelete="CASCADE"), nullable=False
    )
    gate_id: Mapped[int] = mapped_column(Integer, nullable=False)
    gate_name: Mapped[str] = mapped_column(String(100), nullable=False)
    # check_type: "gate_result" | "risk_domain" | "compliance_rule"
    check_type: Mapped[str] = mapped_column(String(50), nullable=False)
    check_name: Mapped[str] = mapped_column(String(500), nullable=False)
    # result: "pass" | "fail" | "warn" | "flagged" | "triggered"
    result: Mapped[str] = mapped_column(String(20), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    detail_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    remediation_hint: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Remedy workflow fields
    is_remediated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    remediated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    remediated_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    audit: Mapped["Audit"] = relationship(back_populates="traces")


# ─────────────────────────────────────────────────────────────────────────────
# Reference tables (read-only, populated by import_*.py scripts)
# ─────────────────────────────────────────────────────────────────────────────


class MITRisk(Base):
    __tablename__ = "mit_risks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ev_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    paper_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    category_level: Mapped[str | None] = mapped_column(String(50), nullable=True)
    risk_category: Mapped[str | None] = mapped_column(String(255), nullable=True)
    risk_subcategory: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    additional_ev: Mapped[str | None] = mapped_column(Text, nullable=True)
    causal_entity: Mapped[str | None] = mapped_column(String(255), nullable=True)
    causal_intent: Mapped[str | None] = mapped_column(String(100), nullable=True)
    causal_timing: Mapped[str | None] = mapped_column(String(100), nullable=True)
    domain: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sub_domain: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class EUAIActRule(Base):
    __tablename__ = "eu_ai_act_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    article_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    risk_level: Mapped[str | None] = mapped_column(String(100), nullable=True)
    obligations_providers: Mapped[str | None] = mapped_column(Text, nullable=True)
    obligations_users: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    annex_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    last_updated: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class NISTControl(Base):
    __tablename__ = "nist_ai_rmf_controls"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    function_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    subcategory_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    key_actions: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_updated: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class AIGPPrinciple(Base):
    __tablename__ = "aigp_principles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    domain: Mapped[str | None] = mapped_column(String(255), nullable=True)
    subtopic: Mapped[str | None] = mapped_column(String(500), nullable=True)
    key_principles: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_updated: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class GovernanceRule(Base):
    __tablename__ = "governance_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    framework_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    rule_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    category: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    obligations: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_updated: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class AIIncident(Base):
    __tablename__ = "ai_incidents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    incident_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    date: Mapped[str | None] = mapped_column(String(50), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str | None] = mapped_column(String(255), nullable=True)
    harm_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    affected_sector: Mapped[str | None] = mapped_column(String(255), nullable=True)
    url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Whether the incident was remediated/resolved
    is_fixed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class DemoRequest(Base):
    """
    Prospective customer demo/trial signup request.
    Submitted from the public login page — no authentication required.
    """
    __tablename__ = "demo_requests"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    contact_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    company_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    # status: "pending" | "contacted" | "rejected" | "converted"
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
