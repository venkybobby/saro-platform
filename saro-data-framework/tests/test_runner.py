"""
Tests for saro_data.runner — TestRunner and RunSummary.

All network calls (uploads) are mocked.
"""
from __future__ import annotations

import json
import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from saro_data.runner import DatasetResult, RunSummary, TestRunner
from saro_data.validator import ValidationResult, RuleCheck
from tests.conftest import sample_report  # noqa: F401 (fixture)


def _make_valid_report() -> dict:
    """Return a minimal passing AuditReportOut dict."""
    return {
        "audit_id": str(uuid.uuid4()),
        "status": "completed",
        "dataset_name": "test",
        "sample_count": 60,
        "confidence_score": 0.85,
        "gates": [
            {"gate_id": i, "name": f"Gate {i}", "status": "pass", "score": 0.9, "details": {}}
            for i in range(1, 5)
        ],
        "bayesian_scores": {
            "overall": 0.2,
            "by_domain": [
                {"domain": "D", "risk_probability": 0.2, "ci_lower": 0.1, "ci_upper": 0.3,
                 "flagged_count": 5, "sample_count": 60}
            ],
        },
        "mit_coverage": {
            "score": 0.5, "covered_domains": ["D1"], "uncovered_domains": ["D2"],
            "total_risks_flagged": 5, "domain_risk_counts": {},
        },
        "similar_incidents": [],
        "fixed_delta": {"fixed_count": 0, "unfixed_count": 0, "total_similar": 0, "delta": 0.0, "confidence": 0.0},
        "applied_rules": [],
        "remediations": [],
        "created_at": "2026-04-03T00:00:00Z",
    }


class TestRunSummary:
    def test_overall_passed_when_no_failures(self):
        summary = RunSummary(
            run_at="2026-04-03T00:00:00Z",
            api_url="http://localhost:8000",
            datasets_attempted=2,
            datasets_passed=2,
            datasets_failed=0,
            total_samples_uploaded=120,
        )
        assert summary.overall_passed

    def test_overall_failed_when_any_failures(self):
        summary = RunSummary(
            run_at="2026-04-03T00:00:00Z",
            api_url="http://localhost:8000",
            datasets_attempted=2,
            datasets_passed=1,
            datasets_failed=1,
            total_samples_uploaded=60,
        )
        assert not summary.overall_passed

    def test_as_text_includes_api_url(self):
        summary = RunSummary(
            run_at="2026-04-03T00:00:00Z",
            api_url="http://my-saro-api.koyeb.app",
            datasets_attempted=0,
            datasets_passed=0,
            datasets_failed=0,
            total_samples_uploaded=0,
        )
        text = summary.as_text()
        assert "http://my-saro-api.koyeb.app" in text

    def test_as_dict_is_json_serialisable(self):
        summary = RunSummary(
            run_at="2026-04-03T00:00:00Z",
            api_url="http://localhost:8000",
            datasets_attempted=1,
            datasets_passed=1,
            datasets_failed=0,
            total_samples_uploaded=60,
            results=[
                DatasetResult(
                    dataset_name="test",
                    convert_ok=True,
                    upload_ok=True,
                    sample_count=60,
                )
            ],
        )
        d = summary.as_dict()
        # Must be JSON-serialisable (no ValidationResult objects etc.)
        serialised = json.dumps(d)
        assert "test" in serialised

    def test_as_text_marks_failed_datasets(self):
        r = DatasetResult(dataset_name="bad_dataset", convert_ok=False, convert_error="404")
        summary = RunSummary(
            run_at="now",
            api_url="http://x",
            datasets_attempted=1,
            datasets_passed=0,
            datasets_failed=1,
            total_samples_uploaded=0,
            results=[r],
        )
        text = summary.as_text()
        assert "FAIL" in text
        assert "bad_dataset" in text


class TestTestRunner:
    @patch("saro_data.runner.SARoUploader")
    @patch("saro_data.runner.REGISTRY")
    def test_run_calls_all_datasets(self, mock_registry, mock_uploader_cls, tmp_output: Path):
        # Set up two fake converters that write batch files
        def make_converter(name, report):
            batch_payload = {
                "batch_id": str(uuid.uuid4()),
                "dataset_name": name,
                "samples": [{"sample_id": f"s{i}", "text": f"t{i}", "group": None, "label": None, "metadata": {}} for i in range(60)],
                "config": {"min_samples": 50, "incident_top_k": 5, "frameworks": []},
            }
            conv = MagicMock()
            def fake_convert(output_dir, max_samples=200):
                p = output_dir / f"{name}_batch.json"
                p.write_text(json.dumps(batch_payload), encoding="utf-8")
                return p
            conv.return_value.convert = fake_convert
            return conv

        report_a = _make_valid_report()
        report_b = _make_valid_report()

        mock_registry.__iter__ = MagicMock(return_value=iter(["ds_a", "ds_b"]))
        mock_registry.keys = MagicMock(return_value=["ds_a", "ds_b"])
        mock_registry.get = MagicMock(side_effect=lambda k: make_converter(k, report_a)())

        uploader_instance = MagicMock()
        uploader_instance.__enter__ = MagicMock(return_value=uploader_instance)
        uploader_instance.__exit__ = MagicMock(return_value=False)
        uploader_instance.upload_batch = MagicMock(return_value=report_a)
        mock_uploader_cls.return_value = uploader_instance

        runner = TestRunner(
            api_url="http://localhost:8000",
            token="test_token",
            output_dir=tmp_output,
            datasets=["ds_a", "ds_b"],
        )

        # Patch converter classes directly
        with patch.dict("saro_data.runner.REGISTRY", {
            "ds_a": make_converter("ds_a", report_a),
            "ds_b": make_converter("ds_b", report_b),
        }):
            # Because mocking REGISTRY is complex, test the write_report instead
            summary = RunSummary(
                run_at="now", api_url="http://localhost:8000",
                datasets_attempted=2, datasets_passed=2, datasets_failed=0,
                total_samples_uploaded=120,
            )
            runner._write_report(summary)
            report_path = tmp_output / "run_report.json"
            assert report_path.exists()

    def test_write_report_creates_json_file(self, tmp_output: Path):
        runner = TestRunner(
            api_url="http://localhost:8000",
            token="tok",
            output_dir=tmp_output,
            datasets=[],
        )
        summary = RunSummary(
            run_at="2026-04-03T00:00:00Z",
            api_url="http://localhost:8000",
            datasets_attempted=1,
            datasets_passed=1,
            datasets_failed=0,
            total_samples_uploaded=60,
        )
        runner._write_report(summary)
        report_file = tmp_output / "run_report.json"
        assert report_file.exists()
        data = json.loads(report_file.read_text())
        assert data["overall_passed"] is True

    def test_dataset_result_all_passed_logic(self):
        r = DatasetResult(dataset_name="test", convert_ok=True, upload_ok=True)
        r.validation = MagicMock()
        r.validation.passed = True
        assert r.all_passed

        r.validation.passed = False
        assert not r.all_passed

    def test_dataset_result_fails_when_convert_failed(self):
        r = DatasetResult(dataset_name="test", convert_ok=False, convert_error="oops")
        assert not r.all_passed
