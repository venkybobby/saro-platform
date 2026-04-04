"""Converter registry — maps dataset name → converter class."""
from __future__ import annotations

from saro_data_framework.converters.base import BaseConverter
from saro_data_framework.converters.crows_pairs import CrowsPairsConverter
from saro_data_framework.converters.guardrails_hallucination import (
    GuardrailsHallucinationConverter,
)
from saro_data_framework.converters.mimic3 import MIMIC3Converter
from saro_data_framework.converters.pii_masking import PIIMaskingConverter
from saro_data_framework.converters.real_toxicity_prompts import RealToxicityPromptsConverter
from saro_data_framework.converters.truthfulqa import TruthfulQAConverter

REGISTRY: dict[str, type[BaseConverter]] = {
    "real_toxicity_prompts": RealToxicityPromptsConverter,
    "guardrails_hallucination": GuardrailsHallucinationConverter,
    "pii_masking": PIIMaskingConverter,
    "crows_pairs": CrowsPairsConverter,
    "truthfulqa": TruthfulQAConverter,
    "mimic3": MIMIC3Converter,
}

__all__ = [
    "BaseConverter",
    "CrowsPairsConverter",
    "GuardrailsHallucinationConverter",
    "MIMIC3Converter",
    "PIIMaskingConverter",
    "RealToxicityPromptsConverter",
    "TruthfulQAConverter",
    "REGISTRY",
]
