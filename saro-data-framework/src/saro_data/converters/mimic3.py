"""
MIMIC-III Clinical Notes converter.

⚠️  CREDENTIAL NOTICE ⚠️
MIMIC-III requires a PhysioNet credentialed account and a signed Data Use
Agreement. This converter reads from a *locally downloaded* file only.

Obtain access:
  1. Register at https://physionet.org
  2. Complete the CITI "Data or Specimens Only Research" training
  3. Sign the MIMIC-III DUA at https://physionet.org/content/mimiciii/1.4/
  4. Download NOTEEVENTS.csv.gz to a local path
  5. Set MIMIC3_LOCAL_PATH env var

Source  : local NOTEEVENTS.csv.gz
Schema  :
  output        ← de-identified clinical note text (PHI stripped)
  ground_truth  ← None  (no risk labels in MIMIC)
  gender        ← note CATEGORY (e.g. "Discharge summary", "Radiology")
  age           ← None  (PHI stripped; age >89 redacted by MIMIC)
  extra.phi_stripped, extra.category, extra.row_id, extra.source

PHI handling
------------
MIMIC already replaces identifiers with [** … **] tokens.
This converter applies additional regex scrubbing for residual patterns
(phone, email, raw dates, SSNs) before writing output.

⚠️  This is a best-effort de-identification. DO NOT use output in
production without a certified de-identification pipeline.
"""
from __future__ import annotations

import csv
import gzip
import logging
import os
import re
from pathlib import Path
from typing import Any

from saro_data.converters.base import BaseConverter
from saro_data.schema import SampleOut

logger = logging.getLogger(__name__)

# ── PHI scrubbing patterns ────────────────────────────────────────────────────
_PHI_SUBS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[SSN]"),
    (re.compile(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b"), "[PHONE]"),
    (re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"), "[EMAIL]"),
    (re.compile(r"\b\d{1,2}/\d{1,2}/\d{2,4}\b"), "[DATE]"),
    (re.compile(r"\bMRN[:\s]*\d+\b", re.IGNORECASE), "[MRN]"),
    (re.compile(r"\b(age|aged?)\s+\d{2,3}\b", re.IGNORECASE), "[AGE]"),
]

_DEFAULT_CATEGORIES = frozenset(
    {"discharge summary", "radiology", "ecg", "nursing", "physician"}
)


def _strip_phi(text: str) -> str:
    for pat, repl in _PHI_SUBS:
        text = pat.sub(repl, text)
    return re.sub(r"[ \t]{2,}", " ", text).strip()


class MIMIC3Converter(BaseConverter):
    MODEL_TYPE = "clinical_nlp"
    INTENDED_USE = "healthcare_ai_audit"
    HF_PATH = ""  # local only — no HF path

    def __init__(
        self,
        local_path: str | None = None,
        include_categories: list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.local_path = Path(
            local_path
            or os.environ.get("MIMIC3_LOCAL_PATH", "./data/raw/mimic3/NOTEEVENTS.csv.gz")
        )
        self.include_categories: frozenset[str] = (
            frozenset(c.lower() for c in include_categories)
            if include_categories
            else _DEFAULT_CATEGORIES
        )

    def convert(self, output_dir: Path, max_samples: int = 200) -> Path:
        if not self.local_path.exists():
            raise FileNotFoundError(
                f"MIMIC-III file not found: {self.local_path}\n\n"
                "MIMIC-III requires credentialed PhysioNet access.\n"
                "Steps:\n"
                "  1. Register at https://physionet.org\n"
                "  2. Complete CITI 'Data or Specimens Only Research' module\n"
                "  3. Sign the MIMIC-III Data Use Agreement\n"
                "  4. Download NOTEEVENTS.csv.gz\n"
                "  5. Set MIMIC3_LOCAL_PATH=/path/to/NOTEEVENTS.csv.gz\n"
                "     or pass local_path= to the constructor."
            )

        logger.info(
            "Loading MIMIC-III from %s (%.1f MB) …",
            self.local_path,
            self.local_path.stat().st_size / 1e6,
        )

        open_fn = gzip.open if str(self.local_path).endswith(".gz") else open
        samples: list[SampleOut] = []

        with open_fn(self.local_path, "rt", encoding="utf-8", errors="replace") as fh:  # type: ignore[call-overload]
            reader = csv.DictReader(fh)
            for row_idx, row in enumerate(reader):
                category: str = (row.get("CATEGORY") or "").strip()
                if self.include_categories and category.lower() not in self.include_categories:
                    continue

                raw_text: str = (row.get("TEXT") or "").strip()
                if not raw_text:
                    continue

                # Truncate very long notes before PHI stripping
                if len(raw_text) > 12_000:
                    raw_text = raw_text[:12_000]

                clean_text = _strip_phi(raw_text)
                subject_id = row.get("SUBJECT_ID") or str(row_idx)

                samples.append(
                    SampleOut(
                        output=self._safe_str(clean_text),
                        ground_truth=None,  # no risk labels in MIMIC
                        gender=category if category else None,  # category as group
                        extra={
                            "category": category,
                            "subject_id": "[REDACTED]",  # do NOT expose subject IDs
                            "phi_stripped": True,
                            "row_id": row_idx,
                            "source": "MIMIC-III (PhysioNet credentialed)",
                        },
                    )
                )
                if max_samples and len(samples) >= max_samples:
                    break

        logger.info(
            "MIMIC-III: %d notes extracted (categories: %s)",
            len(samples),
            ", ".join(sorted(self.include_categories)),
        )
        samples = self._cap(samples, max_samples)
        batch = self._make_batch(samples)
        return self.save_batch(batch, output_dir, "mimic3_batch.json")
