"""
GuardrailsAI Hallucination Detection converter.

Source: guardrails-ai/hallucination-detection (HuggingFace)
  - Binary hallucination labels: 0 = grounded, 1 = hallucinated
  - Fields vary by version; we handle both 'text'/'passage' field names.

Reference: Guardrails AI open-source hallucination benchmark dataset.
"""
from __future__ import annotations

import logging
from typing import Any

from datasets import load_dataset

from saro_data_framework.converters.base import BaseConverter
from saro_data_framework.schema import SampleOut

logger = logging.getLogger(__name__)

_HF_PATH = "guardrails-ai/hallucination-detection"


class GuardrailsHallucinationConverter(BaseConverter):
    DATASET_NAME = "guardrails_hallucination"

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
            # Try different field names the dataset may use
            text = (
                row.get("text")
                or row.get("passage")
                or row.get("sentence")
                or row.get("claim")
                or ""
            )
            if not str(text).strip():
                continue

            raw_label = row.get("label") or row.get("hallucination") or row.get("is_hallucination")
            # Normalise label to string
            if raw_label is None:
                label = None
            elif isinstance(raw_label, bool):
                label = "hallucination" if raw_label else "grounded"
            elif isinstance(raw_label, int):
                label = "hallucination" if raw_label == 1 else "grounded"
            else:
                label = str(raw_label).lower()

            # Optional context / reference fields
            context = row.get("context") or row.get("evidence") or row.get("source") or ""
            question = row.get("question") or row.get("query") or ""

            samples.append(
                SampleOut(
                    sample_id=f"gh_{i}",
                    text=self._safe_str(text),
                    label=label,
                    metadata={
                        "context": self._safe_str(context, max_len=2000) if context else None,
                        "question": self._safe_str(question, max_len=500) if question else None,
                        "source": "guardrails-ai/hallucination-detection",
                    },
                )
            )

        logger.info(
            "Converted %d samples from GuardrailsAI Hallucination dataset", len(samples)
        )
        return samples
