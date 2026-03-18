"""Transform raw source values into canonical Python values."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any


def to_decimal(value: str | int | float | None, default: str = "0") -> Decimal:
    """Convert a raw value into a Decimal, using a string default when empty."""
    if value in (None, ""):
        return Decimal(default)
    return Decimal(str(value))


def cents_to_decimal(value: str | int | float | None, default: str = "0") -> Decimal:
    """Convert integer cents into a Decimal amount in the main currency unit."""
    cents = to_decimal(value, default=default)
    return cents / Decimal("100")


def to_int(value: str | int | None, default: int = 0) -> int:
    """Convert a raw value into an integer."""
    if value in (None, ""):
        return default
    return int(value)


def to_date(value: str | None) -> date | None:
    """Convert an ISO date string into a date, or None when empty."""
    if value in (None, ""):
        return None
    return date.fromisoformat(value)


def to_text(value: Any, default: str | None = None) -> str | None:
    """Normalize text values, returning None for blank input."""
    if value is None:
        return default
    text = str(value).strip()
    if text == "":
        return default
    return text


def apply_transform(
    transform: str | None,
    raw_value: Any,
    default: Any = None,
) -> Any:
    """Apply a named transform from source config metadata."""
    if transform is None:
        return raw_value if raw_value not in ("", None) else default
    if transform == "decimal":
        fallback = "0" if default is None else str(default)
        return to_decimal(raw_value, default=fallback)
    if transform == "cents_to_decimal":
        fallback = "0" if default is None else str(default)
        return cents_to_decimal(raw_value, default=fallback)
    if transform == "integer":
        fallback = 0 if default is None else int(default)
        return to_int(raw_value, default=fallback)
    if transform in {"iso_date", "iso_date_nullable"}:
        return to_date(raw_value)
    if transform == "string":
        fallback = None if default is None else str(default)
        return to_text(raw_value, default=fallback)
    raise ValueError(f"Unsupported transform '{transform}'.")
