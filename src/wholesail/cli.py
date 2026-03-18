"""Command-line entry point for the integration scaffold."""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from wholesail.config.loader import load_source_configs
from wholesail.domain.models import InvalidRow, InvoiceRecord
from wholesail.ingestion.csv_reader import discover_csv_files, read_csv_rows
from wholesail.ingestion.row_mapper import map_row_to_invoice
from wholesail.ingestion.source_resolver import resolve_source
from wholesail.ingestion.validators import validate_invoice
from wholesail.reporting.summary_report import build_customer_balance_rows, build_run_summary
from wholesail.reporting.writers import write_csv_report, write_json_report


def build_parser() -> argparse.ArgumentParser:
    """Create the CLI parser for the reporting workflow."""
    parser = argparse.ArgumentParser(
        description="Normalize provider CSV files and generate per-file customer balance reports."
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("data/input"),
        help="Directory containing source CSV files.",
    )
    parser.add_argument(
        "--config-dir",
        type=Path,
        default=Path("configs/sources"),
        help="Directory containing provider TOML configs.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/output"),
        help="Directory where generated CSV reports will be written.",
    )
    parser.add_argument(
        "--as-of-date",
        type=date.fromisoformat,
        default=date(2022, 3, 31),
        help="Date used for past-due evaluation in ISO format.",
    )
    return parser


def _build_report_path(output_dir: Path, csv_file: Path) -> Path:
    """Build the output path for a single input CSV report."""
    return output_dir / f"{csv_file.stem}-report.csv"


def main() -> None:
    """Run the full integration flow."""
    args = build_parser().parse_args()
    configs = load_source_configs(args.config_dir)
    csv_files = discover_csv_files(args.input_dir)

    unresolved_files = []
    invalid_rows: list[InvalidRow] = []
    generated_reports: list[dict[str, object]] = []
    file_errors: list[dict[str, str]] = []

    for csv_file in csv_files:
        config = resolve_source(csv_file, configs)
        if config is None:
            unresolved_files.append(str(csv_file))
            continue

        excluded_statuses = {status.lower() for status in config.metrics_excluded_statuses}
        valid_records: list[InvoiceRecord] = []

        try:
            raw_rows = read_csv_rows(csv_file)
        except (OSError, UnicodeDecodeError, ValueError) as exc:
            file_errors.append(
                {
                    "file_name": csv_file.name,
                    "source_name": config.source_name,
                    "error": str(exc),
                }
            )
            continue

        for row_number, row in enumerate(raw_rows, start=2):
            try:
                record = map_row_to_invoice(row, config)
            except (KeyError, TypeError, ValueError) as exc:
                invalid_rows.append(
                    InvalidRow(
                        source_name=config.source_name,
                        file_name=csv_file.name,
                        row_number=row_number,
                        errors=[str(exc)],
                    )
                )
                continue

            issues = validate_invoice(record, row_number)
            if issues:
                invalid_rows.append(
                    InvalidRow(
                        source_name=config.source_name,
                        file_name=csv_file.name,
                        row_number=row_number,
                        errors=[issue.message for issue in issues],
                    )
                )
                continue

            valid_records.append(record)

        report_rows = build_customer_balance_rows(
            as_of_date=args.as_of_date,
            records=valid_records,
            excluded_statuses=excluded_statuses,
        )
        report_path = _build_report_path(args.output_dir, csv_file)
        write_csv_report(report_path, report_rows)
        generated_reports.append(
            {
                "input_file": str(csv_file),
                "source_name": config.source_name,
                "output_file": str(report_path),
                "customer_count": len(report_rows),
                "valid_record_count": len(valid_records),
            }
        )

    summary = build_run_summary(
        as_of_date=args.as_of_date,
        source_count=len(configs),
        discovered_files=len(csv_files),
        generated_reports=generated_reports,
        unresolved_files=unresolved_files,
        invalid_rows=invalid_rows,
        file_errors=file_errors,
    )
    write_json_report(args.output_dir / "run_summary.json", summary)


if __name__ == "__main__":
    main()
