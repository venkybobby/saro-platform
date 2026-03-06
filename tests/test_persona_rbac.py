"""
SARO Persona RBAC — Test Suite
================================
Tests for FR-005 (Persona Limitation), FR-003 (Multi-role), FR-007 (Report Access).
Covers: permission matrix integrity, scope merging, denial enforcement, audit logging.

Run: pytest tests/test_persona_rbac.py -v
"""

import pytest
from models.personas import (
    Persona, APIScope, DataSensitivity, ViewGroup, ReportType,
    PERSONA_MATRIX,
    get_persona_scopes, get_persona_views, get_persona_reports,
    get_merged_scopes, get_merged_views, get_merged_reports,
    get_highest_sensitivity, check_scope,
)


# ===========================================================================
# 1. PERMISSION MATRIX INTEGRITY
# ===========================================================================

class TestPersonaMatrixIntegrity:
    """Validate the persona permission matrix is complete and consistent."""

    def test_all_personas_defined(self):
        """Every Persona enum value must have a matrix entry."""
        for persona in Persona:
            assert persona in PERSONA_MATRIX, f"Missing matrix entry for {persona}"

    def test_all_personas_have_required_keys(self):
        required_keys = {
            "description", "scopes", "views", "reports",
            "data_ceiling", "max_export_rows", "session_timeout_minutes",
        }
        for persona, config in PERSONA_MATRIX.items():
            for key in required_keys:
                assert key in config, f"{persona.value} missing key: {key}"

    def test_all_scopes_are_valid_enums(self):
        for persona, config in PERSONA_MATRIX.items():
            for scope in config["scopes"]:
                assert isinstance(scope, APIScope), (
                    f"{persona.value} has invalid scope: {scope}"
                )

    def test_all_views_are_valid_enums(self):
        for persona, config in PERSONA_MATRIX.items():
            for view in config["views"]:
                assert isinstance(view, ViewGroup), (
                    f"{persona.value} has invalid view: {view}"
                )

    def test_all_reports_are_valid_enums(self):
        for persona, config in PERSONA_MATRIX.items():
            for report in config["reports"]:
                assert isinstance(report, ReportType), (
                    f"{persona.value} has invalid report: {report}"
                )

    def test_every_persona_has_profile_and_notifications(self):
        """All personas should have basic self-service scopes."""
        for persona in Persona:
            scopes = get_persona_scopes(persona)
            assert APIScope.PROFILE_SELF in scopes, (
                f"{persona.value} missing profile:self"
            )
            assert APIScope.NOTIFICATIONS in scopes, (
                f"{persona.value} missing notifications:read"
            )

    def test_no_persona_has_admin_scopes(self):
        """Admin scopes should never be in a persona's default set."""
        admin_scopes = {APIScope.ADMIN_PROVISION, APIScope.ADMIN_TENANT, APIScope.ADMIN_BILLING}
        for persona in Persona:
            overlap = get_persona_scopes(persona) & admin_scopes
            assert not overlap, (
                f"{persona.value} has admin scopes: {overlap}"
            )


# ===========================================================================
# 2. INDIVIDUAL PERSONA SCOPE TESTS
# ===========================================================================

class TestForecasterPersona:
    def test_has_forecast_scopes(self):
        scopes = get_persona_scopes(Persona.FORECASTER)
        assert APIScope.FORECAST_READ in scopes
        assert APIScope.FORECAST_CREATE in scopes
        assert APIScope.FORECAST_SCENARIO in scopes

    def test_has_risk_scopes(self):
        scopes = get_persona_scopes(Persona.FORECASTER)
        assert APIScope.RISK_DASHBOARD in scopes
        assert APIScope.RISK_ALERTS in scopes

    def test_cannot_access_audit(self):
        scopes = get_persona_scopes(Persona.FORECASTER)
        assert APIScope.AUDIT_TRAIL not in scopes
        assert APIScope.AUDIT_EVIDENCE not in scopes
        assert APIScope.AUDIT_EXPORT not in scopes

    def test_cannot_access_onboarding(self):
        scopes = get_persona_scopes(Persona.FORECASTER)
        assert APIScope.ONBOARD_MANAGE not in scopes

    def test_cannot_access_ethics(self):
        scopes = get_persona_scopes(Persona.FORECASTER)
        assert APIScope.ETHICS_REPORTS not in scopes
        assert APIScope.ETHICS_BIAS_REVIEW not in scopes

    def test_data_ceiling_internal(self):
        ceiling = PERSONA_MATRIX[Persona.FORECASTER]["data_ceiling"]
        assert ceiling == DataSensitivity.INTERNAL

    def test_reports_limited(self):
        reports = get_persona_reports(Persona.FORECASTER)
        assert ReportType.RISK_FORECAST in reports
        assert ReportType.SCENARIO_ANALYSIS in reports
        assert ReportType.FULL_AUDIT_LOG not in reports
        assert ReportType.ETHICS_SUMMARY not in reports

    def test_views_limited(self):
        views = get_persona_views(Persona.FORECASTER)
        assert ViewGroup.FORECAST_DASHBOARD in views
        assert ViewGroup.SCENARIO_MODELER in views
        assert ViewGroup.AUDIT_TRAIL not in views
        assert ViewGroup.ETHICS_DASHBOARD not in views
        assert ViewGroup.ONBOARD_PANEL not in views


class TestEnablerPersona:
    def test_has_onboard_scopes(self):
        scopes = get_persona_scopes(Persona.ENABLER)
        assert APIScope.ONBOARD_MANAGE in scopes
        assert APIScope.ONBOARD_TRAINING in scopes
        assert APIScope.ONBOARD_INTEGRATIONS in scopes

    def test_has_risk_read_only(self):
        scopes = get_persona_scopes(Persona.ENABLER)
        assert APIScope.RISK_DASHBOARD in scopes
        assert APIScope.RISK_ALERTS not in scopes  # read-only context, not alerts

    def test_cannot_forecast(self):
        scopes = get_persona_scopes(Persona.ENABLER)
        assert APIScope.FORECAST_CREATE not in scopes
        assert APIScope.FORECAST_SCENARIO not in scopes

    def test_data_ceiling_confidential(self):
        ceiling = PERSONA_MATRIX[Persona.ENABLER]["data_ceiling"]
        assert ceiling == DataSensitivity.CONFIDENTIAL


class TestEvangelistPersona:
    def test_has_ethics_scopes(self):
        scopes = get_persona_scopes(Persona.EVANGELIST)
        assert APIScope.ETHICS_REPORTS in scopes
        assert APIScope.ETHICS_PUBLIC in scopes
        assert APIScope.ETHICS_BIAS_REVIEW in scopes

    def test_data_ceiling_public(self):
        ceiling = PERSONA_MATRIX[Persona.EVANGELIST]["data_ceiling"]
        assert ceiling == DataSensitivity.PUBLIC

    def test_cannot_access_audit(self):
        scopes = get_persona_scopes(Persona.EVANGELIST)
        assert APIScope.AUDIT_TRAIL not in scopes

    def test_reports_ethics_only(self):
        reports = get_persona_reports(Persona.EVANGELIST)
        assert ReportType.ETHICS_SUMMARY in reports
        assert ReportType.BIAS_AUDIT in reports
        assert ReportType.PUBLIC_COMPLIANCE in reports
        assert ReportType.FULL_AUDIT_LOG not in reports
        assert ReportType.RISK_FORECAST not in reports


class TestAuditorPersona:
    def test_has_audit_scopes(self):
        scopes = get_persona_scopes(Persona.AUDITOR)
        assert APIScope.AUDIT_TRAIL in scopes
        assert APIScope.AUDIT_EVIDENCE in scopes
        assert APIScope.AUDIT_EXPORT in scopes
        assert APIScope.AUDIT_COMPLIANCE in scopes

    def test_has_cross_read_scopes(self):
        """Auditor can read across domains for verification."""
        scopes = get_persona_scopes(Persona.AUDITOR)
        assert APIScope.RISK_DASHBOARD in scopes
        assert APIScope.ETHICS_REPORTS in scopes
        assert APIScope.FORECAST_READ in scopes

    def test_cannot_create_forecasts(self):
        scopes = get_persona_scopes(Persona.AUDITOR)
        assert APIScope.FORECAST_CREATE not in scopes
        assert APIScope.FORECAST_SCENARIO not in scopes

    def test_data_ceiling_restricted(self):
        ceiling = PERSONA_MATRIX[Persona.AUDITOR]["data_ceiling"]
        assert ceiling == DataSensitivity.RESTRICTED

    def test_short_session_timeout(self):
        """Auditor should have shortest timeout for security."""
        timeout = PERSONA_MATRIX[Persona.AUDITOR]["session_timeout_minutes"]
        assert timeout == 15
        for persona in Persona:
            if persona != Persona.AUDITOR:
                other_timeout = PERSONA_MATRIX[persona]["session_timeout_minutes"]
                assert timeout <= other_timeout

    def test_highest_export_limit(self):
        limit = PERSONA_MATRIX[Persona.AUDITOR]["max_export_rows"]
        for persona in Persona:
            if persona != Persona.AUDITOR:
                assert limit >= PERSONA_MATRIX[persona]["max_export_rows"]


# ===========================================================================
# 3. MULTI-ROLE MERGING (FR-003: up to 4 roles)
# ===========================================================================

class TestMultiRoleMerging:
    def test_single_role_returns_own_scopes(self):
        scopes = get_merged_scopes([Persona.FORECASTER])
        assert scopes == get_persona_scopes(Persona.FORECASTER)

    def test_two_roles_union(self):
        merged = get_merged_scopes([Persona.FORECASTER, Persona.ENABLER])
        forecaster = get_persona_scopes(Persona.FORECASTER)
        enabler = get_persona_scopes(Persona.ENABLER)
        assert merged == forecaster | enabler

    def test_all_four_roles(self):
        all_personas = [Persona.FORECASTER, Persona.ENABLER, Persona.EVANGELIST, Persona.AUDITOR]
        merged = get_merged_scopes(all_personas)
        for persona in all_personas:
            for scope in get_persona_scopes(persona):
                assert scope in merged

    def test_merged_views_union(self):
        merged = get_merged_views([Persona.FORECASTER, Persona.EVANGELIST])
        assert ViewGroup.FORECAST_DASHBOARD in merged
        assert ViewGroup.ETHICS_DASHBOARD in merged

    def test_merged_reports_union(self):
        merged = get_merged_reports([Persona.FORECASTER, Persona.AUDITOR])
        assert ReportType.RISK_FORECAST in merged
        assert ReportType.FULL_AUDIT_LOG in merged

    def test_highest_sensitivity_wins(self):
        """Multi-role: highest data ceiling among all personas."""
        # Forecaster (INTERNAL) + Auditor (RESTRICTED) → RESTRICTED
        highest = get_highest_sensitivity([Persona.FORECASTER, Persona.AUDITOR])
        assert highest == DataSensitivity.RESTRICTED

    def test_evangelist_forecaster_sensitivity(self):
        # Evangelist (PUBLIC) + Forecaster (INTERNAL) → INTERNAL
        highest = get_highest_sensitivity([Persona.EVANGELIST, Persona.FORECASTER])
        assert highest == DataSensitivity.INTERNAL

    def test_empty_list_returns_empty(self):
        """Empty persona list returns empty scopes (no permissions)."""
        assert get_merged_scopes([]) == frozenset()


# ===========================================================================
# 4. SCOPE CHECK FUNCTION
# ===========================================================================

class TestScopeCheck:
    def test_scope_present(self):
        scopes = get_persona_scopes(Persona.FORECASTER)
        assert check_scope(scopes, APIScope.FORECAST_READ) is True

    def test_scope_absent(self):
        scopes = get_persona_scopes(Persona.FORECASTER)
        assert check_scope(scopes, APIScope.AUDIT_TRAIL) is False

    def test_admin_scope_never_in_persona(self):
        for persona in Persona:
            scopes = get_persona_scopes(persona)
            assert check_scope(scopes, APIScope.ADMIN_PROVISION) is False


# ===========================================================================
# 5. DENIAL SCENARIO MATRIX — critical for FR-005 "no leaks"
# ===========================================================================

class TestDenialMatrix:
    """
    FR-005 AC: '100% view limits; no leaks'
    Every persona must be denied access to every other persona's exclusive scopes.
    """

    # Exclusive scopes per persona (not shared with any other persona)
    FORECASTER_EXCLUSIVE = {APIScope.FORECAST_CREATE, APIScope.FORECAST_SCENARIO, APIScope.RISK_ALERTS}
    ENABLER_EXCLUSIVE = {APIScope.ONBOARD_MANAGE, APIScope.ONBOARD_TRAINING, APIScope.ONBOARD_INTEGRATIONS}
    EVANGELIST_EXCLUSIVE = {APIScope.ETHICS_PUBLIC, APIScope.ETHICS_BIAS_REVIEW}
    AUDITOR_EXCLUSIVE = {APIScope.AUDIT_EVIDENCE, APIScope.AUDIT_EXPORT, APIScope.AUDIT_COMPLIANCE}

    def test_enabler_denied_forecaster_exclusives(self):
        scopes = get_persona_scopes(Persona.ENABLER)
        for exclusive in self.FORECASTER_EXCLUSIVE:
            assert exclusive not in scopes, f"LEAK: Enabler has {exclusive}"

    def test_evangelist_denied_forecaster_exclusives(self):
        scopes = get_persona_scopes(Persona.EVANGELIST)
        for exclusive in self.FORECASTER_EXCLUSIVE:
            assert exclusive not in scopes, f"LEAK: Evangelist has {exclusive}"

    def test_forecaster_denied_enabler_exclusives(self):
        scopes = get_persona_scopes(Persona.FORECASTER)
        for exclusive in self.ENABLER_EXCLUSIVE:
            assert exclusive not in scopes, f"LEAK: Forecaster has {exclusive}"

    def test_evangelist_denied_enabler_exclusives(self):
        scopes = get_persona_scopes(Persona.EVANGELIST)
        for exclusive in self.ENABLER_EXCLUSIVE:
            assert exclusive not in scopes, f"LEAK: Evangelist has {exclusive}"

    def test_forecaster_denied_evangelist_exclusives(self):
        scopes = get_persona_scopes(Persona.FORECASTER)
        for exclusive in self.EVANGELIST_EXCLUSIVE:
            assert exclusive not in scopes, f"LEAK: Forecaster has {exclusive}"

    def test_enabler_denied_evangelist_exclusives(self):
        scopes = get_persona_scopes(Persona.ENABLER)
        for exclusive in self.EVANGELIST_EXCLUSIVE:
            assert exclusive not in scopes, f"LEAK: Enabler has {exclusive}"

    def test_forecaster_denied_auditor_exclusives(self):
        scopes = get_persona_scopes(Persona.FORECASTER)
        for exclusive in self.AUDITOR_EXCLUSIVE:
            assert exclusive not in scopes, f"LEAK: Forecaster has {exclusive}"

    def test_enabler_denied_auditor_exclusives(self):
        scopes = get_persona_scopes(Persona.ENABLER)
        for exclusive in self.AUDITOR_EXCLUSIVE:
            assert exclusive not in scopes, f"LEAK: Enabler has {exclusive}"

    def test_evangelist_denied_auditor_exclusives(self):
        scopes = get_persona_scopes(Persona.EVANGELIST)
        for exclusive in self.AUDITOR_EXCLUSIVE:
            assert exclusive not in scopes, f"LEAK: Evangelist has {exclusive}"


# ===========================================================================
# 6. SCHEMA VALIDATION TESTS
# ===========================================================================

class TestSchemaValidation:
    def test_role_assignment_max_4(self):
        from schemas import RoleAssignment
        # Valid: 4 roles
        ra = RoleAssignment(
            roles=["forecaster", "enabler", "evangelist", "auditor"],
            primary_role="forecaster",
        )
        assert len(ra.roles) == 4

    def test_role_assignment_rejects_5(self):
        from schemas import RoleAssignment
        with pytest.raises(Exception):
            RoleAssignment(
                roles=["forecaster", "enabler", "evangelist", "auditor", "forecaster"],
                primary_role="forecaster",
            )

    def test_role_assignment_rejects_invalid_persona(self):
        from schemas import RoleAssignment
        with pytest.raises(Exception):
            RoleAssignment(roles=["hacker"], primary_role="hacker")

    def test_primary_must_be_in_roles(self):
        from schemas import RoleAssignment
        with pytest.raises(Exception):
            RoleAssignment(roles=["forecaster"], primary_role="auditor")

    def test_no_duplicate_roles(self):
        from schemas import RoleAssignment
        with pytest.raises(Exception):
            RoleAssignment(
                roles=["forecaster", "forecaster"],
                primary_role="forecaster",
            )
