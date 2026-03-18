"""Build report-friendly summary structures."""

from __future__ import annotations

from collections import defaultdict
from datetime import date
from decimal import Decimal
from typing import Any

from wholesail.domain.metrics import calculate_balance, is_outstanding, is_past_due
from wholesail.domain.models import InvalidRow, InvoiceRecord


def _format_decimal(value: Decimal) -> str:
    """Format a Decimal value using two fractional digits."""
    return f"{value:.2f}"


def build_customer_balance_rows(
    *,
    as_of_date: date,
    records: list[InvoiceRecord],
    excluded_statuses: set[str],
) -> list[dict[str, str]]:
    """Build customer-level balance rows for one input file."""
    grouped_balances: dict[str, dict[str, Decimal]] = defaultdict(
        lambda: {
            "outstanding_balance": Decimal("0"),
            "past_due_balance": Decimal("0"),
        }
    )

    for record in records:
        status = (record.status or "").lower()
        if status in excluded_statuses:
            continue

        balance = calculate_balance(record)
        if is_outstanding(record):
            grouped_balances[record.customer_name]["outstanding_balance"] += balance
        if is_past_due(record, as_of_date):
            grouped_balances[record.customer_name]["past_due_balance"] += balance

    return [
        {
            "customer": customer_name,
            "outstanding_balance": _format_decimal(bucket["outstanding_balance"]),
            "past_due_balance": _format_decimal(bucket["past_due_balance"]),
        }
        for customer_name, bucket in sorted(grouped_balances.items())
    ]


def build_run_summary(
    *,
    as_of_date: date,
    source_count: int,
    discovered_files: int,
    generated_reports: list[dict[str, Any]],
    unresolved_files: list[str],
    invalid_rows: list[InvalidRow],
    file_errors: list[dict[str, str]],
) -> dict[str, Any]:
    """Create a JSON-serializable run summary for generated CSV reports."""
    invalid_row_payload = [
        {
            "source_name": row.source_name,
            "file_name": row.file_name,
            "row_number": row.row_number,
            "errors": row.errors,
        }
        for row in invalid_rows
    ]

    return {
        "as_of_date": as_of_date.isoformat(),
        "run_summary": {
            "source_count": source_count,
            "discovered_files": discovered_files,
            "generated_report_count": len(generated_reports),
            "generated_reports": generated_reports,
            "unresolved_files": unresolved_files,
            "file_error_count": len(file_errors),
            "invalid_row_count": len(invalid_rows),
        },
        "file_errors": file_errors,
        "invalid_rows": invalid_row_payload,
    }
