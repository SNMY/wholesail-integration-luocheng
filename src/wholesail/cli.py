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
from wholesail.reporting.summary_report import build_report_summary
from wholesail.reporting.writers import write_json_report


def build_parser() -> argparse.ArgumentParser:
    """Create the CLI parser for the reporting workflow."""
    parser = argparse.ArgumentParser(
        description="Normalize provider CSV files and generate balance report summaries."
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
        "--output",
        type=Path,
        default=Path("data/output/report.json"),
        help="Path to the generated summary report.",
    )
    parser.add_argument(
        "--as-of-date",
        type=date.fromisoformat,
        default=date(2022, 3, 31),
        help="Date used for past-due evaluation in ISO format.",
    )
    parser.add_argument(
        "--format",
        choices=("json",),
        default="json",
        help="Output format for the generated report.",
    )
    return parser


def main() -> None:
    """Run the full integration flow."""
    args = build_parser().parse_args()
    configs = load_source_configs(args.config_dir)
    csv_files = discover_csv_files(args.input_dir)

    resolved_files = []
    unresolved_files = []
    valid_records: list[InvoiceRecord] = []
    invalid_rows: list[InvalidRow] = []
    excluded_statuses: set[str] = set()

    for csv_file in csv_files:
        config = resolve_source(csv_file, configs)
        if config is None:
            unresolved_files.append(str(csv_file))
            continue

        resolved_files.append({"file": str(csv_file), "source_name": config.source_name})
        excluded_statuses.update(status.lower() for status in config.metrics_excluded_statuses)

        for row_number, row in enumerate(read_csv_rows(csv_file), start=2):
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

    report = build_report_summary(
        as_of_date=args.as_of_date,
        records=valid_records,
        invalid_rows=invalid_rows,
        source_count=len(configs),
        discovered_files=len(csv_files),
        resolved_files=resolved_files,
        unresolved_files=unresolved_files,
        excluded_statuses=excluded_statuses,
    )

    if args.format == "json":
        write_json_report(args.output, report)


if __name__ == "__main__":
    main()
