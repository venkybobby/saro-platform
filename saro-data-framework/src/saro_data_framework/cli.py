"""
saro-data CLI

Usage:
    saro-data convert [OPTIONS]       — download + convert datasets → batch JSON
    saro-data upload  [OPTIONS]       — upload batch JSON files to SARO API
    saro-data run     [OPTIONS]       — convert + upload in one command

Examples:
    saro-data convert --dataset real_toxicity_prompts --output ./output
    saro-data convert --all --output ./output --max-samples 500
    saro-data upload --dir ./output --api-url http://localhost:8000 --token $TOKEN
    saro-data run --all --api-url http://localhost:8000 --token $TOKEN
"""
from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path

import click
import structlog
from dotenv import load_dotenv

from saro_data_framework.converters import REGISTRY
from saro_data_framework.uploader import SARoUploader

load_dotenv()

# ── Logging setup ─────────────────────────────────────────────────────────────

structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
)

logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger(__name__)

_ALL_DATASETS = list(REGISTRY.keys())


# ── CLI ───────────────────────────────────────────────────────────────────────

@click.group()
@click.version_option(version="1.0.0", prog_name="saro-data")
def cli() -> None:
    """SARO Data Framework — convert AI-risk datasets to SARO batch JSON."""


@cli.command()
@click.option("--dataset", "-d", multiple=True, help="Dataset name (repeat for multiple)")
@click.option("--all", "all_datasets", is_flag=True, default=False, help="Convert all datasets")
@click.option("--output", "-o", default="./output", show_default=True, help="Output directory")
@click.option("--max-samples", type=int, default=None, help="Max samples per dataset")
@click.option("--max-per-file", type=int, default=1000, show_default=True, help="Max samples per output file")
@click.option("--hf-token", envvar="HF_TOKEN", default=None, help="HuggingFace API token")
def convert(
    dataset: tuple[str, ...],
    all_datasets: bool,
    output: str,
    max_samples: int | None,
    max_per_file: int,
    hf_token: str | None,
) -> None:
    """Download and convert datasets to SARO batch JSON."""
    if all_datasets:
        targets = _ALL_DATASETS
    elif dataset:
        targets = list(dataset)
    else:
        click.echo("Specify --dataset NAME or --all. Use --help for usage.", err=True)
        sys.exit(1)

    unknown = [t for t in targets if t not in REGISTRY]
    if unknown:
        click.echo(f"Unknown datasets: {unknown}. Available: {_ALL_DATASETS}", err=True)
        sys.exit(1)

    success, failed = 0, 0
    for name in targets:
        click.echo(f"\n── {name} ──")
        converter_cls = REGISTRY[name]
        try:
            converter = converter_cls(
                output_dir=output,
                max_samples=max_samples,
                max_samples_per_file=max_per_file,
                hf_token=hf_token,
            )
            files = converter.run()
            for f in files:
                click.echo(f"  ✓ {f}")
            success += 1
        except FileNotFoundError as exc:
            # Special case for MIMIC-III: print clear instructions
            click.echo(f"  ⚠  {exc}", err=True)
            failed += 1
        except Exception as exc:
            click.echo(f"  ✗ {exc}", err=True)
            logger.exception("Converter %s failed", name)
            failed += 1

    click.echo(f"\nDone: {success} succeeded, {failed} failed.")
    if failed:
        sys.exit(1)


@cli.command()
@click.option("--dir", "-d", "input_dir", required=True, help="Directory with batch JSON files")
@click.option(
    "--api-url",
    envvar="SARO_API_URL",
    default="http://localhost:8000",
    show_default=True,
    help="SARO API base URL",
)
@click.option(
    "--token",
    envvar="SARO_TOKEN",
    required=True,
    help="JWT Bearer token (env: SARO_TOKEN)",
)
@click.option("--timeout", type=int, default=120, show_default=True, help="Request timeout (s)")
def upload(
    input_dir: str,
    api_url: str,
    token: str,
    timeout: int,
) -> None:
    """Upload converted batch JSON files to the SARO API."""
    directory = Path(input_dir)
    if not directory.exists():
        click.echo(f"Directory not found: {directory}", err=True)
        sys.exit(1)

    with SARoUploader(api_base=api_url, token=token, timeout=timeout) as uploader:
        reports = uploader.upload_directory(directory)

    if not reports:
        click.echo("No reports returned — check that the API is running and files exist.")
        sys.exit(1)

    # Summary
    click.echo(f"\nSummary: {len(reports)} audits completed")
    for r in reports:
        mit = r.get("mit_coverage", {}).get("score", 0)
        delta = r.get("fixed_delta", {}).get("delta", 0)
        status = r.get("status", "?")
        audit_id = str(r.get("audit_id", "?"))[:8]
        dataset = r.get("dataset_name", "?")
        click.echo(f"  {audit_id}  {dataset:<35}  status={status}  mit={mit:.3f}  delta={delta:+.3f}")


@cli.command()
@click.option("--dataset", "-d", multiple=True)
@click.option("--all", "all_datasets", is_flag=True, default=False)
@click.option("--output", "-o", default="./output", show_default=True)
@click.option("--max-samples", type=int, default=None)
@click.option("--max-per-file", type=int, default=1000, show_default=True)
@click.option("--hf-token", envvar="HF_TOKEN", default=None)
@click.option("--api-url", envvar="SARO_API_URL", default="http://localhost:8000", show_default=True)
@click.option("--token", envvar="SARO_TOKEN", required=True)
@click.option("--timeout", type=int, default=120, show_default=True)
@click.pass_context
def run(ctx: click.Context, **kwargs: object) -> None:
    """Convert datasets then immediately upload to the SARO API."""
    # Invoke convert first, then upload
    ctx.invoke(
        convert,
        dataset=kwargs["dataset"],
        all_datasets=kwargs["all_datasets"],
        output=kwargs["output"],
        max_samples=kwargs["max_samples"],
        max_per_file=kwargs["max_per_file"],
        hf_token=kwargs["hf_token"],
    )
    ctx.invoke(
        upload,
        input_dir=kwargs["output"],
        api_url=kwargs["api_url"],
        token=kwargs["token"],
        timeout=kwargs["timeout"],
    )


if __name__ == "__main__":
    cli()
