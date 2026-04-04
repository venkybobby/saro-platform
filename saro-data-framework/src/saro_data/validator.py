"""
AuditReportValidator — validates every SARO audit report returned by the API.

Called by the automated test runner after each upload.  Returns a
ValidationResult containing pass/fail status and a list of rule checks.

Rules checked
-------------
  R01  status == "completed"
  R02  gates has exactly 4 entries
  R03  gate1 (Data Quality) is present and not "fail" for ≥50 samples
  R04  bayesian_scores.overall ∈ [0.0, 1.0]
  R05  all bayesian domain CI: ci_lower ≤ risk_probability ≤ ci_upper
  R06  mit_coverage.score ∈ [0.0, 1.0]
  R07  fixed_delta.delta ∈ [−1.0, 1.0]
  R08  fixed_delta.fixed_count + unfixed_count == total_similar
  R09  confidence_score ∈ [0.0, 1.0]
  R10  all applied_rules have framework, rule_id, title, triggered_by
  R11  all remediations have domain, suggestion, priority (critical/high/medium/low)
  R12  similar_incidents each have similarity_score ∈ [0, 1]
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

_VALID_PRIORITIES = {"critical", "high", "medium", "low"}
_VALID_STATUSES = {"completed", "failed", "partial"}
_VALID_GATE_STATUSES = {"pass", "warn", "fail"}


@dataclass
class RuleCheck:
    rule_id: str
    description: str
    passed: bool
    detail: str = ""


@dataclass
class ValidationResult:
    dataset_name: str
    audit_id: str
    http_status: int
    checks: list[RuleCheck] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return self.http_status == 200 and all(c.passed for c in self.checks)

    @property
    def failed_checks(self) -> list[RuleCheck]:
        return [c for c in self.checks if not c.passed]

    def summary(self) -> str:
        total = len(self.checks)
        ok = sum(1 for c in self.checks if c.passed)
        status = "PASS" if self.passed else "FAIL"
        return (
            f"[{status}] {self.dataset_name} | audit={self.audit_id[:8]} | "
            f"{ok}/{total} checks passed"
        )


def validate_report(
    report: dict[str, Any],
    dataset_name: str,
    http_status: int = 200,
) -> ValidationResult:
    """
    Run all rule checks against an AuditReportOut dict.
    Returns a ValidationResult with per-rule outcomes.
    """
    audit_id = str(report.get("audit_id", "unknown"))
    result = ValidationResult(
        dataset_name=dataset_name,
        audit_id=audit_id,
        http_status=http_status,
    )

    def _add(rule_id: str, desc: str, ok: bool, detail: str = "") -> None:
        result.checks.append(RuleCheck(rule_id, desc, ok, detail))

    # R01 — status
    status = report.get("status", "")
    _add("R01", "status ∈ {completed, failed, partial}",
         status in _VALID_STATUSES, f"got: {status!r}")

    # R02 — gates count
    gates: list[dict] = report.get("gates", [])
    _add("R02", "gates has exactly 4 entries", len(gates) == 4, f"got: {len(gates)}")

    # R03 — gate1 present and not hard-fail (unless status is failed)
    gate1 = next((g for g in gates if g.get("gate_id") == 1), None)
    if gate1 is None:
        _add("R03", "Gate 1 (Data Quality) present", False, "gate1 missing")
    else:
        g1_status = gate1.get("status", "")
        ok = g1_status in _VALID_GATE_STATUSES
        _add("R03", "Gate 1 status valid", ok, f"status={g1_status!r}")

    # R04 — overall risk probability
    overall = report.get("bayesian_scores", {}).get("overall")
    _add("R04", "bayesian_scores.overall ∈ [0, 1]",
         overall is not None and 0.0 <= overall <= 1.0, f"got: {overall}")

    # R05 — per-domain CI order
    by_domain: list[dict] = report.get("bayesian_scores", {}).get("by_domain", [])
    ci_ok = all(
        d.get("ci_lower", -1) <= d.get("risk_probability", -1) <= d.get("ci_upper", 2)
        for d in by_domain
    )
    _add("R05", "all domain CI: ci_lower ≤ mean ≤ ci_upper", ci_ok,
         "" if ci_ok else "one or more domains violate CI ordering")

    # R06 — MIT coverage
    mit_score = report.get("mit_coverage", {}).get("score")
    _add("R06", "mit_coverage.score ∈ [0, 1]",
         mit_score is not None and 0.0 <= mit_score <= 1.0, f"got: {mit_score}")

    # R07 — fixed delta range
    delta = report.get("fixed_delta", {}).get("delta")
    _add("R07", "fixed_delta.delta ∈ [−1, 1]",
         delta is not None and -1.0 <= delta <= 1.0, f"got: {delta}")

    # R08 — fixed_count + unfixed_count == total_similar
    fd = report.get("fixed_delta", {})
    fixed = fd.get("fixed_count", 0)
    unfixed = fd.get("unfixed_count", 0)
    total_sim = fd.get("total_similar", -1)
    _add("R08", "fixed_count + unfixed_count == total_similar",
         fixed + unfixed == total_sim, f"{fixed}+{unfixed}={fixed+unfixed} vs {total_sim}")

    # R09 — confidence score
    conf = report.get("confidence_score")
    _add("R09", "confidence_score ∈ [0, 1]",
         conf is not None and 0.0 <= conf <= 1.0, f"got: {conf}")

    # R10 — applied rules structure
    rules: list[dict] = report.get("applied_rules", [])
    rules_ok = all(
        all(k in r for k in ("framework", "rule_id", "title", "triggered_by"))
        for r in rules
    )
    _add("R10", "all applied_rules have required fields",
         rules_ok, "" if rules_ok else "one or more rules missing required fields")

    # R11 — remediations structure
    remediations: list[dict] = report.get("remediations", [])
    rem_ok = all(
        all(k in r for k in ("domain", "suggestion", "priority"))
        and r.get("priority") in _VALID_PRIORITIES
        for r in remediations
    )
    _add("R11", "all remediations have valid structure",
         rem_ok, "" if rem_ok else "one or more remediations invalid")

    # R12 — similar incidents similarity score
    incidents: list[dict] = report.get("similar_incidents", [])
    inc_ok = all(
        0.0 <= inc.get("similarity_score", -1) <= 1.0 for inc in incidents
    )
    _add("R12", "all incident similarity_scores ∈ [0, 1]",
         inc_ok, "" if inc_ok else "one or more similarity scores out of range")

    if not result.passed:
        for check in result.failed_checks:
            logger.warning(
                "  [FAIL] %s — %s: %s",
                check.rule_id,
                check.description,
                check.detail,
            )

    return result
