"""Converter registry for saro_data."""
from __future__ import annotations

from saro_data.converters.base import BaseConverter
from saro_data.converters.crows_pairs import CrowsPairsConverter
from saro_data.converters.guardrails_hallucination import GuardrailsHallucinationConverter
from saro_data.converters.mimic3 import MIMIC3Converter
from saro_data.converters.pii_masking import PIIMaskingConverter
from saro_data.converters.real_toxicity_prompts import RealToxicityPromptsConverter
from saro_data.converters.truthfulqa import TruthfulQAConverter

# Maps CLI / config dataset name → converter class
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
