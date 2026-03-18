"""Domain models shared across ingestion and reporting."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Any


@dataclass(slots=True)
class FieldMapping:
    """Describe how a source field maps into a canonical field."""

    source: str
    transform: str | None = None
    default: Any = None


@dataclass(slots=True)
class SourceConfig:
    """Store provider-specific mapping and matching rules."""

    source_name: str
    filename_patterns: list[str]
    required_headers: list[str]
    fields: dict[str, FieldMapping]
    status_markers: list[str] = field(default_factory=list)
    metrics_excluded_statuses: list[str] = field(default_factory=list)


@dataclass(slots=True)
class InvoiceRecord:
    """Canonical invoice shape used by downstream business logic."""

    source_name: str
    invoice_id: str
    customer_name: str
    trans_amount: Decimal
    trans_date: date
    adjustment: Decimal
    term_schedule_days: int
    paid_amount: Decimal
    paid_at: date | None = None
    billing_address: str | None = None
    shipping_address: str | None = None
    raw_items_json: str | None = None
    note: str | None = None
    status: str | None = None


@dataclass(slots=True)
class ValidationIssue:
    """Represent a row-level validation problem."""

    row_number: int
    field_name: str
    message: str
    severity: str = "error"


@dataclass(slots=True)
class InvalidRow:
    """Capture row-level errors while keeping the full run alive."""

    source_name: str
    file_name: str
    row_number: int
    errors: list[str]
