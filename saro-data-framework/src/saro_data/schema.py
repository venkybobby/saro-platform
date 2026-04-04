"""
SARO Data Framework — batch schema (Pydantic v2).

SampleOut  — one model output record, rich with demographic & label fields.
BatchOut   — collection of outputs with model_type & intended_use metadata.

Design note
-----------
The framework uses its own schema (model_type / intended_use / model_outputs)
that maps naturally to how each HuggingFace dataset describes model behaviour.
The `to_saro_payload()` method translates to the format expected by the SARO
backend POST /api/v1/scan (samples[].text / group / label).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field, field_validator


# ─────────────────────────────────────────────────────────────────────────────
# Sample-level schema
# ─────────────────────────────────────────────────────────────────────────────


class SampleOut(BaseModel):
    """
    One model-output sample in a SARO test batch.

    Fields map naturally to the data each dataset provides:
      output       — the raw text produced by / fed to the model
      prediction   — numeric risk/toxicity score if the dataset supplies one
      gender       — demographic gender label (for fairness slicing)
      age          — numeric age (HIPAA-safe; >89 replaced by '[AGE]')
      ethnicity    — demographic ethnicity label (for fairness slicing)
      ground_truth — 0/1 label (0 = safe/correct, 1 = risky/incorrect)
    """

    # Primary text field — maps to SARO's samples[].text
    output: str

    # Numeric risk score from the original dataset (0.0 – 1.0)
    prediction: float | None = None

    # Demographic group fields — used for Gate 2 statistical parity analysis
    gender: str | None = None
    age: int | None = None
    ethnicity: str | None = None

    # Ground-truth risk label (0 = benign, 1 = risky/toxic/hallucinated)
    ground_truth: int | None = None

    # Additional dataset-specific metadata preserved for traceability
    extra: dict[str, Any] = Field(default_factory=dict)

    @field_validator("output")
    @classmethod
    def output_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("output must not be blank")
        return v

    def to_saro_sample(self, idx: int, sample_id_prefix: str = "df") -> dict[str, Any]:
        """
        Translate to the SARO API `SampleIn` format:
          text   ← output
          group  ← gender or ethnicity (gender takes priority if both present)
          label  ← str(ground_truth) if available
          metadata ← prediction + age + extra
        """
        group = self.gender or self.ethnicity  # prefer gender for parity analysis

        label: str | None = None
        if self.ground_truth is not None:
            label = "risky" if self.ground_truth == 1 else "safe"
        elif self.prediction is not None:
            label = "risky" if self.prediction >= 0.5 else "safe"

        return {
            "sample_id": f"{sample_id_prefix}_{idx}",
            "text": self.output,
            "group": group,
            "label": label,
            "metadata": {
                "prediction": self.prediction,
                "age": self.age,
                "ground_truth": self.ground_truth,
                **self.extra,
            },
        }


# ─────────────────────────────────────────────────────────────────────────────
# Batch-level schema
# ─────────────────────────────────────────────────────────────────────────────


class BatchOut(BaseModel):
    """
    Complete test batch produced by a converter.

    Attributes
    ----------
    model_type    : logical model category being tested (e.g. "toxicity_generator")
    intended_use  : use-case under audit (e.g. "content_moderation")
    model_outputs : list of SampleOut — must be ≥50 (EU AI Act Art. 10 / NIST MAP 2.3)
    """

    model_type: str = Field(..., min_length=1, max_length=200)
    intended_use: str = Field(..., min_length=1, max_length=200)
    model_outputs: list[SampleOut]

    # Internal bookkeeping — not sent to the API
    source_dataset: str = ""
    batch_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    converted_at: str = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc).isoformat()
    )

    @field_validator("model_outputs")
    @classmethod
    def validate_min_samples(cls, v: list[SampleOut]) -> list[SampleOut]:
        if len(v) < 50:
            raise ValueError(
                f"Batch contains only {len(v)} samples. "
                "A minimum of 50 samples is required for valid fairness metrics "
                "(EU AI Act Art. 10 / NIST MAP 2.3)."
            )
        return v

    @property
    def sample_count(self) -> int:
        return len(self.model_outputs)

    def to_saro_payload(self) -> dict[str, Any]:
        """
        Translate the framework's batch format into the SARO API's BatchIn format
        (POST /api/v1/scan).

        Mapping:
          model_type     → dataset_name
          model_outputs  → samples (each SampleOut.to_saro_sample())
          batch_id       → batch_id
        """
        prefix = self.source_dataset or self.model_type
        return {
            "batch_id": self.batch_id,
            "dataset_name": self.model_type,
            "samples": [s.to_saro_sample(i, prefix) for i, s in enumerate(self.model_outputs)],
            "config": {
                "min_samples": 50,
                "incident_top_k": 5,
                "frameworks": ["EU AI Act", "NIST AI RMF", "AIGP", "ISO 42001"],
            },
        }
