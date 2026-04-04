"""
RealToxicityPrompts converter.

Source  : allenai/real-toxicity-prompts
Split   : train
Schema  :
  output        ← prompt.text (the prompt shown to the model)
  prediction    ← prompt.toxicity (Perspective API score 0.0–1.0)
  ground_truth  ← 1 if toxicity ≥ 0.5 else 0

Additional metadata preserved:
  severe_toxicity, profanity, threat, identity_attack, insult,
  sexually_explicit, continuation_toxicity

Reference:
  Gehman et al. (2020) "RealToxicityPrompts: Evaluating Neural Toxic
  Degeneration in Language Models", EMNLP 2020.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from datasets import load_dataset

from saro_data.converters.base import BaseConverter
from saro_data.schema import SampleOut

logger = logging.getLogger(__name__)


class RealToxicityPromptsConverter(BaseConverter):
    MODEL_TYPE = "toxicity_generator"
    INTENDED_USE = "content_moderation"
    HF_PATH = "allenai/real-toxicity-prompts"

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
            prompt: dict[str, Any] = row.get("prompt") or {}
            text: str = prompt.get("text") or ""
            if not text.strip():
                continue

            toxicity: float | None = prompt.get("toxicity")
            cont: dict[str, Any] = row.get("continuation") or {}

            samples.append(
                SampleOut(
                    output=self._safe_str(text),
                    prediction=float(toxicity) if toxicity is not None else None,
                    ground_truth=1 if (toxicity is not None and toxicity >= 0.5) else 0,
                    extra={
                        "severe_toxicity": prompt.get("severe_toxicity"),
                        "profanity": prompt.get("profanity"),
                        "threat": prompt.get("threat"),
                        "identity_attack": prompt.get("identity_attack"),
                        "insult": prompt.get("insult"),
                        "sexually_explicit": prompt.get("sexually_explicit"),
                        "continuation_toxicity": cont.get("toxicity"),
                        "row_index": i,
                        "source": self.HF_PATH,
                    },
                )
            )

            if max_samples and len(samples) >= max_samples:
                break

        logger.info("RealToxicityPrompts: %d samples extracted", len(samples))
        samples = self._cap(samples, max_samples)
        batch = self._make_batch(samples)
        return self.save_batch(batch, output_dir, "real_toxicity_prompts_batch.json")
