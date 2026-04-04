"""
TruthfulQA converter.

Source: truthfulqa/truthful_qa (HuggingFace)
  Two configs:
    - 'generation': question + best_answer + correct_answers + incorrect_answers
    - 'multiple_choice': question + mc1_targets + mc2_targets

We use the 'generation' config by default and produce one sample per question.
The label is "truthful" (question is answerable truthfully) since all
questions in this dataset have verified correct answers.

Group = category (e.g. "Health", "Law", "Science") for fairness slicing.

Reference: Lin et al. (2022) "TruthfulQA: Measuring How Models Mimic Human Falsehoods"
"""
from __future__ import annotations

import logging
from typing import Any

from datasets import load_dataset

from saro_data_framework.converters.base import BaseConverter
from saro_data_framework.schema import SampleOut

logger = logging.getLogger(__name__)

_HF_PATH = "truthfulqa/truthful_qa"


class TruthfulQAConverter(BaseConverter):
    DATASET_NAME = "truthfulqa"

    def __init__(self, config_name: str = "generation", **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.config_name = config_name

    def download(self) -> Any:
        logger.info(
            "Loading %s (config=%s) from HuggingFace…", _HF_PATH, self.config_name
        )
        ds = load_dataset(
            _HF_PATH,
            self.config_name,
            split="validation",
            token=self.hf_token,
            trust_remote_code=False,
        )
        return ds

    def convert(self, raw: Any) -> list[SampleOut]:
        samples: list[SampleOut] = []

        for i, row in enumerate(raw):
            question = row.get("question", "")
            if not question.strip():
                continue

            category = row.get("category") or "unknown"
            best_answer = row.get("best_answer") or ""
            correct_answers = row.get("correct_answers") or []
            incorrect_answers = row.get("incorrect_answers") or []
            source = row.get("source") or ""

            # Build a combined text: question + best answer for richer signal
            if best_answer:
                combined_text = f"Q: {question}\nA: {best_answer}"
            else:
                combined_text = f"Q: {question}"

            samples.append(
                SampleOut(
                    sample_id=f"tqa_{i}",
                    text=self._safe_str(combined_text),
                    group=str(category),
                    label="truthful",  # all entries are factual reference questions
                    metadata={
                        "question": question,
                        "best_answer": best_answer,
                        "correct_answers": correct_answers[:5],  # cap for size
                        "incorrect_answers": incorrect_answers[:5],
                        "category": category,
                        "source_url": source,
                        "config": self.config_name,
                        "source": "truthfulqa/truthful_qa",
                    },
                )
            )

        logger.info("Converted %d samples from TruthfulQA", len(samples))
        return samples
