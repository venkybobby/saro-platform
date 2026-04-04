"""
TruthfulQA converter.

Source  : truthfulqa/truthful_qa
Config  : "generation"  (question + best_answer + correct/incorrect answers)
Split   : validation  (817 rows — full benchmark)
Schema  :
  output        ← "Q: {question}\\nA: {best_answer}"
  ground_truth  ← 0  (all entries are truthful reference Q&A pairs)
  gender        ← category  (e.g. "Health", "Law", "Science") for fairness slicing
  prediction    ← None  (no numeric score in this dataset)
  extra.question, extra.best_answer, extra.correct_answers,
  extra.incorrect_answers, extra.source_url

Design: this dataset is used to test whether the model hallucinates when
queried with known-answer questions.  ground_truth=0 means "this is a
factually correct reference" — auditing whether the model diverges from
these ground truths is the purpose of the benchmark.

Reference:
  Lin et al. (2022) "TruthfulQA: Measuring How Models Mimic Human
  Falsehoods", ACL 2022.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from datasets import load_dataset

from saro_data.converters.base import BaseConverter
from saro_data.schema import SampleOut

logger = logging.getLogger(__name__)


class TruthfulQAConverter(BaseConverter):
    MODEL_TYPE = "truthfulness_evaluator"
    INTENDED_USE = "hallucination_and_misinformation_audit"
    HF_PATH = "truthfulqa/truthful_qa"

    def __init__(self, config_name: str = "generation", **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.config_name = config_name

    def convert(self, output_dir: Path, max_samples: int = 100) -> Path:
        logger.info(
            "Loading %s (config=%s, split=validation) …",
            self.HF_PATH,
            self.config_name,
        )
        ds = load_dataset(
            self.HF_PATH,
            self.config_name,
            split="validation",
            token=self.hf_token,
            trust_remote_code=self.trust_remote_code,
        )

        samples: list[SampleOut] = []
        for i, row in enumerate(ds):
            question: str = row.get("question") or ""
            if not question.strip():
                continue

            best_answer: str = row.get("best_answer") or ""
            category: str = row.get("category") or "unknown"
            correct_answers: list[str] = row.get("correct_answers") or []
            incorrect_answers: list[str] = row.get("incorrect_answers") or []
            source_url: str = row.get("source") or ""

            # Combine question + best answer for maximum signal coverage
            if best_answer:
                combined = f"Q: {question}\nA: {best_answer}"
            else:
                combined = f"Q: {question}"

            samples.append(
                SampleOut(
                    output=self._safe_str(combined),
                    ground_truth=0,  # truthful reference — 0 = correct/safe
                    gender=str(category),  # category as the group for fairness slicing
                    extra={
                        "question": question,
                        "best_answer": best_answer,
                        "correct_answers": correct_answers[:5],  # cap list size
                        "incorrect_answers": incorrect_answers[:5],
                        "category": category,
                        "source_url": source_url,
                        "config": self.config_name,
                        "row_index": i,
                        "source": self.HF_PATH,
                    },
                )
            )
            if max_samples and len(samples) >= max_samples:
                break

        logger.info("TruthfulQA: %d samples extracted", len(samples))
        samples = self._cap(samples, max_samples)
        batch = self._make_batch(samples)
        return self.save_batch(batch, output_dir, "truthfulqa_batch.json")
