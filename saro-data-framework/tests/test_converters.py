"""
Tests for all 6 saro_data converters.

All HuggingFace downloads are mocked so tests run offline with no HF token.
Only the MIMIC-III converter gets a real filesystem test (missing file path).
"""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from saro_data.schema import BatchOut
from tests.conftest import (
    fake_crows_row,
    fake_hallucination_row,
    fake_pii_row,
    fake_rtp_row,
    fake_tqa_row,
    make_hf_mock,
)


def _load_payload(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


# ── RealToxicityPrompts ───────────────────────────────────────────────────────

class TestRealToxicityPromptsConverter:
    @patch("saro_data.converters.real_toxicity_prompts.load_dataset")
    def test_converts_to_batch_json(self, mock_load, tmp_output: Path):
        rows = [fake_rtp_row(i) for i in range(60)]
        mock_load.return_value = make_hf_mock(rows)

        from saro_data.converters.real_toxicity_prompts import RealToxicityPromptsConverter
        conv = RealToxicityPromptsConverter()
        path = conv.convert(tmp_output, max_samples=60)

        assert path.exists()
        payload = _load_payload(path)
        assert len(payload["samples"]) == 60
        assert payload["dataset_name"] == "toxicity_generator"

    @patch("saro_data.converters.real_toxicity_prompts.load_dataset")
    def test_ground_truth_maps_toxicity_threshold(self, mock_load, tmp_output: Path):
        # Row 0: toxicity=0.8 → ground_truth=1 (risky)
        # Row 1: toxicity=0.2 → ground_truth=0 (safe)
        rows = [fake_rtp_row(0), fake_rtp_row(1)] + [fake_rtp_row(i+2) for i in range(58)]
        mock_load.return_value = make_hf_mock(rows)

        from saro_data.converters.real_toxicity_prompts import RealToxicityPromptsConverter
        conv = RealToxicityPromptsConverter()
        path = conv.convert(tmp_output, max_samples=60)
        payload = _load_payload(path)

        # Row 0 has toxicity=0.8 → label should be "risky"
        assert payload["samples"][0]["label"] == "risky"
        assert payload["samples"][1]["label"] == "safe"

    @patch("saro_data.converters.real_toxicity_prompts.load_dataset")
    def test_skips_blank_text_rows(self, mock_load, tmp_output: Path):
        rows = [{"prompt": {"text": ""}, "continuation": {}}]
        rows += [fake_rtp_row(i) for i in range(60)]
        mock_load.return_value = make_hf_mock(rows)

        from saro_data.converters.real_toxicity_prompts import RealToxicityPromptsConverter
        conv = RealToxicityPromptsConverter()
        path = conv.convert(tmp_output, max_samples=60)
        payload = _load_payload(path)
        # Blank row skipped; 60 valid rows remain
        assert len(payload["samples"]) == 60

    @patch("saro_data.converters.real_toxicity_prompts.load_dataset")
    def test_max_samples_respected(self, mock_load, tmp_output: Path):
        rows = [fake_rtp_row(i) for i in range(100)]
        mock_load.return_value = make_hf_mock(rows)

        from saro_data.converters.real_toxicity_prompts import RealToxicityPromptsConverter
        conv = RealToxicityPromptsConverter()
        path = conv.convert(tmp_output, max_samples=75)
        payload = _load_payload(path)
        assert len(payload["samples"]) == 75


# ── GuardrailsHallucination ───────────────────────────────────────────────────

class TestGuardrailsHallucinationConverter:
    @patch("saro_data.converters.guardrails_hallucination.load_dataset")
    def test_converts_and_writes_batch(self, mock_load, tmp_output: Path):
        rows = [fake_hallucination_row(i) for i in range(60)]
        mock_load.return_value = make_hf_mock(rows)

        from saro_data.converters.guardrails_hallucination import GuardrailsHallucinationConverter
        conv = GuardrailsHallucinationConverter()
        path = conv.convert(tmp_output, max_samples=60)

        assert path.exists()
        payload = _load_payload(path)
        assert len(payload["samples"]) == 60

    @patch("saro_data.converters.guardrails_hallucination.load_dataset")
    def test_label_1_maps_to_risky(self, mock_load, tmp_output: Path):
        rows = [fake_hallucination_row(1)] + [fake_hallucination_row(i+2) for i in range(59)]
        mock_load.return_value = make_hf_mock(rows)

        from saro_data.converters.guardrails_hallucination import GuardrailsHallucinationConverter
        conv = GuardrailsHallucinationConverter()
        path = conv.convert(tmp_output, max_samples=60)
        payload = _load_payload(path)
        assert payload["samples"][0]["label"] == "risky"

    @patch("saro_data.converters.guardrails_hallucination.load_dataset")
    def test_all_hf_paths_tried_on_failure(self, mock_load, tmp_output: Path):
        # First call raises, second succeeds
        rows = [fake_hallucination_row(i) for i in range(60)]
        mock_load.side_effect = [
            Exception("not found"),
            make_hf_mock(rows),
        ]

        from saro_data.converters.guardrails_hallucination import GuardrailsHallucinationConverter
        conv = GuardrailsHallucinationConverter()
        path = conv.convert(tmp_output, max_samples=60)
        assert path.exists()
        assert mock_load.call_count == 2


# ── PIIMasking ────────────────────────────────────────────────────────────────

class TestPIIMaskingConverter:
    @patch("saro_data.converters.pii_masking.load_dataset")
    def test_converts_and_writes_batch(self, mock_load, tmp_output: Path):
        rows = [fake_pii_row(i) for i in range(60)]
        mock_load.return_value = make_hf_mock(rows)

        from saro_data.converters.pii_masking import PIIMaskingConverter
        conv = PIIMaskingConverter()
        path = conv.convert(tmp_output, max_samples=60)

        assert path.exists()
        payload = _load_payload(path)
        assert len(payload["samples"]) == 60
        assert payload["dataset_name"] == "pii_detector"

    @patch("saro_data.converters.pii_masking.load_dataset")
    def test_all_ground_truth_is_1(self, mock_load, tmp_output: Path):
        rows = [fake_pii_row(i) for i in range(60)]
        mock_load.return_value = make_hf_mock(rows)

        from saro_data.converters.pii_masking import PIIMaskingConverter
        conv = PIIMaskingConverter()
        path = conv.convert(tmp_output, max_samples=60)
        payload = _load_payload(path)
        # PII dataset: all samples have PII → all risky
        for s in payload["samples"]:
            assert s["label"] == "risky"

    @patch("saro_data.converters.pii_masking.load_dataset")
    def test_language_becomes_group(self, mock_load, tmp_output: Path):
        rows = [fake_pii_row(i) for i in range(60)]
        mock_load.return_value = make_hf_mock(rows)

        from saro_data.converters.pii_masking import PIIMaskingConverter
        conv = PIIMaskingConverter()
        path = conv.convert(tmp_output, max_samples=60)
        payload = _load_payload(path)
        # fake_pii_row sets language="en" → maps to group
        for s in payload["samples"]:
            assert s["group"] == "en"


# ── CrowsPairs ────────────────────────────────────────────────────────────────

class TestCrowsPairsConverter:
    @patch("saro_data.converters.crows_pairs.load_dataset")
    def test_two_samples_per_row(self, mock_load, tmp_output: Path):
        rows = [fake_crows_row(i) for i in range(30)]  # 30 rows → 60 samples
        mock_load.return_value = make_hf_mock(rows)

        from saro_data.converters.crows_pairs import CrowsPairsConverter
        conv = CrowsPairsConverter()
        path = conv.convert(tmp_output, max_samples=60)
        payload = _load_payload(path)
        assert len(payload["samples"]) == 60

    @patch("saro_data.converters.crows_pairs.load_dataset")
    def test_bias_type_becomes_group(self, mock_load, tmp_output: Path):
        rows = [fake_crows_row(i) for i in range(30)]
        mock_load.return_value = make_hf_mock(rows)

        from saro_data.converters.crows_pairs import CrowsPairsConverter
        conv = CrowsPairsConverter()
        path = conv.convert(tmp_output, max_samples=60)
        payload = _load_payload(path)
        bias_types = {"race", "gender", "religion", "profession"}
        for s in payload["samples"]:
            assert s.get("group") in bias_types

    @patch("saro_data.converters.crows_pairs.load_dataset")
    def test_max_samples_cap(self, mock_load, tmp_output: Path):
        rows = [fake_crows_row(i) for i in range(100)]
        mock_load.return_value = make_hf_mock(rows)

        from saro_data.converters.crows_pairs import CrowsPairsConverter
        conv = CrowsPairsConverter()
        path = conv.convert(tmp_output, max_samples=80)
        payload = _load_payload(path)
        assert len(payload["samples"]) == 80


# ── TruthfulQA ────────────────────────────────────────────────────────────────

class TestTruthfulQAConverter:
    @patch("saro_data.converters.truthfulqa.load_dataset")
    def test_converts_and_writes_batch(self, mock_load, tmp_output: Path):
        rows = [fake_tqa_row(i) for i in range(60)]
        mock_load.return_value = make_hf_mock(rows)

        from saro_data.converters.truthfulqa import TruthfulQAConverter
        conv = TruthfulQAConverter()
        path = conv.convert(tmp_output, max_samples=60)

        assert path.exists()
        payload = _load_payload(path)
        assert len(payload["samples"]) == 60

    @patch("saro_data.converters.truthfulqa.load_dataset")
    def test_all_ground_truth_is_0(self, mock_load, tmp_output: Path):
        rows = [fake_tqa_row(i) for i in range(60)]
        mock_load.return_value = make_hf_mock(rows)

        from saro_data.converters.truthfulqa import TruthfulQAConverter
        conv = TruthfulQAConverter()
        path = conv.convert(tmp_output, max_samples=60)
        payload = _load_payload(path)
        for s in payload["samples"]:
            assert s["label"] == "safe"  # ground_truth=0 → safe

    @patch("saro_data.converters.truthfulqa.load_dataset")
    def test_category_becomes_group(self, mock_load, tmp_output: Path):
        rows = [fake_tqa_row(i) for i in range(60)]
        mock_load.return_value = make_hf_mock(rows)

        from saro_data.converters.truthfulqa import TruthfulQAConverter
        conv = TruthfulQAConverter()
        path = conv.convert(tmp_output, max_samples=60)
        payload = _load_payload(path)
        valid_groups = {"Health", "Law", "Science", "History"}
        for s in payload["samples"]:
            assert s.get("group") in valid_groups

    @patch("saro_data.converters.truthfulqa.load_dataset")
    def test_output_contains_q_and_a(self, mock_load, tmp_output: Path):
        rows = [fake_tqa_row(0)] + [fake_tqa_row(i+1) for i in range(59)]
        mock_load.return_value = make_hf_mock(rows)

        from saro_data.converters.truthfulqa import TruthfulQAConverter
        conv = TruthfulQAConverter()
        path = conv.convert(tmp_output, max_samples=60)
        payload = _load_payload(path)
        # First sample combines Q: and A:
        assert "Q:" in payload["samples"][0]["text"]
        assert "A:" in payload["samples"][0]["text"]


# ── MIMIC-III ─────────────────────────────────────────────────────────────────

class TestMIMIC3Converter:
    def test_raises_file_not_found_when_missing(self, tmp_output: Path, tmp_path: Path):
        from saro_data.converters.mimic3 import MIMIC3Converter
        conv = MIMIC3Converter(local_path=str(tmp_path / "NOTEEVENTS.csv.gz"))
        with pytest.raises(FileNotFoundError, match="PhysioNet"):
            conv.convert(tmp_output, max_samples=60)

    def test_converts_real_csv_gz(self, tmp_output: Path, tmp_path: Path):
        """Write a minimal fake CSV.gz and verify the converter reads it."""
        import csv
        import gzip
        import io

        fake_notes = tmp_path / "NOTEEVENTS.csv.gz"
        rows_data = [
            {
                "ROW_ID": str(i),
                "SUBJECT_ID": str(1000 + i),
                "HADM_ID": str(2000 + i),
                "CHARTDATE": "2115-01-01",
                "CATEGORY": "Discharge summary",
                "DESCRIPTION": "Report",
                "CGID": "1",
                "ISERROR": "",
                "TEXT": f"Patient presented with symptoms of condition {i}. "
                        f"Treatment plan includes medication and follow-up. "
                        f"No adverse events reported during the admission.",
            }
            for i in range(60)
        ]

        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=rows_data[0].keys())
        writer.writeheader()
        writer.writerows(rows_data)

        with gzip.open(fake_notes, "wt", encoding="utf-8") as gz:
            gz.write(buf.getvalue())

        from saro_data.converters.mimic3 import MIMIC3Converter
        conv = MIMIC3Converter(
            local_path=str(fake_notes),
            include_categories=["Discharge summary"],
        )
        path = conv.convert(tmp_output, max_samples=60)
        assert path.exists()
        payload = _load_payload(path)
        assert len(payload["samples"]) == 60
        # Check PHI was stripped (no raw dates should survive)
        for s in payload["samples"]:
            assert "SUBJECT_ID" not in s["text"]
