"""
saro_data — standalone testing data framework for the SARO platform.

Downloads real AI-risk datasets from HuggingFace, converts them to the
SARO batch format, uploads to /api/v1/scan, and validates all rule
responses automatically.
"""
from __future__ import annotations

__version__ = "1.0.0"
__all__ = ["__version__"]
