"""
ai4privacy/pii-masking-300k converter.

Source: ai4privacy/pii-masking-300k (HuggingFace)
  - `source_text`: original text containing PII
  - `target_text`: text with PII replaced by placeholders
  - `privacy_mask`: list of {value, label} dicts
  - `span_labels`: BIO span annotations

We use source_text as the sample text (which contains real PII patterns)
and extract the PII entity types as labels/metadata.

Reference: ai4privacy open-source PII masking benchmark.
"""
from __future__ import annotations

import logging
from typing import Any

from datasets import load_dataset

from saro_data_framework.converters.base import BaseConverter
from saro_data_framework.schema import SampleOut

logger = logging.getLogger(__name__)

_HF_PATH = "ai4privacy/pii-masking-300k"


class PIIMaskingConverter(BaseConverter):
    DATASET_NAME = "pii_masking"

    def download(self) -> Any:
        logger.info("Loading %s from HuggingFace…", _HF_PATH)
        ds = load_dataset(
            _HF_PATH,
            split="train",
            token=self.hf_token,
            trust_remote_code=False,
        )
        return ds

    def convert(self, raw: Any) -> list[SampleOut]:
        samples: list[SampleOut] = []

        for i, row in enumerate(raw):
            text = row.get("source_text") or row.get("text") or ""
            if not str(text).strip():
                continue

            # Extract PII entity types
            pii_entities: list[str] = []
            privacy_mask = row.get("privacy_mask") or []
            if isinstance(privacy_mask, list):
                for entry in privacy_mask:
                    if isinstance(entry, dict):
                        label = entry.get("label") or entry.get("entity_type") or ""
                        if label:
                            pii_entities.append(str(label))

            # Deduplicate entity types
            unique_entities = sorted(set(pii_entities))

            # Label: "pii_present" if any PII detected, else "clean"
            label = "pii_present" if unique_entities else "clean"

            samples.append(
                SampleOut(
                    sample_id=f"pii_{i}",
                    text=self._safe_str(text),
                    label=label,
                    metadata={
                        "pii_entity_types": unique_entities,
                        "pii_count": len(pii_entities),
                        "masked_text": self._safe_str(row.get("target_text", ""), max_len=2000)
                        if row.get("target_text")
                        else None,
                        "source": "ai4privacy/pii-masking-300k",
                    },
                )
            )

        logger.info("Converted %d samples from PII Masking 300k", len(samples))
        return samples
