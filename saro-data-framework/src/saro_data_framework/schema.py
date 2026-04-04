"""
SARO Batch JSON schema (Pydantic v2).

All dataset converters produce a BatchOut which serialises to the exact JSON
format expected by POST /api/v1/scan.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field, field_validator


class SampleOut(BaseModel):
    """A single text sample in a SARO batch."""

    sample_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    text: str
    group: str | None = None      # demographic group for Gate 2 fairness
    label: str | None = None      # ground-truth label if known
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("text")
    @classmethod
    def text_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Sample text must not be blank")
        return v


class BatchOut(BaseModel):
    """
    Complete SARO batch — serialises to the body of POST /api/v1/scan.

    The `samples` list must contain at least 50 entries for the API to accept
    it (EU AI Act Art. 10 / NIST MAP 2.3 enforcement at the API layer).
    """

    batch_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    dataset_name: str
    samples: list[SampleOut]
    config: dict[str, Any] = Field(
        default_factory=lambda: {
            "min_samples": 50,
            "incident_top_k": 5,
            "frameworks": ["EU AI Act", "NIST AI RMF", "AIGP", "ISO 42001"],
        }
    )
    # Framework metadata (not sent to API, used for bookkeeping)
    _source_dataset: str = ""
    _conversion_timestamp: str = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc).isoformat()
    )

    def to_api_payload(self) -> dict[str, Any]:
        """Return the dict to POST to /api/v1/scan."""
        return self.model_dump(
            include={"batch_id", "dataset_name", "samples", "config"},
            mode="json",
        )

    @property
    def sample_count(self) -> int:
        return len(self.samples)
