"""
ai4privacy / PII Masking 300k converter.

Source  : ai4privacy/pii-masking-300k
Split   : train
Schema  :
  output        ← source_text  (text containing real PII patterns)
  ground_truth  ← 1 (every row has PII by construction)
  extra.pii_entities  ← list of entity type labels (EMAIL, PHONE, SSN …)
  extra.masked_text   ← target_text (for reference / diff)

The `gender` field is populated from the `language` metadata when it
contains a demographic cue (e.g. gendered names in EN vs DE vs ES).
For most rows `gender` stays None — fairness analysis falls back to
ethnicity / language-code grouping.

Reference:
  ai4privacy PII Masking 300k on HuggingFace.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from datasets import load_dataset

from saro_data.converters.base import BaseConverter
from saro_data.schema import SampleOut

logger = logging.getLogger(__name__)


class PIIMaskingConverter(BaseConverter):
    MODEL_TYPE = "pii_detector"
    INTENDED_USE = "privacy_compliance_audit"
    HF_PATH = "ai4privacy/pii-masking-300k"

    def convert(self, output_dir: Path, max_samples: int = 200) -> Path:
        logger.info("Loading %s …", self.HF_PATH)
        ds = load_dataset(
            self.HF_PATH,
            split="train",
            token=self.hf_token,
            trust_remote_code=self.trust_remote_code,
        )

        samples: list[SampleOut] = []
        for i, row in enumerate(ds):
            text: str = row.get("source_text") or row.get("text") or ""
            if not str(text).strip():
                continue

            # Extract PII entity type labels
            pii_entities: list[str] = []
            privacy_mask: Any = row.get("privacy_mask") or []
            if isinstance(privacy_mask, list):
                for entry in privacy_mask:
                    if isinstance(entry, dict):
                        lbl = (
                            entry.get("label")
                            or entry.get("entity_type")
                            or entry.get("type")
                            or ""
                        )
                        if lbl:
                            pii_entities.append(str(lbl))

            unique_entities = sorted(set(pii_entities))

            # Language code as a proxy group (enables cross-language fairness analysis)
            lang = row.get("language") or row.get("lang") or None

            samples.append(
                SampleOut(
                    output=self._safe_str(str(text)),
                    ground_truth=1,  # every row in this dataset has PII by design
                    ethnicity=str(lang) if lang else None,  # language as demographic proxy
                    extra={
                        "pii_entity_types": unique_entities,
                        "pii_count": len(pii_entities),
                        "masked_text": self._safe_str(
                            row.get("target_text", ""), max_len=1_000
                        ) if row.get("target_text") else None,
                        "row_index": i,
                        "source": self.HF_PATH,
                    },
                )
            )
            if max_samples and len(samples) >= max_samples:
                break

        logger.info("PII Masking: %d samples extracted", len(samples))
        samples = self._cap(samples, max_samples)
        batch = self._make_batch(samples)
        return self.save_batch(batch, output_dir, "pii_masking_batch.json")
