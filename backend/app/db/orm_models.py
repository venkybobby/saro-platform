"""
SARO v8.0 — Eight SQLAlchemy ORM models.

Tables
------
tenants          Multi-tenant root; subscription tier governs feature flags.
users            Per-tenant user accounts with hashed passwords.
models           AI/ML model registry (name, version, metadata).
regulations      Regulatory documents (EU AI Act, NIST RMF, etc.).
risk_forecasts   Bayesian probability forecasts per model + regulation.
audit_results    Compliance audit runs, findings JSON, score.
workflows        Tenant-defined automation workflows (JSON DSL).
audit_log        Immutable change log — every write action recorded here.
audits           v9.2 full pipeline audit records (NIST, bias, PII, remediation).
"""
import uuid
from datetime import datetime
from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey,
    Integer, JSON, String, Text, UniqueConstraint,
)
from sqlalchemy.orm import relationship
from app.db.base import Base, TimestampMixin


def _uuid() -> str:
    return str(uuid.uuid4())


# ── 1. Tenants ────────────────────────────────────────────────────────────────
class Tenant(Base, TimestampMixin):
    __tablename__ = "tenants"

    id                = Column(String(36), primary_key=True, default=_uuid)
    name              = Column(String(255), nullable=False, unique=True)
    subscription_tier = Column(String(32),  nullable=False, default="trial")  # trial|pro|enterprise
    is_active         = Column(Boolean, nullable=False, default=True)
    metadata_json     = Column(JSON, nullable=True)
    # v9.1 two-role model: admin sets config; operator inherits
    config            = Column(JSON, nullable=True, default=lambda: {
        "risk_thresholds": {"bias_disparity": 0.15, "pii_leak": 0},
        "lenses": ["EU AI Act", "NIST AI RMF", "ISO 42001", "AIGP"],
        "ethics_enabled": True,
        "report_format": "pdf",
        "metrics_to_show": ["all"],
    })

    users      = relationship("User",         back_populates="tenant", cascade="all, delete-orphan")
    models     = relationship("AIModel",      back_populates="tenant", cascade="all, delete-orphan")
    workflows  = relationship("Workflow",     back_populates="tenant", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog",     back_populates="tenant")


# ── 2. Users ──────────────────────────────────────────────────────────────────
class User(Base, TimestampMixin):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("tenant_id", "email"),)

    id              = Column(String(36), primary_key=True, default=_uuid)
    tenant_id       = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    email           = Column(String(255), nullable=False)
    role            = Column(String(32),  nullable=False, default="viewer")  # admin|auditor|viewer
    hashed_password = Column(String(255), nullable=True)   # null = magic-link only
    last_login      = Column(DateTime, nullable=True)
    is_active       = Column(Boolean, nullable=False, default=True)

    tenant      = relationship("Tenant", back_populates="users")
    audit_logs  = relationship("AuditLog", back_populates="user")


# ── 3. AI Model Registry ──────────────────────────────────────────────────────
class AIModel(Base, TimestampMixin):
    __tablename__ = "models"

    id            = Column(String(36), primary_key=True, default=_uuid)
    tenant_id     = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    name          = Column(String(255), nullable=False)
    model_type    = Column(String(64),  nullable=False)   # classifier|regressor|llm|…
    version       = Column(String(32),  nullable=False, default="1.0.0")
    description   = Column(Text, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    is_active     = Column(Boolean, nullable=False, default=True)

    tenant         = relationship("Tenant",       back_populates="models")
    risk_forecasts = relationship("RiskForecast", back_populates="model", cascade="all, delete-orphan")
    audit_results  = relationship("AuditResult",  back_populates="model", cascade="all, delete-orphan")


# ── 4. Regulations ────────────────────────────────────────────────────────────
class Regulation(Base, TimestampMixin):
    __tablename__ = "regulations"

    id             = Column(String(36), primary_key=True, default=_uuid)
    name           = Column(String(255), nullable=False, unique=True)
    jurisdiction   = Column(String(64),  nullable=False)   # EU|US|UK|APAC
    effective_date = Column(DateTime, nullable=True)
    content        = Column(Text, nullable=True)
    last_updated   = Column(DateTime, default=datetime.utcnow)

    risk_forecasts = relationship("RiskForecast", back_populates="regulation")


# ── 5. Risk Forecasts ─────────────────────────────────────────────────────────
class RiskForecast(Base, TimestampMixin):
    __tablename__ = "risk_forecasts"

    id                  = Column(String(36), primary_key=True, default=_uuid)
    model_id            = Column(String(36), ForeignKey("models.id",      ondelete="CASCADE"), nullable=False)
    regulation_id       = Column(String(36), ForeignKey("regulations.id", ondelete="SET NULL"), nullable=True)
    probability         = Column(Float, nullable=False)
    confidence_interval = Column(JSON, nullable=True)   # {"lower": 0.1, "upper": 0.9}
    horizon_days        = Column(Integer, nullable=False, default=90)
    forecast_metadata   = Column(JSON, nullable=True)

    model      = relationship("AIModel",    back_populates="risk_forecasts")
    regulation = relationship("Regulation", back_populates="risk_forecasts")


# ── 6. Audit Results ──────────────────────────────────────────────────────────
class AuditResult(Base, TimestampMixin):
    __tablename__ = "audit_results"

    id               = Column(String(36), primary_key=True, default=_uuid)
    model_id         = Column(String(36), ForeignKey("models.id", ondelete="CASCADE"), nullable=False)
    audit_type       = Column(String(64),  nullable=False)   # bias|transparency|safety|…
    score            = Column(Float, nullable=False)
    risk_level       = Column(String(16),  nullable=False, default="medium")
    compliance_status= Column(String(32),  nullable=False, default="review")
    findings_json    = Column(JSON, nullable=True)
    regulations_json = Column(JSON, nullable=True)
    audited_at       = Column(DateTime, default=datetime.utcnow)

    model = relationship("AIModel", back_populates="audit_results")


# ── 7. Workflows ──────────────────────────────────────────────────────────────
class Workflow(Base, TimestampMixin):
    __tablename__ = "workflows"

    id              = Column(String(36), primary_key=True, default=_uuid)
    tenant_id       = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    name            = Column(String(255), nullable=False)
    definition_json = Column(JSON, nullable=False)   # step DAG
    status          = Column(String(32),  nullable=False, default="draft")  # draft|active|paused|archived
    last_run_at     = Column(DateTime, nullable=True)

    tenant = relationship("Tenant", back_populates="workflows")


# ── 8. Audit Log ──────────────────────────────────────────────────────────────
class AuditLog(Base):  # noqa: keep before new models
    """Immutable audit trail — no updates, inserts only."""
    __tablename__ = "audit_log"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id   = Column(String(36), ForeignKey("tenants.id", ondelete="SET NULL"), nullable=True)
    user_id     = Column(String(36), ForeignKey("users.id",   ondelete="SET NULL"), nullable=True)
    action      = Column(String(128), nullable=False)   # CREATE_MODEL, RUN_AUDIT, …
    resource    = Column(String(64),  nullable=True)    # models, audits, …
    resource_id = Column(String(36),  nullable=True)
    detail_json = Column(JSON, nullable=True)
    ip_address  = Column(String(45),  nullable=True)
    created_at  = Column(DateTime, default=datetime.utcnow, nullable=False)

    tenant = relationship("Tenant", back_populates="audit_logs")
    user   = relationship("User",   back_populates="audit_logs")


# ── 9. Audits (v9.2 — full pipeline audit records) ───────────────────────────
class Audit(Base, TimestampMixin):
    """
    Stores every full audit pipeline run (from /audit-engine/run).
    Supports before/after comparison via previous_audit_id + fixed_delta.

    status lifecycle: open → partially_fixed → fully_fixed
    fixed_delta: {metric: {before, after, improved/fixed}} — computed on re-run.
    evidence_hash: Merkle root for regulatory immutability (EU AI Act Art.61).
    """
    __tablename__ = "audits"

    id                = Column(String(36), primary_key=True, default=_uuid)
    tenant_id         = Column(String(36), ForeignKey("tenants.id", ondelete="SET NULL"), nullable=True)
    user_id           = Column(String(36), nullable=True)
    mode              = Column(String(16),  nullable=False, default="reactive")  # proactive|reactive
    model_name        = Column(String(255), nullable=False, default="unnamed")
    domain            = Column(String(64),  nullable=True)
    lenses            = Column(JSON, nullable=True)            # ["EU AI Act", ...]
    compliance_score  = Column(Float, nullable=True)           # 0.0 – 1.0
    risk_level        = Column(String(16),  nullable=True)     # low|medium|high|critical
    metrics           = Column(JSON, nullable=True)            # 6 KPI metrics block
    checklist         = Column(JSON, nullable=True)            # NIST 58-control checklist
    compliance_checklist = Column(JSON, nullable=True)         # per-lens compliance items
    remediation_plan  = Column(JSON, nullable=True)            # priority actions
    bias_summary      = Column(JSON, nullable=True)            # bias/fairness result
    pii_summary       = Column(JSON, nullable=True)            # PII/PHI detection result
    evidence_hash     = Column(String(128), nullable=True)     # Merkle root (placeholder)
    status            = Column(String(32),  nullable=False, default="open")  # open|partially_fixed|fully_fixed
    previous_audit_id = Column(String(36), ForeignKey("audits.id", ondelete="SET NULL"), nullable=True)
    fixed_delta       = Column(JSON, nullable=True)            # {metric: {before, after, improved}}
    report_json       = Column(JSON, nullable=True)            # full report blob for retrieval
    # ── v9.2 MIT AI Risk Repository columns ──────────────────────────────────
    mit_domain_tags   = Column(JSON,  nullable=True)           # ["Discrimination & Toxicity", ...]
    mit_coverage_score = Column(Float, nullable=True)          # 0.0 – 100.0
    fixed_delta_mit   = Column(JSON,  nullable=True)           # {before_score, after_score, new_domains, improved}
    # ── v9.3 Audit Tracing columns ────────────────────────────────────────────
    rules_version          = Column(String(16),  nullable=True, default="1.0")  # rules engine semver
    evidence_package_url   = Column(Text, nullable=True)         # S3 URL or inline JSON path
    batch_sample_count     = Column(Integer, nullable=True)      # number of batch records processed
    retention_until        = Column(DateTime, nullable=True)     # 7-year retention date

    tenant   = relationship("Tenant", foreign_keys=[tenant_id])
    previous = relationship("Audit",  foreign_keys=[previous_audit_id], remote_side=[id])


# ── 10. Onboarding Sessions ───────────────────────────────────────────────────
class OnboardingSession(Base, TimestampMixin):
    """Persistent onboarding record — synced async from Redis cache (Story 1)."""
    __tablename__ = "onboarding_sessions"

    id              = Column(String(36), primary_key=True, default=_uuid)
    tenant_id       = Column(String(36), nullable=False, index=True)
    email           = Column(String(255), nullable=False)
    company_name    = Column(String(255), nullable=True)
    sector          = Column(String(64),  nullable=True)   # finance|health|tech|…
    plan            = Column(String(32),  nullable=False, default="trial")
    persona         = Column(String(32),  nullable=False, default="enabler")
    roles_json      = Column(JSON, nullable=True)          # ["admin","forecaster"]
    stripe_sub_id   = Column(String(128), nullable=True)
    trial_ends_at   = Column(DateTime, nullable=True)
    synced_from_cache = Column(Boolean, nullable=False, default=False)
    metadata_json   = Column(JSON, nullable=True)


# ── 10. Transactions ──────────────────────────────────────────────────────────
class Transaction(Base, TimestampMixin):
    """Billing/subscription transactions for audit trail (Story 3). Auto-purge 6 mo."""
    __tablename__ = "transactions"

    id              = Column(String(36), primary_key=True, default=_uuid)
    tenant_id       = Column(String(36), nullable=False, index=True)
    stripe_charge_id= Column(String(128), nullable=True)
    amount_cents    = Column(Integer, nullable=False, default=0)
    currency        = Column(String(8),  nullable=False, default="usd")
    status          = Column(String(32), nullable=False, default="pending")  # pending|succeeded|failed|refunded
    plan            = Column(String(64), nullable=True)
    description     = Column(Text, nullable=True)
    period_start    = Column(DateTime, nullable=True)
    period_end      = Column(DateTime, nullable=True)
    purge_after     = Column(DateTime, nullable=True)   # GDPR: auto-purge after 6 months
    metadata_json   = Column(JSON, nullable=True)


# ── 11. MIT AI Risk Repository (persistent risk catalogue) ───────────────────
class MITRisk(Base, TimestampMixin):
    """
    Persistent storage for the MIT AI Risk Repository (1,612+ risks).
    Populated once by import_mit_risks.py; queried by audit_engine per audit run.

    ev_id / paper_id — original MIT identifiers.
    domain / sub_domain — 7-domain MIT taxonomy.
    causal_entity / causal_intent / causal_timing — MIT Causal Taxonomy.
    """
    __tablename__ = "mit_risks"

    id               = Column(Integer,     primary_key=True, autoincrement=True)
    ev_id            = Column(String(32),  nullable=True,  index=True)
    paper_id         = Column(String(64),  nullable=True)
    category_level   = Column(String(64),  nullable=True)
    risk_category    = Column(String(255), nullable=True)
    risk_subcategory = Column(String(255), nullable=True)
    description      = Column(Text,        nullable=True)
    additional_ev    = Column(Text,        nullable=True)
    causal_entity    = Column(String(64),  nullable=True)
    causal_intent    = Column(String(64),  nullable=True)
    causal_timing    = Column(String(64),  nullable=True)
    domain           = Column(String(128), nullable=True,  index=True)
    sub_domain       = Column(String(255), nullable=True)


# ── 12. User Roles (multi-role, max 4) ───────────────────────────────────────
class UserRole(Base, TimestampMixin):
    """Multi-role assignments per user (Story 5). AI auto-suggests based on actions."""
    __tablename__ = "user_roles"
    __table_args__ = (UniqueConstraint("user_id", "role"),)

    id              = Column(String(36), primary_key=True, default=_uuid)
    user_id         = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    tenant_id       = Column(String(36), nullable=False, index=True)
    role            = Column(String(32), nullable=False)   # admin|forecaster|autopsier|enabler|evangelist
    assigned_by     = Column(String(32), nullable=False, default="ai_auto")  # ai_auto|manual
    confidence      = Column(Float, nullable=True)         # AI confidence score (0-1)
    trigger_action  = Column(String(128), nullable=True)   # action that triggered AI suggestion
    is_primary      = Column(Boolean, nullable=False, default=False)
    is_active       = Column(Boolean, nullable=False, default=True)


# ── 13. EU AI Act Rules ───────────────────────────────────────────────────────
class EUAIActRule(Base, TimestampMixin):
    """Persistent EU AI Act article registry. Seeded by seed_rules_db.py."""
    __tablename__ = "eu_ai_act_rules"

    id             = Column(Integer,     primary_key=True, autoincrement=True)
    article_number = Column(String(16),  nullable=False, index=True)
    title          = Column(String(255), nullable=False)
    risk_level     = Column(String(32),  nullable=True)   # unacceptable|high|limited|minimal
    description    = Column(Text,        nullable=True)
    obligation     = Column(Text,        nullable=True)
    applies_to     = Column(String(128), nullable=True)


# ── 14. NIST AI RMF Controls ─────────────────────────────────────────────────
class NISTControl(Base, TimestampMixin):
    """All 58 NIST AI RMF 1.0 controls. Seeded by seed_rules_db.py."""
    __tablename__ = "nist_ai_rmf_controls"

    id          = Column(Integer,    primary_key=True, autoincrement=True)
    control_id  = Column(String(32), nullable=False, unique=True, index=True)
    function    = Column(String(32), nullable=False, index=True)
    category    = Column(String(64), nullable=True)
    description = Column(Text,       nullable=True)


# ── 15. AIGP Principles ──────────────────────────────────────────────────────
class AIGPPrinciple(Base, TimestampMixin):
    """IAPP AIGP governance principles. Seeded by seed_rules_db.py."""
    __tablename__ = "aigp_principles"

    id          = Column(Integer,     primary_key=True, autoincrement=True)
    domain      = Column(String(128), nullable=False, index=True)
    subtopic    = Column(String(255), nullable=True)
    description = Column(Text,        nullable=True)
    item_id     = Column(String(32),  nullable=True)


# ── 16. AI Incidents ─────────────────────────────────────────────────────────
class AIIncident(Base, TimestampMixin):
    """Curated AI incident registry used for similar-incident matching per audit."""
    __tablename__ = "ai_incidents"

    id          = Column(Integer,     primary_key=True, autoincrement=True)
    title       = Column(String(512), nullable=False)
    date        = Column(String(16),  nullable=True)
    harm_type   = Column(String(128), nullable=True, index=True)  # MIT domain
    description = Column(Text,        nullable=True)
    severity    = Column(String(16),  nullable=True)
    source      = Column(String(255), nullable=True)
    ai_system   = Column(String(255), nullable=True)
    region      = Column(String(64),  nullable=True)


# ── 17. Audit Transactions (usage metering) ───────────────────────────────────
class AuditTransaction(Base, TimestampMixin):
    """
    Usage-metering table. One row per scan (/api/v1/scan or UI Run Full Audit).
    Used for Stripe subscription billing at month-end.

    Billing model:
      Free tier    — 50 scans/month  · $0
      Pro tier     — 500 scans/month · $99/month base + $0.05/extra scan
      Enterprise   — unlimited       · custom pricing
    """
    __tablename__ = "audit_transactions"

    id              = Column(String(36),  primary_key=True, default=_uuid)
    tenant_id       = Column(String(36),  nullable=True,  index=True)
    audit_id        = Column(String(64),  nullable=True,  index=True)   # FK to audits.id (soft)
    model_name      = Column(String(255), nullable=True)
    domain          = Column(String(64),  nullable=True)
    tier            = Column(String(32),  nullable=True, default="free")  # free|pro|enterprise
    cost_cents      = Column(Integer,     nullable=False, default=0)       # 0 for free/included; 5 = $0.05
    is_included     = Column(Boolean,     nullable=False, default=True)    # within plan quota
    scan_source     = Column(String(32),  nullable=True, default="ui")    # ui|api
    billing_period  = Column(String(16),  nullable=True)                  # YYYY-MM


# ── 18. Pricing Config ────────────────────────────────────────────────────────
class PricingConfig(Base, TimestampMixin):
    """
    Per-tier pricing configuration. Managed by Super Admin via Setup Hub.
    Changes take effect immediately (no redeploy needed).
    """
    __tablename__ = "pricing_config"

    id                  = Column(Integer,     primary_key=True, autoincrement=True)
    tier                = Column(String(32),  nullable=False, unique=True, index=True)  # free|pro|enterprise
    monthly_base_cents  = Column(Integer,     nullable=False, default=0)       # base fee in cents
    included_scans      = Column(Integer,     nullable=False, default=50)      # scans within base fee
    per_extra_scan_cents= Column(Integer,     nullable=False, default=5)       # $0.05 = 5 cents
    annual_discount_pct = Column(Integer,     nullable=False, default=20)      # 20% annual discount
    is_active           = Column(Boolean,     nullable=False, default=True)
    description         = Column(Text,        nullable=True)

