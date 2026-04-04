"""
RealToxicityPrompts converter.

Source: allenai/real-toxicity-prompts (HuggingFace)
  - Each row has a 'prompt' dict with fields: text, toxicity, severe_toxicity, etc.
  - We extract prompt.text as the sample text.
  - We add the toxicity score to metadata and map it to a label.

Reference: Gehman et al. (2020) "RealToxicityPrompts: Evaluating Neural Toxic
           Degeneration in Language Models"
"""
from __future__ import annotations

import logging
from typing import Any

from datasets import load_dataset

from saro_data_framework.converters.base import BaseConverter
from saro_data_framework.schema import SampleOut

logger = logging.getLogger(__name__)

_HF_PATH = "allenai/real-toxicity-prompts"


class RealToxicityPromptsConverter(BaseConverter):
    DATASET_NAME = "real_toxicity_prompts"

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
            prompt = row.get("prompt") or {}
            text = prompt.get("text", "")
            if not text or not text.strip():
                continue

            # toxicity score 0.0–1.0; label as "toxic" if ≥ 0.5
            toxicity: float | None = prompt.get("toxicity")
            label: str | None = None
            if toxicity is not None:
                label = "toxic" if toxicity >= 0.5 else "safe"

            continuation = row.get("continuation") or {}
            cont_toxicity = continuation.get("toxicity")

            samples.append(
                SampleOut(
                    sample_id=f"rtp_{i}",
                    text=self._safe_str(text),
                    label=label,
                    metadata={
                        "prompt_toxicity": toxicity,
                        "continuation_toxicity": cont_toxicity,
                        "severe_toxicity": prompt.get("severe_toxicity"),
                        "profanity": prompt.get("profanity"),
                        "sexually_explicit": prompt.get("sexually_explicit"),
                        "threat": prompt.get("threat"),
                        "identity_attack": prompt.get("identity_attack"),
                        "insult": prompt.get("insult"),
                        "source": "allenai/real-toxicity-prompts",
                    },
                )
            )

        logger.info("Converted %d samples from RealToxicityPrompts", len(samples))
        return samples
