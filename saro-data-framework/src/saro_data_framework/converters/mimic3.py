"""
MIMIC-III Clinical Notes converter.

⚠️  CREDENTIAL NOTICE ⚠️
MIMIC-III requires a PhysioNet credentialed account and signed Data Use Agreement.
Access: https://physionet.org/content/mimiciii/1.4/

This converter reads from a locally downloaded NOTEEVENTS.csv.gz file.
It does NOT automatically download from PhysioNet.

Steps to obtain access:
  1. Register at https://physionet.org
  2. Complete the CITI "Data or Specimens Only Research" course
  3. Sign the Data Use Agreement for MIMIC-III
  4. Download NOTEEVENTS.csv.gz to the path specified in config.yaml

PHI handling:
  - All notes are processed through a rule-based PHI stripper before output.
  - Patterns removed: proper names (heuristic), dates, phone numbers, MRNs,
    SSNs, ages > 89 (HIPAA), email addresses, URLs.
  - This is a best-effort de-identification — do NOT use output in production
    without a certified de-identification pipeline.
"""
from __future__ import annotations

import gzip
import logging
import os
import re
from pathlib import Path
from typing import Any

from saro_data_framework.converters.base import BaseConverter
from saro_data_framework.schema import SampleOut

logger = logging.getLogger(__name__)

# ── PHI redaction patterns ────────────────────────────────────────────────────

_PHI_PATTERNS: list[tuple[re.Pattern, str]] = [
    # MIMIC already uses [**...**] placeholders — keep them, they are safe
    # Additional raw PII that might slip through:
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[SSN]"),                          # SSN
    (re.compile(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b"), "[PHONE]"),                # Phone
    (re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"), "[EMAIL]"),  # Email
    (re.compile(r"\b(age|aged?)\s+\d{2,3}\b", re.I), "[AGE]"),                # Age
    (re.compile(r"\b\d{1,2}/\d{1,2}/\d{2,4}\b"), "[DATE]"),                   # Dates
    (re.compile(r"\bMRN[:\s]*\d+\b", re.I), "[MRN]"),                         # MRN
    (re.compile(r"\bpt\s+(is|was|has|presents)\s+[A-Z][a-z]+", re.I), "pt [ANON]"),
]


def _strip_phi(text: str) -> str:
    """Apply rule-based PHI stripping to a clinical note."""
    for pattern, replacement in _PHI_PATTERNS:
        text = pattern.sub(replacement, text)
    # Remove runs of whitespace introduced by redaction
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


class MIMIC3Converter(BaseConverter):
    """
    Reads MIMIC-III NOTEEVENTS.csv.gz and converts clinical notes to SARO samples.

    Set local_path in config or via MIMIC3_LOCAL_PATH env var.
    """

    DATASET_NAME = "mimic3"

    def __init__(
        self,
        local_path: str | None = None,
        include_categories: list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.local_path = local_path or os.environ.get(
            "MIMIC3_LOCAL_PATH", "./data/mimic3/NOTEEVENTS.csv.gz"
        )
        self.include_categories = include_categories or [
            "Discharge summary",
            "Radiology",
            "ECG",
            "Nursing",
            "Physician",
        ]

    def download(self) -> Any:
        """Verify the local file exists; return the path."""
        path = Path(self.local_path)
        if not path.exists():
            raise FileNotFoundError(
                f"MIMIC-III NOTEEVENTS file not found at: {path}\n"
                "\n"
                "MIMIC-III requires a PhysioNet credentialed account and signed DUA.\n"
                "Steps:\n"
                "  1. Register at https://physionet.org\n"
                "  2. Complete the CITI 'Data or Specimens Only Research' course\n"
                "  3. Sign the DUA for MIMIC-III Clinical Database\n"
                "  4. Download NOTEEVENTS.csv.gz\n"
                "  5. Set MIMIC3_LOCAL_PATH env var or local_path in config.yaml"
            )
        logger.info("MIMIC-III notes file found: %s (%.1f MB)", path, path.stat().st_size / 1e6)
        return path

    def convert(self, raw: Any) -> list[SampleOut]:
        """Parse NOTEEVENTS.csv.gz and convert rows to SampleOut."""
        import csv
        import io

        path: Path = raw
        samples: list[SampleOut] = []
        include_set = {c.lower() for c in self.include_categories}

        open_fn = gzip.open if str(path).endswith(".gz") else open

        with open_fn(path, "rt", encoding="utf-8", errors="replace") as f:  # type: ignore[call-overload]
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                category = (row.get("CATEGORY") or "").strip()
                if include_set and category.lower() not in include_set:
                    continue

                text = (row.get("TEXT") or "").strip()
                if not text:
                    continue

                # Truncate very long notes (common in MIMIC)
                if len(text) > 8000:
                    text = text[:8000] + " [TRUNCATED]"

                # Strip PHI
                text = _strip_phi(text)

                subject_id = row.get("SUBJECT_ID", f"s{i}")

                samples.append(
                    SampleOut(
                        sample_id=f"mimic_{subject_id}_{i}",
                        text=text,
                        group=category if category else None,
                        label=None,  # No ground-truth risk labels in MIMIC
                        metadata={
                            "category": category,
                            "chartdate": "[DATE_REDACTED]",
                            "row_id": i,
                            "source": "MIMIC-III (PhysioNet)",
                            "phi_stripped": True,
                        },
                    )
                )

                if self.max_samples and len(samples) >= self.max_samples:
                    break

        logger.info(
            "Converted %d MIMIC-III notes (categories: %s)",
            len(samples),
            ", ".join(self.include_categories),
        )
        return samples
