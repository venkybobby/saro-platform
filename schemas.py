"""
Pydantic v2 request / response schemas for the SARO API.

Naming convention:
  *In   — request body / input
  *Out  — response body / output
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, EmailStr, Field, field_validator


# ─────────────────────────────────────────────────────────────────────────────
# Auth
# ─────────────────────────────────────────────────────────────────────────────


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class UserCreateIn(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    role: Literal["super_admin", "operator"] = "operator"
    tenant_id: uuid.UUID


class UserOut(BaseModel):
    id: uuid.UUID
    email: EmailStr
    role: str
    tenant_id: uuid.UUID
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class BootstrapIn(BaseModel):
    """
    First-run payload: creates the initial tenant + super_admin account.
    Only accepted when the users table is empty (chicken-and-egg bootstrap).
    """

    org_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8)


class TenantCreateIn(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    slug: str = Field(..., pattern=r"^[a-z0-9\-]+$")


class TenantOut(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────────────────────────────────────
# Scan / Audit input
# ─────────────────────────────────────────────────────────────────────────────


class SampleIn(BaseModel):
    """A single text sample in a batch."""

    sample_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    text: str = Field(..., min_length=1)
    # Optional demographic group label (used for Gate 2 fairness analysis)
    group: str | None = None
    # Ground-truth label if known (e.g. "toxic", "safe", "hallucination")
    label: str | None = None
    # Any extra metadata the caller wants to attach
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("text")
    @classmethod
    def text_not_whitespace(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Sample text must not be blank")
        return v


class AuditConfigIn(BaseModel):
    """Optional per-scan configuration overrides."""

    min_samples: int = Field(default=50, ge=50)
    confidence_threshold: float = Field(default=0.95, ge=0.5, le=1.0)
    incident_top_k: int = Field(default=5, ge=1, le=20)
    # Which frameworks to include in compliance mapping
    frameworks: list[str] = Field(
        default=["EU AI Act", "NIST AI RMF", "AIGP", "ISO 42001"]
    )


class BatchIn(BaseModel):
    """
    Full batch submitted to /api/v1/scan.

    Minimum 50 samples enforced per EU AI Act Art. 10 and NIST MAP 2.3.
    """

    batch_id: str | None = Field(default=None)
    dataset_name: str | None = Field(default=None, max_length=255)
    samples: list[SampleIn] = Field(..., min_length=1)
    config: AuditConfigIn = Field(default_factory=AuditConfigIn)

    @field_validator("samples")
    @classmethod
    def enforce_minimum_samples(cls, v: list[SampleIn]) -> list[SampleIn]:
        if len(v) < 50:
            raise ValueError(
                f"Batch contains only {len(v)} samples. "
                "A minimum of 50 samples is required for fairness metrics "
                "(EU AI Act Art. 10, NIST MAP 2.3)."
            )
        return v


# ─────────────────────────────────────────────────────────────────────────────
# saro_data framework batch format (POST /api/v1/scan/data)
# ─────────────────────────────────────────────────────────────────────────────


class SARoDataSampleIn(BaseModel):
    """
    One sample in the saro_data framework format.

    Fields mirror saro_data.schema.SampleOut:
      output       → maps to SampleIn.text
      prediction   → numeric risk score (stored in metadata)
      gender       → demographic group → SampleIn.group
      age          → stored in metadata
      ethnicity    → SampleIn.group (fallback when gender absent)
      ground_truth → 0=safe / 1=risky → SampleIn.label
    """

    output: str = Field(..., min_length=1)
    prediction: float | None = None
    gender: str | None = None
    age: int | None = None
    ethnicity: str | None = None
    ground_truth: int | None = None
    extra: dict[str, Any] = Field(default_factory=dict)

    @field_validator("output")
    @classmethod
    def output_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("output must not be blank")
        return v

    def to_sample_in(self, idx: int, prefix: str = "df") -> SampleIn:
        """Translate to the standard SampleIn used by the audit engine."""
        group = self.gender or self.ethnicity
        label: str | None = None
        if self.ground_truth is not None:
            label = "risky" if self.ground_truth == 1 else "safe"
        elif self.prediction is not None:
            label = "risky" if self.prediction >= 0.5 else "safe"
        return SampleIn(
            sample_id=f"{prefix}_{idx}",
            text=self.output,
            group=group,
            label=label,
            metadata={
                "prediction": self.prediction,
                "age": self.age,
                "ground_truth": self.ground_truth,
                **self.extra,
            },
        )


class SARoDataBatchIn(BaseModel):
    """
    Batch in the saro_data framework schema.

    Accepted by POST /api/v1/scan/data.  The endpoint translates this into
    a standard BatchIn and routes it through the same audit engine.

    Fields:
      model_type    — logical model category (e.g. "toxicity_generator")
      intended_use  — use-case under audit (e.g. "content_moderation")
      model_outputs — list of SARoDataSampleIn (≥50 required)
    """

    model_type: str = Field(..., min_length=1, max_length=200)
    intended_use: str = Field(..., min_length=1, max_length=200)
    model_outputs: list[SARoDataSampleIn] = Field(..., min_length=1)
    batch_id: str | None = None

    @field_validator("model_outputs")
    @classmethod
    def enforce_minimum_samples(cls, v: list[SARoDataSampleIn]) -> list[SARoDataSampleIn]:
        if len(v) < 50:
            raise ValueError(
                f"❌ Minimum 50 samples required for valid fairness metrics "
                f"(EU AI Act Art. 10 / NIST MAP 2.3). Got: {len(v)}."
            )
        return v

    def to_batch_in(self) -> BatchIn:
        """
        Translate SARoDataBatchIn → BatchIn for the audit engine.
        model_type is used as dataset_name; model_outputs become samples.
        """
        prefix = self.model_type.replace(" ", "_").lower()
        return BatchIn(
            batch_id=self.batch_id,
            dataset_name=self.model_type,
            samples=[s.to_sample_in(i, prefix) for i, s in enumerate(self.model_outputs)],
        )


# ─────────────────────────────────────────────────────────────────────────────
# Scan / Audit output
# ─────────────────────────────────────────────────────────────────────────────


class GateResultOut(BaseModel):
    gate_id: int
    name: str
    status: Literal["pass", "warn", "fail"]
    score: float = Field(..., ge=0.0, le=1.0)
    details: dict[str, Any]


class BayesianDomainScore(BaseModel):
    domain: str
    risk_probability: float = Field(..., ge=0.0, le=1.0)
    ci_lower: float
    ci_upper: float
    sample_count: int
    flagged_count: int


class BayesianScoresOut(BaseModel):
    overall: float
    by_domain: list[BayesianDomainScore]


class MITCoverageOut(BaseModel):
    score: float = Field(..., ge=0.0, le=1.0)
    covered_domains: list[str]
    uncovered_domains: list[str]
    total_risks_flagged: int
    domain_risk_counts: dict[str, int]


class SimilarIncidentOut(BaseModel):
    incident_id: str
    title: str
    category: str
    harm_type: str | None
    affected_sector: str | None
    date: str | None
    url: str | None
    similarity_score: float
    is_fixed: bool


class FixedDeltaOut(BaseModel):
    """
    Compares fixed vs not-fixed rates among similar historical incidents.

    delta > 0 → more fixed than unfixed (favourable historical outcome)
    delta < 0 → more unfixed incidents (ongoing risk pattern)
    """

    fixed_count: int
    unfixed_count: int
    total_similar: int
    delta: float  # = fixed_count/total - unfixed_count/total
    confidence: float


class AppliedRuleOut(BaseModel):
    framework: str
    rule_id: str
    title: str
    triggered_by: str
    obligations: str | None = None


class RemediationOut(BaseModel):
    domain: str
    suggestion: str
    priority: Literal["critical", "high", "medium", "low"]
    related_controls: list[str]


class AuditReportOut(BaseModel):
    audit_id: uuid.UUID
    status: Literal["completed", "failed", "partial"]
    batch_id: str | None
    dataset_name: str | None
    sample_count: int
    gates: list[GateResultOut]
    bayesian_scores: BayesianScoresOut
    mit_coverage: MITCoverageOut
    similar_incidents: list[SimilarIncidentOut]
    fixed_delta: FixedDeltaOut
    applied_rules: list[AppliedRuleOut]
    remediations: list[RemediationOut]
    confidence_score: float
    created_at: datetime


class AuditListItemOut(BaseModel):
    id: uuid.UUID
    batch_id: str | None
    dataset_name: str | None
    sample_count: int
    status: str
    mit_coverage_score: float | None
    fixed_delta: float | None
    overall_risk_score: float | None
    created_at: datetime

    model_config = {"from_attributes": True}
