"""
SARO Persona-Level RBAC — Core Persona Definitions & Permission Matrix
=======================================================================
FR-005: Role-based UI limits (e.g., Forecaster: Forecast only).
Admin assigns personas; enforced in session via middleware.

Personas:
  - Forecaster : Risk forecasting dashboards, scenario modeling
  - Enabler    : Onboarding, training, integration management
  - Evangelist : Ethics reports, compliance evangelism, public docs
  - Auditor    : Full audit trails, compliance verification, evidence export

Each persona maps to:
  1. Allowed views (UI routes)
  2. Allowed API scopes (endpoint groups)
  3. Allowed report types
  4. Data sensitivity ceiling (what PII level they can access)
"""

from enum import Enum
from typing import FrozenSet, Dict, Any


# ---------------------------------------------------------------------------
# Persona Enum
# ---------------------------------------------------------------------------
class Persona(str, Enum):
    FORECASTER = "forecaster"
    ENABLER = "enabler"
    EVANGELIST = "evangelist"
    AUDITOR = "auditor"


# ---------------------------------------------------------------------------
# API Scope Enum — granular permission units
# ---------------------------------------------------------------------------
class APIScope(str, Enum):
    # Forecast domain
    FORECAST_READ = "forecast:read"
    FORECAST_CREATE = "forecast:create"
    FORECAST_SCENARIO = "forecast:scenario"

    # Risk domain
    RISK_DASHBOARD = "risk:dashboard"
    RISK_ALERTS = "risk:alerts"

    # Onboarding / enablement domain
    ONBOARD_MANAGE = "onboard:manage"
    ONBOARD_TRAINING = "onboard:training"
    ONBOARD_INTEGRATIONS = "onboard:integrations"

    # Ethics / evangelism domain
    ETHICS_REPORTS = "ethics:reports"
    ETHICS_PUBLIC = "ethics:public"
    ETHICS_BIAS_REVIEW = "ethics:bias_review"

    # Audit domain
    AUDIT_TRAIL = "audit:trail"
    AUDIT_EVIDENCE = "audit:evidence"
    AUDIT_EXPORT = "audit:export"
    AUDIT_COMPLIANCE = "audit:compliance"

    # Shared / cross-cutting
    PROFILE_SELF = "profile:self"
    NOTIFICATIONS = "notifications:read"

    # Admin (super-user only, not a persona)
    ADMIN_PROVISION = "admin:provision"
    ADMIN_TENANT = "admin:tenant"
    ADMIN_BILLING = "admin:billing"


# ---------------------------------------------------------------------------
# Data Sensitivity Levels
# ---------------------------------------------------------------------------
class DataSensitivity(int, Enum):
    PUBLIC = 0          # Aggregated, anonymized
    INTERNAL = 1        # Org-level, no PII
    CONFIDENTIAL = 2    # May contain PII references
    RESTRICTED = 3      # Raw PII, audit evidence


# ---------------------------------------------------------------------------
# View Route Groups — maps to frontend route prefixes
# ---------------------------------------------------------------------------
class ViewGroup(str, Enum):
    FORECAST_DASHBOARD = "/dashboard/forecast"
    SCENARIO_MODELER = "/dashboard/scenarios"
    RISK_OVERVIEW = "/dashboard/risk"
    ONBOARD_PANEL = "/manage/onboarding"
    TRAINING_HUB = "/manage/training"
    INTEGRATION_MGR = "/manage/integrations"
    ETHICS_DASHBOARD = "/reports/ethics"
    BIAS_REVIEW = "/reports/bias"
    PUBLIC_DOCS = "/reports/public"
    AUDIT_TRAIL = "/audit/trail"
    AUDIT_EVIDENCE = "/audit/evidence"
    AUDIT_EXPORT = "/audit/export"
    COMPLIANCE_CENTER = "/audit/compliance"
    PROFILE = "/settings/profile"
    NOTIFICATIONS = "/notifications"


# ---------------------------------------------------------------------------
# Report Types — persona-limited report access (FR-007)
# ---------------------------------------------------------------------------
class ReportType(str, Enum):
    RISK_FORECAST = "risk_forecast"
    SCENARIO_ANALYSIS = "scenario_analysis"
    ONBOARDING_STATUS = "onboarding_status"
    TRAINING_PROGRESS = "training_progress"
    ETHICS_SUMMARY = "ethics_summary"
    BIAS_AUDIT = "bias_audit"
    PUBLIC_COMPLIANCE = "public_compliance"
    FULL_AUDIT_LOG = "full_audit_log"
    EVIDENCE_PACKAGE = "evidence_package"
    REGULATORY_FILING = "regulatory_filing"


# ---------------------------------------------------------------------------
# PERSONA PERMISSION MATRIX — Single source of truth
# ---------------------------------------------------------------------------
PERSONA_MATRIX: Dict[Persona, Dict[str, Any]] = {
    Persona.FORECASTER: {
        "description": "Risk forecasting specialist — scenario modeling and risk dashboards",
        "scopes": frozenset({
            APIScope.FORECAST_READ,
            APIScope.FORECAST_CREATE,
            APIScope.FORECAST_SCENARIO,
            APIScope.RISK_DASHBOARD,
            APIScope.RISK_ALERTS,
            APIScope.PROFILE_SELF,
            APIScope.NOTIFICATIONS,
        }),
        "views": frozenset({
            ViewGroup.FORECAST_DASHBOARD,
            ViewGroup.SCENARIO_MODELER,
            ViewGroup.RISK_OVERVIEW,
            ViewGroup.PROFILE,
            ViewGroup.NOTIFICATIONS,
        }),
        "reports": frozenset({
            ReportType.RISK_FORECAST,
            ReportType.SCENARIO_ANALYSIS,
        }),
        "data_ceiling": DataSensitivity.INTERNAL,
        "max_export_rows": 10_000,
        "session_timeout_minutes": 30,
    },

    Persona.ENABLER: {
        "description": "Onboarding & enablement lead — training, integrations, client setup",
        "scopes": frozenset({
            APIScope.ONBOARD_MANAGE,
            APIScope.ONBOARD_TRAINING,
            APIScope.ONBOARD_INTEGRATIONS,
            APIScope.RISK_DASHBOARD,  # read-only risk view for context
            APIScope.PROFILE_SELF,
            APIScope.NOTIFICATIONS,
        }),
        "views": frozenset({
            ViewGroup.ONBOARD_PANEL,
            ViewGroup.TRAINING_HUB,
            ViewGroup.INTEGRATION_MGR,
            ViewGroup.RISK_OVERVIEW,
            ViewGroup.PROFILE,
            ViewGroup.NOTIFICATIONS,
        }),
        "reports": frozenset({
            ReportType.ONBOARDING_STATUS,
            ReportType.TRAINING_PROGRESS,
        }),
        "data_ceiling": DataSensitivity.CONFIDENTIAL,
        "max_export_rows": 5_000,
        "session_timeout_minutes": 60,
    },

    Persona.EVANGELIST: {
        "description": "Ethics & compliance evangelist — public reports, bias reviews, comms",
        "scopes": frozenset({
            APIScope.ETHICS_REPORTS,
            APIScope.ETHICS_PUBLIC,
            APIScope.ETHICS_BIAS_REVIEW,
            APIScope.PROFILE_SELF,
            APIScope.NOTIFICATIONS,
        }),
        "views": frozenset({
            ViewGroup.ETHICS_DASHBOARD,
            ViewGroup.BIAS_REVIEW,
            ViewGroup.PUBLIC_DOCS,
            ViewGroup.PROFILE,
            ViewGroup.NOTIFICATIONS,
        }),
        "reports": frozenset({
            ReportType.ETHICS_SUMMARY,
            ReportType.BIAS_AUDIT,
            ReportType.PUBLIC_COMPLIANCE,
        }),
        "data_ceiling": DataSensitivity.PUBLIC,
        "max_export_rows": 50_000,  # public docs can be large
        "session_timeout_minutes": 120,
    },

    Persona.AUDITOR: {
        "description": "Compliance auditor — full trail access, evidence export, regulatory filings",
        "scopes": frozenset({
            APIScope.AUDIT_TRAIL,
            APIScope.AUDIT_EVIDENCE,
            APIScope.AUDIT_EXPORT,
            APIScope.AUDIT_COMPLIANCE,
            APIScope.RISK_DASHBOARD,       # read-only for context
            APIScope.ETHICS_REPORTS,        # read-only for cross-check
            APIScope.FORECAST_READ,         # read-only for verification
            APIScope.PROFILE_SELF,
            APIScope.NOTIFICATIONS,
        }),
        "views": frozenset({
            ViewGroup.AUDIT_TRAIL,
            ViewGroup.AUDIT_EVIDENCE,
            ViewGroup.AUDIT_EXPORT,
            ViewGroup.COMPLIANCE_CENTER,
            ViewGroup.RISK_OVERVIEW,
            ViewGroup.ETHICS_DASHBOARD,
            ViewGroup.FORECAST_DASHBOARD,
            ViewGroup.PROFILE,
            ViewGroup.NOTIFICATIONS,
        }),
        "reports": frozenset({
            ReportType.FULL_AUDIT_LOG,
            ReportType.EVIDENCE_PACKAGE,
            ReportType.REGULATORY_FILING,
            ReportType.RISK_FORECAST,      # read-only
            ReportType.ETHICS_SUMMARY,     # read-only
        }),
        "data_ceiling": DataSensitivity.RESTRICTED,
        "max_export_rows": 500_000,
        "session_timeout_minutes": 15,  # short for security
    },
}


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------
def get_persona_scopes(persona: Persona) -> FrozenSet[APIScope]:
    """Return the set of API scopes for a persona."""
    return PERSONA_MATRIX[persona]["scopes"]


def get_persona_views(persona: Persona) -> FrozenSet[ViewGroup]:
    """Return the set of allowed view routes for a persona."""
    return PERSONA_MATRIX[persona]["views"]


def get_persona_reports(persona: Persona) -> FrozenSet[ReportType]:
    """Return the set of accessible report types for a persona."""
    return PERSONA_MATRIX[persona]["reports"]


def get_merged_scopes(personas: list[Persona]) -> FrozenSet[APIScope]:
    """
    For multi-role users (up to 4 roles per FR-003), merge scopes.
    Union of all persona scopes = effective permission set.
    """
    merged = frozenset()
    for p in personas:
        merged = merged | PERSONA_MATRIX[p]["scopes"]
    return merged


def get_merged_views(personas: list[Persona]) -> FrozenSet[ViewGroup]:
    """Merge view permissions across multiple personas."""
    merged = frozenset()
    for p in personas:
        merged = merged | PERSONA_MATRIX[p]["views"]
    return merged


def get_merged_reports(personas: list[Persona]) -> FrozenSet[ReportType]:
    """Merge report access across multiple personas."""
    merged = frozenset()
    for p in personas:
        merged = merged | PERSONA_MATRIX[p]["reports"]
    return merged


def get_highest_sensitivity(personas: list[Persona]) -> DataSensitivity:
    """For multi-role users, the highest sensitivity ceiling wins."""
    return max(PERSONA_MATRIX[p]["data_ceiling"] for p in personas)


def check_scope(user_scopes: FrozenSet[APIScope], required: APIScope) -> bool:
    """Check if a required scope exists in the user's effective scopes."""
    return required in user_scopes
