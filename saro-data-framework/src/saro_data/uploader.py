"""
SARO API uploader for the saro_data framework.

Reads converted batch JSON files (already in SARO API format after
BatchOut.to_saro_payload()) and POSTs them to POST /api/v1/scan.

Features:
  • tenacity retry (3 attempts, exponential back-off)
  • Streams results back and logs per-file summary
  • Returns list of AuditReportOut dicts for programmatic inspection
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import httpx
from tenacity import (
    RetryError,
    retry,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)


class SARoUploader:
    """
    Uploads SARO batch JSON files to POST /api/v1/scan.

    The files must already be in SARO API format
    (batch_id / dataset_name / samples / config) — i.e. they come from
    BaseConverter.save_batch() which calls BatchOut.to_saro_payload().
    """

    def __init__(
        self,
        api_url: str,
        token: str,
        timeout: int = 120,
    ) -> None:
        self.api_url = api_url.rstrip("/")
        self.token = token
        self._client = httpx.Client(
            base_url=self.api_url,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            timeout=timeout,
        )

    # ── Single-file upload ────────────────────────────────────────────────────

    def upload_batch(self, batch_path: Path) -> dict[str, Any]:
        """
        Read one batch JSON file and POST it to /api/v1/scan.
        Returns the full AuditReportOut dict.
        """
        logger.info("Uploading %s …", batch_path.name)
        payload = json.loads(batch_path.read_text(encoding="utf-8"))
        return self._post_with_retry(payload)

    # ── Directory upload ──────────────────────────────────────────────────────

    def upload_all(self, output_dir: Path) -> list[dict[str, Any]]:
        """
        Upload all *.json files in output_dir.
        Returns list of report dicts; failures are logged but do not abort.
        """
        files = sorted(output_dir.glob("*.json"))
        if not files:
            logger.warning("No JSON files found in %s", output_dir)
            return []

        logger.info("Uploading %d files from %s …", len(files), output_dir)
        results: list[dict[str, Any]] = []

        for f in files:
            try:
                report = self.upload_batch(f)
                results.append(report)
                self._log_report(f.name, report)
            except RetryError as exc:
                logger.error("  %s → upload failed after retries: %s", f.name, exc)
            except httpx.HTTPStatusError as exc:
                try:
                    detail = exc.response.json().get("detail", str(exc))
                except Exception:
                    detail = str(exc)
                logger.error("  %s → HTTP %d: %s", f.name, exc.response.status_code, detail)
            except Exception as exc:
                logger.error("  %s → unexpected error: %s", f.name, exc, exc_info=True)

        logger.info(
            "Upload complete: %d/%d succeeded",
            len(results),
            len(files),
        )
        return results

    # ── Internal ──────────────────────────────────────────────────────────────

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        reraise=True,
    )
    def _post_with_retry(self, payload: dict[str, Any]) -> dict[str, Any]:
        resp = self._client.post("/api/v1/scan", content=json.dumps(payload))
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def _log_report(filename: str, report: dict[str, Any]) -> None:
        audit_id = str(report.get("audit_id", "?"))[:8]
        status = report.get("status", "?")
        mit = report.get("mit_coverage", {}).get("score", 0.0)
        delta = report.get("fixed_delta", {}).get("delta", 0.0)
        risk = report.get("bayesian_scores", {}).get("overall", 0.0)
        logger.info(
            "  %-45s → %s | mit=%.3f | δ=%+.3f | risk=%.3f | audit=%s",
            filename,
            status,
            mit,
            delta,
            risk,
            audit_id,
        )

    # ── Context manager ───────────────────────────────────────────────────────

    def __enter__(self) -> "SARoUploader":
        return self

    def __exit__(self, *_: Any) -> None:
        self._client.close()

    def close(self) -> None:
        self._client.close()
