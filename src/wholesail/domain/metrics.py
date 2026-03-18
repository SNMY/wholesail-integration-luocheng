"""Balance calculation helpers."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from wholesail.domain.models import InvoiceRecord


def calculate_balance(record: InvoiceRecord) -> Decimal:
    """Calculate the invoice balance from canonical fields."""
    return record.trans_amount + record.adjustment - record.paid_amount


def is_outstanding(record: InvoiceRecord) -> bool:
    """Return True when a record has a positive remaining balance."""
    return calculate_balance(record) > Decimal("0")


def is_past_due(record: InvoiceRecord, as_of_date: date) -> bool:
    """Return True when an outstanding invoice is older than its term schedule."""
    due_date = record.trans_date + timedelta(days=record.term_schedule_days)
    return is_outstanding(record) and due_date < as_of_date
