"""
SARO API uploader.

Reads converted batch JSON files from the output directory and POSTs them
to POST /api/v1/scan, collecting and summarising results.
"""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class SARoUploader:
    """Uploads batch JSON files to the SARO /api/v1/scan endpoint."""

    def __init__(
        self,
        api_base: str,
        token: str,
        timeout: int = 120,
        retry_attempts: int = 3,
    ) -> None:
        self.api_base = api_base.rstrip("/")
        self.token = token
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        self._client = httpx.Client(
            base_url=self.api_base,
            headers={"Authorization": f"Bearer {token}"},
            timeout=timeout,
        )

    def upload_file(self, path: Path) -> dict[str, Any]:
        """Upload a single batch JSON file to /api/v1/scan."""
        logger.info("Uploading %s…", path.name)
        payload = json.loads(path.read_text(encoding="utf-8"))
        return self._post_with_retry(payload)

    def upload_directory(self, directory: Path) -> list[dict[str, Any]]:
        """Upload all *.json files in a directory, return list of reports."""
        files = sorted(directory.glob("*.json"))
        if not files:
            logger.warning("No JSON files found in %s", directory)
            return []

        logger.info("Uploading %d batch files from %s…", len(files), directory)
        results: list[dict[str, Any]] = []
        for f in files:
            try:
                report = self.upload_file(f)
                results.append(report)
                logger.info(
                    "  %s → audit %s (mit_coverage=%.3f, delta=%.3f)",
                    f.name,
                    report.get("audit_id", "?")[:8],
                    report.get("mit_coverage", {}).get("score", 0),
                    report.get("fixed_delta", {}).get("delta", 0),
                )
            except Exception as exc:
                logger.error("  %s → FAILED: %s", f.name, exc)

        logger.info("Uploaded %d/%d files successfully", len(results), len(files))
        return results

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        reraise=True,
    )
    def _post_with_retry(self, payload: dict[str, Any]) -> dict[str, Any]:
        resp = self._client.post("/api/v1/scan", json=payload)
        resp.raise_for_status()
        return resp.json()

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "SARoUploader":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()
