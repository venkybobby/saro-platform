"""
Abstract base class for all SARO dataset converters.

Every converter must implement:
  - download()  → fetch raw dataset (HuggingFace, local file, etc.)
  - convert()   → transform to list[SampleOut]

The base class provides:
  - batch splitting (respects max_samples_per_file)
  - output file writing
  - logging
  - retry logic via tenacity
"""
from __future__ import annotations

import json
import logging
import os
import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from tenacity import retry, stop_after_attempt, wait_exponential

from saro_data_framework.schema import BatchOut, SampleOut

logger = logging.getLogger(__name__)


class BaseConverter(ABC):
    """
    Abstract base for SARO dataset converters.

    Subclasses implement `download()` and `convert()`.
    The `run()` method orchestrates the full pipeline and writes output files.
    """

    #: Override in subclasses to set the canonical dataset name.
    DATASET_NAME: str = "unknown"

    def __init__(
        self,
        output_dir: str = "./output",
        max_samples: int | None = None,
        max_samples_per_file: int = 1000,
        min_samples: int = 50,
        hf_token: str | None = None,
    ) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.max_samples = max_samples
        self.max_samples_per_file = max_samples_per_file
        self.min_samples = min_samples
        self.hf_token = hf_token or os.environ.get("HF_TOKEN")

    @abstractmethod
    def download(self) -> Any:
        """
        Download or load the raw dataset.

        Returns whatever structure is most convenient for `convert()`.
        Should raise on unrecoverable errors.
        """

    @abstractmethod
    def convert(self, raw: Any) -> list[SampleOut]:
        """
        Transform raw dataset rows into SampleOut objects.

        Must return at least `min_samples` items (or raise ValueError).
        """

    def run(self) -> list[Path]:
        """
        Full pipeline: download → convert → split → write.

        Returns a list of output file paths written.
        """
        logger.info("Starting converter: %s", self.DATASET_NAME)

        raw = self._download_with_retry()
        samples = self.convert(raw)

        if not samples:
            raise ValueError(f"{self.DATASET_NAME}: convert() returned no samples")

        # Enforce max_samples cap
        if self.max_samples and len(samples) > self.max_samples:
            samples = samples[: self.max_samples]
            logger.info("Capped to %d samples", len(samples))

        if len(samples) < self.min_samples:
            raise ValueError(
                f"{self.DATASET_NAME}: only {len(samples)} samples produced, "
                f"minimum is {self.min_samples}"
            )

        output_files = self._write_batches(samples)
        logger.info(
            "Converter %s complete: %d samples → %d file(s)",
            self.DATASET_NAME,
            len(samples),
            len(output_files),
        )
        return output_files

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        reraise=True,
    )
    def _download_with_retry(self) -> Any:
        logger.info("Downloading %s (with retry)…", self.DATASET_NAME)
        return self.download()

    def _write_batches(self, samples: list[SampleOut]) -> list[Path]:
        """Split samples into files of max_samples_per_file and write as JSON."""
        files: list[Path] = []
        chunks = [
            samples[i : i + self.max_samples_per_file]
            for i in range(0, len(samples), self.max_samples_per_file)
        ]
        for idx, chunk in enumerate(chunks):
            batch = BatchOut(
                batch_id=str(uuid.uuid4()),
                dataset_name=self.DATASET_NAME,
                samples=chunk,
            )
            filename = self.output_dir / f"{self.DATASET_NAME}_batch_{idx + 1:03d}.json"
            filename.write_text(
                json.dumps(batch.to_api_payload(), indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            logger.info(
                "Wrote %s (%d samples)",
                filename.name,
                len(chunk),
            )
            files.append(filename)
        return files

    @staticmethod
    def _safe_str(value: Any, max_len: int = 10_000) -> str:
        """Coerce a value to a non-empty string, truncating if necessary."""
        s = str(value).strip()
        if len(s) > max_len:
            s = s[:max_len]
        return s
