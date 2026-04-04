"""
Tests for saro_data.validator — all 12 rule checks.
"""
from __future__ import annotations

import copy
import uuid

import pytest

from saro_data.validator import validate_report


def _mutate(base: dict, **kwargs) -> dict:
    """Deep-copy base dict and apply key-path mutations."""
    d = copy.deepcopy(base)
    for key, val in kwargs.items():
        parts = key.split(".")
        obj = d
        for part in parts[:-1]:
            obj = obj[part]
        obj[parts[-1]] = val
    return d


class TestValidatorRules:
    def test_valid_report_passes_all_rules(self, sample_report):
        result = validate_report(sample_report, "test_dataset")
        assert result.passed, [c for c in result.failed_checks]

    def test_r01_invalid_status_fails(self, sample_report):
        report = _mutate(sample_report, status="running")
        result = validate_report(report, "test")
        r01 = next(c for c in result.checks if c.rule_id == "R01")
        assert not r01.passed

    def test_r02_wrong_gate_count_fails(self, sample_report):
        report = copy.deepcopy(sample_report)
        report["gates"] = report["gates"][:3]  # remove one gate
        result = validate_report(report, "test")
        r02 = next(c for c in result.checks if c.rule_id == "R02")
        assert not r02.passed

    def test_r03_missing_gate1_fails(self, sample_report):
        report = copy.deepcopy(sample_report)
        report["gates"] = [g for g in report["gates"] if g["gate_id"] != 1]
        report["gates"].append({"gate_id": 5, "name": "Extra", "status": "pass", "score": 1.0, "details": {}})
        result = validate_report(report, "test")
        r03 = next(c for c in result.checks if c.rule_id == "R03")
        assert not r03.passed

    def test_r04_overall_out_of_range_fails(self, sample_report):
        report = copy.deepcopy(sample_report)
        report["bayesian_scores"]["overall"] = 1.5
        result = validate_report(report, "test")
        r04 = next(c for c in result.checks if c.rule_id == "R04")
        assert not r04.passed

    def test_r05_ci_order_violation_fails(self, sample_report):
        report = copy.deepcopy(sample_report)
        report["bayesian_scores"]["by_domain"][0]["ci_lower"] = 0.9  # > risk_probability
        result = validate_report(report, "test")
        r05 = next(c for c in result.checks if c.rule_id == "R05")
        assert not r05.passed

    def test_r06_mit_coverage_out_of_range_fails(self, sample_report):
        report = copy.deepcopy(sample_report)
        report["mit_coverage"]["score"] = -0.1
        result = validate_report(report, "test")
        r06 = next(c for c in result.checks if c.rule_id == "R06")
        assert not r06.passed

    def test_r07_delta_out_of_range_fails(self, sample_report):
        report = copy.deepcopy(sample_report)
        report["fixed_delta"]["delta"] = 2.0
        result = validate_report(report, "test")
        r07 = next(c for c in result.checks if c.rule_id == "R07")
        assert not r07.passed

    def test_r08_fixed_unfixed_sum_mismatch_fails(self, sample_report):
        report = copy.deepcopy(sample_report)
        report["fixed_delta"]["fixed_count"] = 3  # 3 + 0 ≠ 1
        result = validate_report(report, "test")
        r08 = next(c for c in result.checks if c.rule_id == "R08")
        assert not r08.passed

    def test_r09_confidence_out_of_range_fails(self, sample_report):
        report = copy.deepcopy(sample_report)
        report["confidence_score"] = 1.1
        result = validate_report(report, "test")
        r09 = next(c for c in result.checks if c.rule_id == "R09")
        assert not r09.passed

    def test_r10_missing_rule_field_fails(self, sample_report):
        report = copy.deepcopy(sample_report)
        del report["applied_rules"][0]["framework"]
        result = validate_report(report, "test")
        r10 = next(c for c in result.checks if c.rule_id == "R10")
        assert not r10.passed

    def test_r11_invalid_priority_fails(self, sample_report):
        report = copy.deepcopy(sample_report)
        report["remediations"][0]["priority"] = "extreme"
        result = validate_report(report, "test")
        r11 = next(c for c in result.checks if c.rule_id == "R11")
        assert not r11.passed

    def test_r12_similarity_out_of_range_fails(self, sample_report):
        report = copy.deepcopy(sample_report)
        report["similar_incidents"][0]["similarity_score"] = 1.5
        result = validate_report(report, "test")
        r12 = next(c for c in result.checks if c.rule_id == "R12")
        assert not r12.passed

    def test_empty_applied_rules_and_remediations_still_passes(self, sample_report):
        report = copy.deepcopy(sample_report)
        report["applied_rules"] = []
        report["remediations"] = []
        result = validate_report(report, "test")
        r10 = next(c for c in result.checks if c.rule_id == "R10")
        r11 = next(c for c in result.checks if c.rule_id == "R11")
        assert r10.passed
        assert r11.passed

    def test_summary_contains_dataset_name(self, sample_report):
        result = validate_report(sample_report, "my_dataset")
        assert "my_dataset" in result.summary()

    def test_failed_checks_listed_in_failed_checks_property(self, sample_report):
        report = _mutate(sample_report, status="unknown_status")
        result = validate_report(report, "test")
        assert any(c.rule_id == "R01" for c in result.failed_checks)

    def test_http_non_200_marks_result_failed(self, sample_report):
        result = validate_report(sample_report, "test", http_status=422)
        assert not result.passed
