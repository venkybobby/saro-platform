"""
CrowS-Pairs bias converter.

Source  : nyu-mll/crows_pairs
Split   : test  (1,508 rows; full dataset)
Schema  :
  output         ← sent_more  (the more-stereotyping sentence)
  ground_truth   ← 1 if stereo_antistereo==0 (stereotyping), 0 otherwise
  gender         ← bias_type  (race, gender, religion, profession, etc.)
  extra.sent_less  ← the less-stereotyping counterpart sentence
  extra.pair_id    ← row index for pairing sent_more / sent_less

Design: we produce TWO samples per row — one for each sentence — so the
batch contains paired stereotyping / anti-stereotyping examples.  This
enables Gate 2 (Fairness) to compute per-group statistical parity
across all bias categories.

Reference:
  Nangia et al. (2020) "CrowS-Pairs: A Challenge Dataset for Measuring
  Social Biases in Masked Language Models", EMNLP 2020.
"""
from __future__ import annotations

import logging
from pathlib import Path

from datasets import load_dataset

from saro_data.converters.base import BaseConverter
from saro_data.schema import SampleOut

logger = logging.getLogger(__name__)

_STEREO_MAP = {0: 1, 1: 0}  # stereo_antistereo==0 → stereotyping (risky=1)


class CrowsPairsConverter(BaseConverter):
    MODEL_TYPE = "bias_detector"
    INTENDED_USE = "social_bias_audit"
    HF_PATH = "nyu-mll/crows_pairs"

    def convert(self, output_dir: Path, max_samples: int = 200) -> Path:
        logger.info("Loading %s …", self.HF_PATH)
        ds = load_dataset(
            self.HF_PATH,
            split="test",
            token=self.hf_token,
            trust_remote_code=True,   # required: dataset uses a custom loading script
        )

        samples: list[SampleOut] = []
        for row_idx, row in enumerate(ds):
            sent_more: str = row.get("sent_more") or ""
            sent_less: str = row.get("sent_less") or ""
            bias_type: str = str(row.get("bias_type") or row.get("type") or "unknown")
            stereo_flag: int | None = row.get("stereo_antistereo")

            gt_more = _STEREO_MAP.get(stereo_flag, None) if stereo_flag is not None else None
            gt_less = (1 - gt_more) if gt_more is not None else None

            # Sample A — more-stereotyping sentence
            if sent_more.strip():
                samples.append(
                    SampleOut(
                        output=self._safe_str(sent_more),
                        ground_truth=gt_more,
                        gender=bias_type,  # bias_type as the "group" for fairness
                        extra={
                            "sentence_role": "more_stereotyping",
                            "bias_type": bias_type,
                            "pair_id": row_idx,
                            "source": self.HF_PATH,
                        },
                    )
                )

            # Sample B — less-stereotyping counterpart
            if sent_less.strip():
                samples.append(
                    SampleOut(
                        output=self._safe_str(sent_less),
                        ground_truth=gt_less,
                        gender=bias_type,
                        extra={
                            "sentence_role": "less_stereotyping",
                            "bias_type": bias_type,
                            "pair_id": row_idx,
                            "source": self.HF_PATH,
                        },
                    )
                )

            # Each row yields ≤2 samples; stop when we have enough
            if max_samples and len(samples) >= max_samples:
                break

        logger.info("CrowS-Pairs: %d samples extracted", len(samples))
        samples = self._cap(samples, max_samples)
        batch = self._make_batch(samples)
        return self.save_batch(batch, output_dir, "crows_pairs_batch.json")
