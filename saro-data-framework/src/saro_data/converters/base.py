"""
BaseConverter — abstract base for all saro_data dataset converters.

Every converter implements:
  convert(output_dir, max_samples) → Path

The base class provides:
  • save_batch()  — atomic JSON write with tenacity retry
  • _cap()        — enforce max_samples cap
  • _safe_str()   — coerce any value to a non-blank string
  • _strip_long() — truncate very long texts

Usage pattern:
  class MyConverter(BaseConverter):
      MODEL_TYPE   = "my_model_type"
      INTENDED_USE = "my_use_case"
      HF_PATH      = "owner/repo"

      def convert(self, output_dir, max_samples=100):
          ds = load_dataset(self.HF_PATH, split="train")
          samples = [SampleOut(output=row["text"]) for row in ds]
          samples = self._cap(samples, max_samples)
          batch = self._make_batch(samples)
          return self.save_batch(batch, output_dir, f"{self.MODEL_TYPE}_batch.json")
"""
from __future__ import annotations

import json
import logging
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from tenacity import retry, stop_after_attempt, wait_exponential

from saro_data.schema import BatchOut, SampleOut

logger = logging.getLogger(__name__)


class BaseConverter(ABC):
    """Abstract base class for all saro_data converters."""

    MODEL_TYPE: str = "unknown"
    INTENDED_USE: str = "general"
    HF_PATH: str = ""

    def __init__(
        self,
        hf_token: str | None = None,
        trust_remote_code: bool = False,
    ) -> None:
        self.hf_token = hf_token or os.environ.get("HF_TOKEN")
        self.trust_remote_code = trust_remote_code

    @abstractmethod
    def convert(self, output_dir: Path, max_samples: int = 100) -> Path:
        """
        Download the dataset, convert to BatchOut, write to output_dir.
        Returns the path of the written JSON file.
        Must produce ≥50 samples or raise ValueError.
        """

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _make_batch(self, samples: list[SampleOut]) -> BatchOut:
        return BatchOut(
            model_type=self.MODEL_TYPE,
            intended_use=self.INTENDED_USE,
            model_outputs=samples,
            source_dataset=self.HF_PATH or self.MODEL_TYPE,
        )

    @staticmethod
    def _cap(samples: list[SampleOut], max_samples: int) -> list[SampleOut]:
        """Trim to max_samples, preserving original order."""
        if max_samples and len(samples) > max_samples:
            samples = samples[:max_samples]
            logger.debug("Capped to %d samples", max_samples)
        return samples

    @staticmethod
    def _safe_str(value: Any, max_len: int = 8_000) -> str:
        """Coerce value to a stripped, non-empty string, truncating at max_len."""
        s = str(value).strip()
        if len(s) > max_len:
            s = s[:max_len] + " [TRUNCATED]"
        return s

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=20),
        reraise=True,
    )
    def save_batch(self, batch: BatchOut, output_dir: Path, filename: str) -> Path:
        """
        Atomically write a BatchOut as JSON.  The payload written is the
        SARO API format (via batch.to_saro_payload()), not the framework schema,
        so files can be uploaded directly without further translation.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / filename
        payload = batch.to_saro_payload()
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.rename(path)  # atomic rename
        logger.info(
            "Saved %s (%d samples, model_type=%s)",
            path.name,
            batch.sample_count,
            batch.model_type,
        )
        return path
