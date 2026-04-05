"""
saro-data CLI — SARO Data Framework command-line interface.

Commands:
  convert  Download real datasets and write batch JSON files
  upload   POST batch JSON files to the SARO API
  run      Convert + upload + validate in one command (recommended)
  validate Validate a local report JSON file against all 12 rules

Examples:
  # Convert all datasets (except MIMIC-III which needs local file)
  saro-data convert --all --output ./output

  # Convert one dataset with a sample cap
  saro-data convert --dataset crows_pairs --max-samples 200

  # Upload already-converted files
  saro-data upload --dir ./output --api-url http://localhost:8000 --token $TOKEN

  # Full pipeline: convert → upload → validate → print report
  saro-data run --all --api-url http://localhost:8000 --token $TOKEN

  # CI mode: exit 1 if any validation check fails
  saro-data run --all --ci --api-url $SARO_API_URL --token $SARO_TOKEN
"""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import click

from saro_data.converters import REGISTRY
from saro_data.runner import TestRunner
from saro_data.uploader import SARoUploader
from saro_data.validator import validate_report

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s  %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)

_ALL_DATASETS = list(REGISTRY.keys())


@click.group()
@click.version_option(version="1.0.0", prog_name="saro-data")
def cli() -> None:
    """SARO Data Framework — pull real AI datasets and automate SARO testing."""


# ── convert ───────────────────────────────────────────────────────────────────

@cli.command()
@click.option("--dataset", "-d", multiple=True, help="Dataset name; repeat for multiple")
@click.option("--all", "all_datasets", is_flag=True, help="Convert all datasets")
@click.option("--output", "-o", default="./output", show_default=True, help="Output directory")
@click.option("--max-samples", type=int, default=None, help="Max samples per dataset")
@click.option("--hf-token", envvar="HF_TOKEN", default=None, help="HuggingFace token")
def convert(
    dataset: tuple[str, ...],
    all_datasets: bool,
    output: str,
    max_samples: int | None,
    hf_token: str | None,
) -> None:
    """Download real datasets and convert to SARO batch JSON files."""
    targets = _ALL_DATASETS if all_datasets else list(dataset)
    if not targets:
        click.echo("Specify --dataset NAME or --all. Try --help.", err=True)
        sys.exit(1)

    bad = [t for t in targets if t not in REGISTRY]
    if bad:
        click.echo(f"Unknown datasets: {bad}\nAvailable: {_ALL_DATASETS}", err=True)
        sys.exit(1)

    ok = failed = 0
    for name in targets:
        click.echo(f"\n── {name} ──")
        conv = REGISTRY[name](hf_token=hf_token)
        try:
            path = conv.convert(Path(output), max_samples=max_samples or 200)
            click.echo(f"  ✓ {path}")
            ok += 1
        except FileNotFoundError as exc:
            click.echo(f"  ⚠  {str(exc).splitlines()[0]}", err=True)
            failed += 1
        except Exception as exc:
            click.echo(f"  ✗ {exc}", err=True)
            failed += 1

    click.echo(f"\nDone: {ok} succeeded, {failed} failed.")
    if failed:
        sys.exit(1)


# ── upload ────────────────────────────────────────────────────────────────────

@cli.command()
@click.option("--dir", "-d", "input_dir", required=True, help="Directory with batch JSON files")
@click.option("--api-url", envvar="SARO_API_URL", default="http://localhost:8000", show_default=True)
@click.option("--token", envvar="SARO_TOKEN", required=True, help="JWT Bearer token")
@click.option("--timeout", type=int, default=120, show_default=True)
def upload(input_dir: str, api_url: str, token: str, timeout: int) -> None:
    """POST converted batch JSON files to the SARO /api/v1/scan endpoint."""
    directory = Path(input_dir)
    if not directory.exists():
        click.echo(f"Directory not found: {directory}", err=True)
        sys.exit(1)

    with SARoUploader(api_url=api_url, token=token, timeout=timeout) as up:
        reports = up.upload_all(directory)

    if not reports:
        click.echo("No reports returned. Is the API running? Do files exist?")
        sys.exit(1)

    click.echo(f"\n{len(reports)} audits completed:")
    for r in reports:
        mit = r.get("mit_coverage", {}).get("score", 0.0)
        delta = r.get("fixed_delta", {}).get("delta", 0.0)
        click.echo(
            f"  {str(r.get('audit_id','?'))[:8]}  "
            f"{r.get('dataset_name','?'):<30}  "
            f"mit={mit:.3f}  δ={delta:+.3f}  {r.get('status','?')}"
        )


# ── run ───────────────────────────────────────────────────────────────────────

@cli.command()
@click.option("--dataset", "-d", multiple=True)
@click.option("--all", "all_datasets", is_flag=True)
@click.option("--output", "-o", default="./output", show_default=True)
@click.option("--max-samples", type=int, default=None)
@click.option("--hf-token", envvar="HF_TOKEN", default=None)
@click.option("--api-url", envvar="SARO_API_URL", default="http://localhost:8000", show_default=True)
@click.option("--token", envvar="SARO_TOKEN", default="", help="JWT Bearer token (not required with --convert-only)")
@click.option("--timeout", type=int, default=120, show_default=True)
@click.option("--ci", is_flag=True, help="Exit 1 if any validation check fails (for CI)")
@click.option(
    "--convert-only",
    "convert_only",
    is_flag=True,
    help=(
        "Only convert datasets to batch JSON — skip upload and validation. "
        "Useful for testing converters without a live SARO API. "
        "A token is not required when this flag is set."
    ),
)
def run(
    dataset: tuple[str, ...],
    all_datasets: bool,
    output: str,
    max_samples: int | None,
    hf_token: str | None,
    api_url: str,
    token: str,
    timeout: int,
    ci: bool,
    convert_only: bool,
) -> None:
    """Convert → upload → validate — full automated test pipeline."""
    targets = _ALL_DATASETS if all_datasets else list(dataset)
    if not targets:
        click.echo("Specify --dataset NAME or --all.", err=True)
        sys.exit(1)

    if not convert_only and not token:
        click.echo(
            "A --token / SARO_TOKEN is required unless --convert-only is set.", err=True
        )
        sys.exit(1)

    runner = TestRunner(
        api_url=api_url,
        token=token,
        output_dir=Path(output),
        datasets=targets,
        max_samples=max_samples,
        hf_token=hf_token,
        convert_only=convert_only,
    )
    summary = runner.run()
    click.echo(summary.as_text())

    report_path = Path(output) / "run_report.json"
    click.echo(f"\nFull report: {report_path}")

    if ci and not summary.overall_passed:
        click.echo("CI mode: exiting with code 1 (failures detected).", err=True)
        sys.exit(1)


# ── validate ──────────────────────────────────────────────────────────────────

@cli.command()
@click.argument("report_file", type=click.Path(exists=True))
def validate(report_file: str) -> None:
    """Validate a saved AuditReportOut JSON file against all 12 SARO rules."""
    data = json.loads(Path(report_file).read_text(encoding="utf-8"))
    name = data.get("dataset_name") or Path(report_file).stem
    result = validate_report(data, dataset_name=name, http_status=200)
    click.echo(result.summary())
    for check in result.checks:
        icon = "✅" if check.passed else "❌"
        detail = f"  ({check.detail})" if check.detail else ""
        click.echo(f"  {icon} [{check.rule_id}] {check.description}{detail}")
    if not result.passed:
        sys.exit(1)


if __name__ == "__main__":
    cli()
