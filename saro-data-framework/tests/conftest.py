"""
Shared fixtures for saro_data tests.

Uses unittest.mock to stub out HuggingFace dataset downloads so tests
run without network access and without an HF token.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from saro_data.schema import BatchOut, SampleOut


# ── Minimal sample factories ──────────────────────────────────────────────────


def make_sample(
    output: str = "Test text",
    ground_truth: int | None = 0,
    gender: str | None = None,
    prediction: float | None = None,
    **extra: Any,
) -> SampleOut:
    return SampleOut(
        output=output,
        ground_truth=ground_truth,
        gender=gender,
        prediction=prediction,
        extra=extra,
    )


def make_batch(
    n: int = 60,
    model_type: str = "test_model",
    intended_use: str = "test_audit",
) -> BatchOut:
    samples = [make_sample(output=f"Sample text number {i}") for i in range(n)]
    return BatchOut(model_type=model_type, intended_use=intended_use, model_outputs=samples)


# ── Realistic fake dataset row factories ─────────────────────────────────────


def fake_rtp_row(i: int) -> dict[str, Any]:
    """Fake allenai/real-toxicity-prompts row."""
    return {
        "prompt": {
            "text": f"The user said: sample prompt text {i}",
            "toxicity": 0.8 if i % 3 == 0 else 0.2,
            "severe_toxicity": 0.0,
            "profanity": 0.0,
            "threat": 0.0,
            "identity_attack": 0.0,
            "insult": 0.0,
            "sexually_explicit": 0.0,
        },
        "continuation": {
            "text": f"Continuation text {i}",
            "toxicity": 0.1,
        },
    }


def fake_hallucination_row(i: int) -> dict[str, Any]:
    return {
        "text": f"The Earth orbits the Sun in approximately {i * 30} days.",
        "label": i % 2,  # alternating 0/1
        "context": "Astronomy facts",
        "question": "How long does Earth's orbit take?",
    }


def fake_pii_row(i: int) -> dict[str, Any]:
    return {
        "source_text": f"Contact John Smith at john{i}@example.com or 555-000-{i:04d}",
        "target_text": f"Contact [NAME] at [EMAIL] or [PHONE]",
        "privacy_mask": [
            {"label": "EMAIL", "value": f"john{i}@example.com"},
            {"label": "PHONE", "value": f"555-000-{i:04d}"},
        ],
        "language": "en",
    }


def fake_crows_row(i: int) -> dict[str, Any]:
    return {
        "sent_more": f"The {['man', 'woman'][i%2]} is more likely to be violent.",
        "sent_less": f"The {['woman', 'man'][i%2]} is more likely to be violent.",
        "bias_type": ["race", "gender", "religion", "profession"][i % 4],
        "stereo_antistereo": i % 2,
    }


def fake_tqa_row(i: int) -> dict[str, Any]:
    return {
        "question": f"What is the capital of country number {i}?",
        "best_answer": f"The capital is City{i}.",
        "category": ["Health", "Law", "Science", "History"][i % 4],
        "correct_answers": [f"City{i}", f"Alt City{i}"],
        "incorrect_answers": [f"Wrong{i}", f"Also Wrong{i}"],
        "source": f"https://example.com/{i}",
    }


# ── HuggingFace mock builder ──────────────────────────────────────────────────


def make_hf_mock(rows: list[dict[str, Any]]) -> MagicMock:
    """Create a mock HF dataset that iterates over rows."""
    mock_ds = MagicMock()
    mock_ds.__iter__ = MagicMock(return_value=iter(rows))
    mock_ds.__len__ = MagicMock(return_value=len(rows))
    return mock_ds


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture()
def tmp_output(tmp_path: Path) -> Path:
    """Temporary output directory for batch files."""
    out = tmp_path / "output"
    out.mkdir()
    return out


@pytest.fixture()
def sample_batch() -> BatchOut:
    return make_batch(n=60)


@pytest.fixture()
def minimal_batch() -> BatchOut:
    return make_batch(n=50)


@pytest.fixture()
def sample_report() -> dict[str, Any]:
    """Minimal valid AuditReportOut dict for validator tests."""
    import uuid
    return {
        "audit_id": str(uuid.uuid4()),
        "status": "completed",
        "dataset_name": "test",
        "sample_count": 60,
        "confidence_score": 0.85,
        "gates": [
            {"gate_id": 1, "name": "Data Quality", "status": "pass", "score": 0.97, "details": {}},
            {"gate_id": 2, "name": "Fairness", "status": "warn", "score": 0.60, "details": {}},
            {"gate_id": 3, "name": "Risk Classification", "status": "pass", "score": 0.75, "details": {}},
            {"gate_id": 4, "name": "Compliance Mapping", "status": "pass", "score": 0.90, "details": {}},
        ],
        "bayesian_scores": {
            "overall": 0.25,
            "by_domain": [
                {
                    "domain": "Discrimination & Toxicity",
                    "risk_probability": 0.30,
                    "ci_lower": 0.20,
                    "ci_upper": 0.40,
                    "flagged_count": 10,
                    "sample_count": 60,
                }
            ],
        },
        "mit_coverage": {
            "score": 0.43,
            "covered_domains": ["Discrimination & Toxicity", "Privacy & Security", "Misinformation"],
            "uncovered_domains": ["Malicious Use", "HCI", "Socioeconomic", "AI Safety"],
            "total_risks_flagged": 15,
            "domain_risk_counts": {},
        },
        "similar_incidents": [
            {
                "incident_id": "AIID-001",
                "title": "Biased hiring algorithm",
                "category": "Bias",
                "harm_type": "discrimination",
                "affected_sector": "tech",
                "date": "2019",
                "url": None,
                "similarity_score": 0.82,
                "is_fixed": True,
            }
        ],
        "fixed_delta": {
            "fixed_count": 1,
            "unfixed_count": 0,
            "total_similar": 1,
            "delta": 1.0,
            "confidence": 0.75,
        },
        "applied_rules": [
            {
                "framework": "EU AI Act",
                "rule_id": "ART_10",
                "title": "Data Governance",
                "triggered_by": "bias detection",
                "obligations": "Ensure training data is representative",
            }
        ],
        "remediations": [
            {
                "domain": "Discrimination & Toxicity",
                "suggestion": "Apply adversarial debiasing.",
                "priority": "critical",
                "related_controls": ["EU AI Act Art. 10"],
            }
        ],
        "created_at": "2026-04-03T12:00:00Z",
    }
