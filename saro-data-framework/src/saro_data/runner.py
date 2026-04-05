"""
SARO Data Framework — Automated Test Runner.

Orchestrates the full testing pipeline:
  1. Convert — download real HuggingFace datasets and write batch JSON
  2. Upload  — POST each batch to SARO /api/v1/scan
  3. Validate — run all 12 rule checks on every returned report
  4. Report  — write a JSON + human-readable summary

Usage (programmatic):
    from pathlib import Path
    from saro_data.runner import TestRunner

    runner = TestRunner(
        api_url="http://localhost:8000",
        token="eyJ...",
        output_dir=Path("./output"),
        datasets=["real_toxicity_prompts", "crows_pairs"],
    )
    summary = runner.run()
    print(summary.as_text())

Usage (CLI):
    saro-data run --all --api-url http://localhost:8000 --token $TOKEN
"""
from __future__ import annotations

import json
import logging
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from saro_data.converters import REGISTRY, BaseConverter
from saro_data.uploader import SARoUploader
from saro_data.validator import ValidationResult, validate_report

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Result data structures
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class DatasetResult:
    """Full outcome for one dataset: convert + upload + validate."""

    dataset_name: str
    convert_ok: bool
    convert_error: str = ""
    batch_file: str = ""
    sample_count: int = 0

    upload_ok: bool = False
    upload_error: str = ""

    validation: ValidationResult | None = None

    # Set to True by the runner when operating in convert-only mode so that
    # all_passed does not penalise the missing upload/validation stages.
    convert_only: bool = False

    # Set to True when the dataset is intentionally skipped (e.g. MIMIC-III
    # requires a local licensed file that is expected to be absent in most
    # environments). Skipped datasets are reported separately and never counted
    # as failures so they don't pollute overall_passed.
    skipped: bool = False

    @property
    def all_passed(self) -> bool:
        # Skipped datasets (expected missing local files) are not failures.
        if self.skipped:
            return True
        if self.convert_only:
            return self.convert_ok
        return (
            self.convert_ok
            and self.upload_ok
            and (self.validation is not None and self.validation.passed)
        )


@dataclass
class RunSummary:
    """Aggregate results across all datasets."""

    run_at: str
    api_url: str
    datasets_attempted: int
    datasets_passed: int
    datasets_skipped: int
    datasets_failed: int
    total_samples_uploaded: int
    results: list[DatasetResult] = field(default_factory=list)
    elapsed_seconds: float = 0.0

    @property
    def overall_passed(self) -> bool:
        # Only real failures (not expected skips) determine the outcome.
        return self.datasets_failed == 0

    def as_text(self) -> str:
        """Human-readable summary for CLI output."""
        lines = [
            "═" * 70,
            f"SARO Data Framework — Test Run Summary",
            f"Run at : {self.run_at}",
            f"API    : {self.api_url}",
            f"Elapsed: {self.elapsed_seconds:.1f}s",
            "─" * 70,
        ]
        for r in self.results:
            if r.skipped:
                icon = "⏭  SKIP"
            elif r.all_passed:
                icon = "✅ PASS"
            else:
                icon = "❌ FAIL"
            lines.append(
                f"  {icon}  {r.dataset_name:<35} "
                f"samples={r.sample_count:>4}"
            )
            if r.skipped:
                lines.append(f"         Skipped: {r.convert_error}")
            elif not r.convert_ok:
                lines.append(f"         Convert error: {r.convert_error}")
            elif not r.convert_only and not r.upload_ok:
                lines.append(f"         Upload error:  {r.upload_error}")
            if r.validation and not r.validation.passed:
                for fc in r.validation.failed_checks:
                    lines.append(f"         [{fc.rule_id}] {fc.description}: {fc.detail}")
        skip_note = f"Skipped: {self.datasets_skipped} | " if self.datasets_skipped else ""
        lines += [
            "─" * 70,
            f"  Total: {self.datasets_attempted} | "
            f"Passed: {self.datasets_passed} | "
            f"{skip_note}"
            f"Failed: {self.datasets_failed} | "
            f"Samples: {self.total_samples_uploaded}",
            f"  Overall: {'✅ ALL PASSED' if self.overall_passed else '❌ FAILURES DETECTED'}",
            "═" * 70,
        ]
        return "\n".join(lines)

    def as_dict(self) -> dict[str, Any]:
        """JSON-serialisable dict for writing report files."""
        return {
            "run_at": self.run_at,
            "api_url": self.api_url,
            "overall_passed": self.overall_passed,
            "elapsed_seconds": self.elapsed_seconds,
            "datasets_attempted": self.datasets_attempted,
            "datasets_passed": self.datasets_passed,
            "datasets_failed": self.datasets_failed,
            "total_samples_uploaded": self.total_samples_uploaded,
            "datasets_skipped": self.datasets_skipped,
            "results": [
                {
                    "dataset_name": r.dataset_name,
                    "all_passed": r.all_passed,
                    "skipped": r.skipped,
                    "convert_ok": r.convert_ok,
                    "convert_error": r.convert_error,
                    "batch_file": r.batch_file,
                    "sample_count": r.sample_count,
                    "upload_ok": r.upload_ok,
                    "upload_error": r.upload_error,
                    "validation": (
                        {
                            "passed": r.validation.passed,
                            "checks": [
                                {
                                    "rule_id": c.rule_id,
                                    "description": c.description,
                                    "passed": c.passed,
                                    "detail": c.detail,
                                }
                                for c in r.validation.checks
                            ],
                        }
                        if r.validation
                        else None
                    ),
                }
                for r in self.results
            ],
        }


# ─────────────────────────────────────────────────────────────────────────────
# Runner
# ─────────────────────────────────────────────────────────────────────────────


class TestRunner:
    """
    End-to-end test runner: convert → upload → validate → report.

    Parameters
    ----------
    api_url      : SARO backend base URL (e.g. "http://localhost:8000")
    token        : JWT Bearer token for /api/v1/scan
    output_dir   : directory for converted batch JSON files
    datasets     : list of dataset names from REGISTRY; None = all
    max_samples  : cap applied to every converter (None = use each converter's default)
    hf_token     : HuggingFace token for gated datasets
    report_dir   : where to write run_report.json; defaults to output_dir
    convert_only : when True, skip upload and validation stages (useful for
                   testing converters without a live API — e.g. ``--api-url http://dummy``)
    """

    def __init__(
        self,
        api_url: str,
        token: str,
        output_dir: Path = Path("./output"),
        datasets: list[str] | None = None,
        max_samples: int | None = None,
        hf_token: str | None = None,
        report_dir: Path | None = None,
        convert_only: bool = False,
    ) -> None:
        self.api_url = api_url
        self.token = token
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.datasets = datasets or list(REGISTRY.keys())
        self.max_samples = max_samples
        self.hf_token = hf_token
        self.report_dir = Path(report_dir or output_dir)
        self.convert_only = convert_only

    def run(self) -> RunSummary:
        """Execute the full pipeline and return a RunSummary."""
        start = time.perf_counter()
        run_at = datetime.now(tz=timezone.utc).isoformat()
        mode = "convert-only" if self.convert_only else "full"
        logger.info("Starting SARO test run (%s) — %d datasets", mode, len(self.datasets))

        results: list[DatasetResult] = []

        if self.convert_only:
            # Skip uploader entirely — no network calls needed
            for name in self.datasets:
                result = self._run_one(name, uploader=None)
                results.append(result)
                logger.info("[%s] %s  samples=%d",
                             "OK" if result.all_passed else "FAIL", name, result.sample_count)
        else:
            with SARoUploader(api_url=self.api_url, token=self.token) as uploader:
                for name in self.datasets:
                    result = self._run_one(name, uploader)
                    results.append(result)
                    logger.info(result.validation.summary() if result.validation else
                                 f"[{'OK' if result.all_passed else 'FAIL'}] {name}")

        elapsed = time.perf_counter() - start
        skipped = [r for r in results if r.skipped]
        passed  = [r for r in results if not r.skipped and r.all_passed]
        failed  = [r for r in results if not r.skipped and not r.all_passed]
        total_samples = sum(r.sample_count for r in results if r.upload_ok)

        summary = RunSummary(
            run_at=run_at,
            api_url=self.api_url,
            datasets_attempted=len(results),
            datasets_passed=len(passed),
            datasets_skipped=len(skipped),
            datasets_failed=len(failed),
            total_samples_uploaded=total_samples,
            results=results,
            elapsed_seconds=round(elapsed, 2),
        )

        self._write_report(summary)
        return summary

    # ── Per-dataset pipeline ──────────────────────────────────────────────────

    def _run_one(self, name: str, uploader: SARoUploader | None) -> DatasetResult:
        result = DatasetResult(dataset_name=name, convert_ok=False,
                               convert_only=self.convert_only)

        # ── 1. Convert ────────────────────────────────────────────────────────
        converter_cls = REGISTRY.get(name)
        if converter_cls is None:
            result.convert_error = f"Unknown dataset: {name!r}. Available: {list(REGISTRY)}"
            return result

        try:
            converter: BaseConverter = converter_cls(hf_token=self.hf_token)
            batch_path = converter.convert(
                output_dir=self.output_dir,
                max_samples=self.max_samples or 200,
            )
            result.convert_ok = True
            result.batch_file = batch_path.name

            # Read sample count from written file
            payload = json.loads(batch_path.read_text(encoding="utf-8"))
            result.sample_count = len(payload.get("samples", []))

        except FileNotFoundError as exc:
            # Expected skip: dataset requires a local licensed file (e.g. MIMIC-III).
            # Mark as skipped so it is reported separately and never counted as a failure.
            msg = str(exc).split("\n")[0]
            logger.warning("  %s: skipped — %s", name, msg)
            result.convert_error = msg
            result.skipped = True
            return result
        except Exception as exc:
            logger.error("  %s: convert failed — %s", name, exc, exc_info=True)
            result.convert_error = str(exc)
            return result

        # ── 2. Upload (skipped in convert-only mode) ──────────────────────────
        if self.convert_only:
            logger.info("  %s: convert-only mode — skipping upload", name)
            return result

        try:
            report = uploader.upload_batch(batch_path)  # type: ignore[union-attr]
            result.upload_ok = True
        except Exception as exc:
            result.upload_error = str(exc)
            logger.error("  %s: upload failed — %s", name, exc)
            return result

        # ── 3. Validate ───────────────────────────────────────────────────────
        result.validation = validate_report(
            report=report,
            dataset_name=name,
            http_status=200,
        )
        return result

    # ── Report writing ────────────────────────────────────────────────────────

    def _write_report(self, summary: RunSummary) -> None:
        report_path = self.report_dir / "run_report.json"
        report_path.write_text(
            json.dumps(summary.as_dict(), indent=2), encoding="utf-8"
        )
        logger.info("Run report written to %s", report_path)
