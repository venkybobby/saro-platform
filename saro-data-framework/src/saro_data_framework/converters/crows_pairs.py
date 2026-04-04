"""
CrowS-Pairs converter.

Source: nyu-mll/crows_pairs (HuggingFace)
  - Counterfactual dataset for measuring social biases in masked LMs.
  - Each row has:
      sent_more  : more stereotyping sentence
      sent_less  : less stereotyping sentence
      stereo_antistereo : 0=stereotyping, 1=anti-stereotyping
      bias_type  : one of race, gender, religion, profession, etc.

  We produce two samples per row (sent_more + sent_less) and tag with
  group=bias_type for Gate 2 fairness analysis.

Reference: Nangia et al. (2020) "CrowS-Pairs: A Challenge Dataset for
           Measuring Social Biases in Masked Language Models"
"""
from __future__ import annotations

import logging
from typing import Any

from datasets import load_dataset

from saro_data_framework.converters.base import BaseConverter
from saro_data_framework.schema import SampleOut

logger = logging.getLogger(__name__)

_HF_PATH = "nyu-mll/crows_pairs"

_STEREO_LABEL_MAP = {0: "stereotyping", 1: "anti-stereotyping"}


class CrowsPairsConverter(BaseConverter):
    DATASET_NAME = "crows_pairs"

    def download(self) -> Any:
        logger.info("Loading %s from HuggingFace…", _HF_PATH)
        ds = load_dataset(
            _HF_PATH,
            split="test",
            token=self.hf_token,
            trust_remote_code=False,
        )
        return ds

    def convert(self, raw: Any) -> list[SampleOut]:
        samples: list[SampleOut] = []
        sample_idx = 0

        for row in raw:
            sent_more = row.get("sent_more", "")
            sent_less = row.get("sent_less", "")
            bias_type = row.get("bias_type") or row.get("type") or "unknown"
            stereo_flag = row.get("stereo_antistereo")
            label = _STEREO_LABEL_MAP.get(stereo_flag) if stereo_flag is not None else None

            # Sample 1: more-stereotyping sentence
            if sent_more and sent_more.strip():
                samples.append(
                    SampleOut(
                        sample_id=f"cp_{sample_idx}a",
                        text=self._safe_str(sent_more),
                        group=str(bias_type),
                        label=label,
                        metadata={
                            "sentence_type": "more_stereotyping",
                            "bias_type": bias_type,
                            "pair_id": sample_idx,
                            "source": "nyu-mll/crows_pairs",
                        },
                    )
                )

            # Sample 2: less-stereotyping sentence (paired)
            if sent_less and sent_less.strip():
                samples.append(
                    SampleOut(
                        sample_id=f"cp_{sample_idx}b",
                        text=self._safe_str(sent_less),
                        group=str(bias_type),
                        # Flip the label for the less-stereotyping sentence
                        label=(
                            "anti-stereotyping"
                            if label == "stereotyping"
                            else "stereotyping"
                            if label == "anti-stereotyping"
                            else None
                        ),
                        metadata={
                            "sentence_type": "less_stereotyping",
                            "bias_type": bias_type,
                            "pair_id": sample_idx,
                            "source": "nyu-mll/crows_pairs",
                        },
                    )
                )
            sample_idx += 1

        logger.info("Converted %d samples from CrowS-Pairs", len(samples))
        return samples
