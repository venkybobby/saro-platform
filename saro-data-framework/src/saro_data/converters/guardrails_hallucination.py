"""
GuardrailsAI Hallucination Detection converter.

Source  : guardrails-ai/hallucination-detection  (tried first)
          GuardrailsAI/hallucination              (fallback)
Split   : train
Schema  :
  output        ← text / claim / passage (whichever field is present)
  prediction    ← confidence score if available
  ground_truth  ← 1 = hallucinated, 0 = grounded

The dataset field names vary across versions; the converter probes for
all known field names and picks the first non-empty one.

Reference:
  Guardrails AI open-source hallucination benchmark.
"""
from __future__ import annotations

import logging
from pathlib import Path

from datasets import load_dataset

from saro_data.converters.base import BaseConverter
from saro_data.schema import SampleOut

logger = logging.getLogger(__name__)

# GuardrailsAI/hallucination is the BUMP dataset (Benchmarking Unfaithful
# Minimal Pairs).  Confirmed schema from HF Hub dataset card:
#   edited_summary    → output text (the hallucinated summary)
#   reference_summary → ground-truth clean summary
#   article           → source document
#   error_type        → hallucination category (15 types)
#   corrected_error_type → simplified category (7 types)
# All rows are hallucinated (edited_summary has introduced errors) → ground_truth=1.
#
# Fallback: truthfulqa/truthful_qa with config='generation' (needs explicit config).

_CANDIDATES = [
    {
        "hf_path": "GuardrailsAI/hallucination",
        "config": None,
        "split": "train",
        "text_field": "edited_summary",
        "ground_truth": 1,   # every row is a hallucinated summary
    },
    {
        "hf_path": "truthfulqa/truthful_qa",
        "config": "generation",
        "split": "validation",
        "text_field": "question",
        "ground_truth": 0,   # truthful answers → not hallucinated
    },
]


class GuardrailsHallucinationConverter(BaseConverter):
    MODEL_TYPE = "hallucination_detector"
    INTENDED_USE = "factual_accuracy_audit"
    HF_PATH = "GuardrailsAI/hallucination"

    def convert(self, output_dir: Path, max_samples: int = 150) -> Path:
        ds = None
        active: dict = {}

        for candidate in _CANDIDATES:
            hf_path = candidate["hf_path"]
            config = candidate["config"]
            split = candidate["split"]
            try:
                logger.info("Trying dataset: %s config=%s split=%s …", hf_path, config, split)
                load_kwargs: dict = {"split": split, "token": self.hf_token}
                if config:
                    load_kwargs["name"] = config
                ds = load_dataset(hf_path, **load_kwargs)

                # Verify the expected text field exists
                sample_row = next(iter(ds))
                if candidate["text_field"] not in sample_row:
                    logger.warning(
                        "  → text field '%s' missing from %s (available: %s), skipping",
                        candidate["text_field"], hf_path, list(sample_row.keys()),
                    )
                    ds = None
                    continue

                active = candidate
                active["hf_path"] = hf_path
                self.HF_PATH = hf_path
                logger.info("Loaded %s (%d rows)", hf_path, len(ds))
                break
            except Exception as exc:
                logger.warning("  → failed: %s", exc)
                ds = None

        if ds is None:
            raise RuntimeError(
                "Could not load any hallucination dataset. "
                "Check HF_TOKEN and network access."
            )

        text_field = active["text_field"]
        fixed_gt: int = active["ground_truth"]

        samples: list[SampleOut] = []
        for i, row in enumerate(ds):
            text = str(row.get(text_field) or "").strip()
            if not text:
                continue

            # For BUMP dataset enrich extra with article + error category
            extra: dict = {"row_index": i, "source": self.HF_PATH}
            if "article" in row and row["article"]:
                extra["article"] = self._safe_str(str(row["article"]), max_len=1_000)
            if "reference_summary" in row and row["reference_summary"]:
                extra["reference_summary"] = self._safe_str(str(row["reference_summary"]))
            if "corrected_error_type" in row:
                extra["error_type"] = str(row["corrected_error_type"])

            samples.append(
                SampleOut(
                    output=self._safe_str(text),
                    ground_truth=fixed_gt,
                    extra=extra,
                )
            )
            if max_samples and len(samples) >= max_samples:
                break

        logger.info("Hallucination: %d samples extracted", len(samples))
        samples = self._cap(samples, max_samples)
        batch = self._make_batch(samples)
        return self.save_batch(batch, output_dir, "guardrails_hallucination_batch.json")
