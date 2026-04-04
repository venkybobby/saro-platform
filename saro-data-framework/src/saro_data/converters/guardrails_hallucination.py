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

# Primary dataset with confirmed field schema (GuardrailsAI/hallucination):
#   "response"     → output text
#   "hallucination"→ 0 (grounded) or 1 (hallucinated)
# Fallback candidates tried in order if primary fails.
_CANDIDATES = [
    ("GuardrailsAI/hallucination", "train", "response", "hallucination"),
    ("guardrails-ai/hallucination-detection", "train", "response", "hallucination"),
    ("truthfulqa/truthful_qa", "validation", "question", None),  # last-resort
]

# Generic field-name fallbacks for unknown dataset schemas
_TEXT_FIELDS = ("response", "text", "passage", "claim", "sentence", "question", "statement")
_LABEL_FIELDS = ("hallucination", "label", "is_hallucination", "output_label", "correct")


def _raw_label_to_int(raw: object) -> int | None:
    """Normalise a heterogeneous label value to 0 / 1 / None."""
    if raw is None:
        return None
    if isinstance(raw, bool):
        return int(raw)
    if isinstance(raw, int):
        return int(bool(raw))
    s = str(raw).strip().lower()
    if s in ("1", "true", "hallucinated", "hallucination", "yes", "incorrect", "wrong"):
        return 1
    if s in ("0", "false", "grounded", "factual", "no", "correct", "right"):
        return 0
    return None


class GuardrailsHallucinationConverter(BaseConverter):
    MODEL_TYPE = "hallucination_detector"
    INTENDED_USE = "factual_accuracy_audit"
    HF_PATH = "GuardrailsAI/hallucination"

    def convert(self, output_dir: Path, max_samples: int = 150) -> Path:
        ds = None
        active_text_field = "response"
        active_label_field = "hallucination"

        for hf_path, split, text_field, label_field in _CANDIDATES:
            try:
                logger.info("Trying dataset: %s (split=%s) …", hf_path, split)
                ds = load_dataset(
                    hf_path,
                    split=split,
                    token=self.hf_token,
                )
                # Verify at least one row has the expected text field
                sample_row = next(iter(ds))
                if text_field not in sample_row:
                    # Fall back to generic field probing
                    text_field = next(
                        (f for f in _TEXT_FIELDS if f in sample_row), None
                    )
                if label_field and label_field not in sample_row:
                    label_field = next(
                        (f for f in _LABEL_FIELDS if f in sample_row), None
                    )
                if not text_field:
                    logger.warning("  → no usable text field in %s, skipping", hf_path)
                    ds = None
                    continue

                active_text_field = text_field
                active_label_field = label_field
                self.HF_PATH = hf_path
                logger.info(
                    "Loaded %s (%d rows); text_field=%s label_field=%s",
                    hf_path, len(ds), active_text_field, active_label_field,
                )
                break
            except Exception as exc:
                logger.warning("  → failed: %s", exc)

        if ds is None:
            raise RuntimeError(
                "Could not load any hallucination dataset. "
                "Check HF_TOKEN and network access."
            )

        samples: list[SampleOut] = []
        for i, row in enumerate(ds):
            text = str(row.get(active_text_field) or "").strip()
            if not text:
                continue

            raw_label = row.get(active_label_field) if active_label_field else None
            ground_truth = _raw_label_to_int(raw_label)

            context = row.get("context") or row.get("evidence") or ""
            confidence = row.get("confidence") or row.get("score") or None

            samples.append(
                SampleOut(
                    output=self._safe_str(text),
                    prediction=float(confidence) if confidence is not None else None,
                    ground_truth=ground_truth,
                    extra={
                        "context": self._safe_str(str(context), max_len=1_000) if context else None,
                        "row_index": i,
                        "source": self.HF_PATH,
                    },
                )
            )
            if max_samples and len(samples) >= max_samples:
                break

        logger.info("Hallucination: %d samples extracted", len(samples))
        samples = self._cap(samples, max_samples)
        batch = self._make_batch(samples)
        return self.save_batch(batch, output_dir, "guardrails_hallucination_batch.json")
