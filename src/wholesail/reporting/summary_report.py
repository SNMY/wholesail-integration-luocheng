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


def build_report_summary(
    *,
    as_of_date: date,
    records: list[InvoiceRecord],
    invalid_rows: list[InvalidRow],
    source_count: int,
    discovered_files: int,
    resolved_files: list[dict[str, str]],
    unresolved_files: list[str],
    excluded_statuses: set[str],
) -> dict[str, Any]:
    """Create a JSON-serializable summary for a full ingestion run."""
    grouped_balances: dict[str, dict[str, dict[str, Decimal | int]]] = defaultdict(dict)
    total_outstanding_balance = Decimal("0")
    total_past_due_balance = Decimal("0")
    records_in_metrics = 0

    for record in records:
        status = (record.status or "").lower()
        if status in excluded_statuses:
            continue

        records_in_metrics += 1
        balance = calculate_balance(record)
        is_record_outstanding = is_outstanding(record)
        is_record_past_due = is_past_due(record, as_of_date)

        seller_bucket = grouped_balances.setdefault(record.source_name, {})
        customer_bucket = seller_bucket.setdefault(
            record.customer_name,
            {
                "invoice_count": 0,
                "outstanding_balance": Decimal("0"),
                "past_due_balance": Decimal("0"),
            },
        )
        customer_bucket["invoice_count"] += 1

        if is_record_outstanding:
            customer_bucket["outstanding_balance"] += balance
            total_outstanding_balance += balance
        if is_record_past_due:
            customer_bucket["past_due_balance"] += balance
            total_past_due_balance += balance

    balances_by_seller = []
    for seller_name in sorted(grouped_balances):
        customer_entries = []
        seller_outstanding = Decimal("0")
        seller_past_due = Decimal("0")

        for customer_name in sorted(grouped_balances[seller_name]):
            bucket = grouped_balances[seller_name][customer_name]
            outstanding_balance = bucket["outstanding_balance"]
            past_due_balance = bucket["past_due_balance"]
            seller_outstanding += outstanding_balance
            seller_past_due += past_due_balance

            customer_entries.append(
                {
                    "customer_name": customer_name,
                    "invoice_count": bucket["invoice_count"],
                    "outstanding_balance": _format_decimal(outstanding_balance),
                    "past_due_balance": _format_decimal(past_due_balance),
                }
            )

        balances_by_seller.append(
            {
                "seller_name": seller_name,
                "customer_count": len(customer_entries),
                "outstanding_balance": _format_decimal(seller_outstanding),
                "past_due_balance": _format_decimal(seller_past_due),
                "customers": customer_entries,
            }
        )

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
            "resolved_files": resolved_files,
            "unresolved_files": unresolved_files,
            "valid_record_count": len(records),
            "records_in_metrics": records_in_metrics,
            "invalid_row_count": len(invalid_rows),
        },
        "balances_report": {
            "total_outstanding_balance": _format_decimal(total_outstanding_balance),
            "total_past_due_balance": _format_decimal(total_past_due_balance),
            "balances_by_seller": balances_by_seller,
        },
        "invalid_rows": invalid_row_payload,
    }
