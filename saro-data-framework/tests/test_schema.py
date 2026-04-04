"""
Tests for saro_data.schema — SampleOut, BatchOut, translation layer.
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from saro_data.schema import BatchOut, SampleOut
from tests.conftest import make_batch, make_sample


class TestSampleOut:
    def test_basic_creation(self):
        s = SampleOut(output="Hello world")
        assert s.output == "Hello world"
        assert s.ground_truth is None
        assert s.gender is None

    def test_blank_output_raises(self):
        with pytest.raises(ValidationError, match="blank"):
            SampleOut(output="   ")

    def test_to_saro_sample_maps_output_to_text(self):
        s = SampleOut(output="Test text", ground_truth=1, gender="group_a")
        d = s.to_saro_sample(5)
        assert d["text"] == "Test text"
        assert d["sample_id"] == "df_5"
        assert d["group"] == "group_a"
        assert d["label"] == "risky"

    def test_to_saro_sample_safe_label_for_zero(self):
        s = SampleOut(output="Safe text", ground_truth=0)
        d = s.to_saro_sample(0)
        assert d["label"] == "safe"

    def test_to_saro_sample_label_from_prediction_when_no_ground_truth(self):
        s = SampleOut(output="Some text", prediction=0.9)
        d = s.to_saro_sample(1)
        assert d["label"] == "risky"

    def test_to_saro_sample_no_label_when_no_ground_truth_no_prediction(self):
        s = SampleOut(output="Some text")
        d = s.to_saro_sample(0)
        assert d["label"] is None

    def test_ethnicity_as_group_when_gender_absent(self):
        s = SampleOut(output="text", ethnicity="asian")
        d = s.to_saro_sample(0)
        assert d["group"] == "asian"

    def test_gender_takes_priority_over_ethnicity(self):
        s = SampleOut(output="text", gender="male", ethnicity="asian")
        d = s.to_saro_sample(0)
        assert d["group"] == "male"

    def test_custom_sample_id_prefix(self):
        s = SampleOut(output="text")
        d = s.to_saro_sample(7, sample_id_prefix="rtp")
        assert d["sample_id"] == "rtp_7"

    def test_metadata_contains_prediction_and_age(self):
        s = SampleOut(output="text", prediction=0.3, age=35)
        d = s.to_saro_sample(0)
        assert d["metadata"]["prediction"] == 0.3
        assert d["metadata"]["age"] == 35

    def test_extra_fields_in_metadata(self):
        s = SampleOut(output="text", extra={"source": "rtp", "row_index": 42})
        d = s.to_saro_sample(0)
        assert d["metadata"]["source"] == "rtp"
        assert d["metadata"]["row_index"] == 42


class TestBatchOut:
    def test_creation_with_valid_samples(self):
        batch = make_batch(n=60)
        assert batch.sample_count == 60

    def test_raises_with_fewer_than_50_samples(self):
        samples = [make_sample(output=f"s {i}") for i in range(49)]
        with pytest.raises(ValidationError, match="50"):
            BatchOut(model_type="test", intended_use="test", model_outputs=samples)

    def test_exactly_50_samples_allowed(self):
        samples = [make_sample(output=f"s {i}") for i in range(50)]
        batch = BatchOut(model_type="test", intended_use="test", model_outputs=samples)
        assert batch.sample_count == 50

    def test_to_saro_payload_structure(self):
        batch = make_batch(n=60, model_type="toxicity_generator")
        payload = batch.to_saro_payload()
        assert "batch_id" in payload
        assert "dataset_name" in payload
        assert "samples" in payload
        assert "config" in payload
        assert payload["dataset_name"] == "toxicity_generator"
        assert len(payload["samples"]) == 60

    def test_to_saro_payload_samples_have_required_fields(self):
        batch = make_batch(n=50)
        payload = batch.to_saro_payload()
        for sample in payload["samples"]:
            assert "sample_id" in sample
            assert "text" in sample
            assert sample["text"]  # non-empty

    def test_to_saro_payload_config_has_min_samples(self):
        batch = make_batch(n=50)
        payload = batch.to_saro_payload()
        assert payload["config"]["min_samples"] == 50

    def test_batch_id_is_unique_across_instances(self):
        b1 = make_batch(n=50)
        b2 = make_batch(n=50)
        assert b1.batch_id != b2.batch_id

    def test_source_dataset_propagates_to_sample_ids(self):
        samples = [make_sample(output=f"s {i}") for i in range(50)]
        batch = BatchOut(
            model_type="bias_detector",
            intended_use="fairness_audit",
            model_outputs=samples,
            source_dataset="crows_pairs",
        )
        payload = batch.to_saro_payload()
        # All sample IDs should use the source_dataset as prefix
        assert all(s["sample_id"].startswith("crows_pairs_") for s in payload["samples"])
