"""Validation helpers for canonical invoice records."""

from __future__ import annotations

from decimal import Decimal

from wholesail.domain.models import InvoiceRecord, ValidationIssue


def validate_invoice(record: InvoiceRecord, row_number: int) -> list[ValidationIssue]:
    """Validate a canonical invoice record."""
    issues: list[ValidationIssue] = []

    if not record.invoice_id:
        issues.append(ValidationIssue(row_number, "invoice_id", "Invoice id is required."))
    if not record.customer_name:
        issues.append(
            ValidationIssue(row_number, "customer_name", "Customer name is required.")
        )
    if record.trans_date is None:
        issues.append(ValidationIssue(row_number, "trans_date", "Transaction date is required."))
    if record.trans_amount < Decimal("0"):
        issues.append(
            ValidationIssue(row_number, "trans_amount", "Transaction amount cannot be negative.")
        )
    if record.term_schedule_days < 0:
        issues.append(
            ValidationIssue(
                row_number,
                "term_schedule_days",
                "Term schedule must be zero or greater.",
            )
        )
    if record.paid_amount < Decimal("0"):
        issues.append(
            ValidationIssue(row_number, "paid_amount", "Paid amount cannot be negative.")
        )

    return issues
