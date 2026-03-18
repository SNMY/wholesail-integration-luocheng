"""Map raw source rows into canonical invoice records."""

from __future__ import annotations

from collections.abc import Mapping

from wholesail.domain.models import InvoiceRecord, SourceConfig
from wholesail.ingestion.converters import apply_transform, to_text


def _extract_status(note: str | None, config: SourceConfig) -> str | None:
    """Return a normalized status when the note matches a configured marker."""
    normalized_note = to_text(note)
    if normalized_note is None:
        return None

    markers = {marker.upper(): marker.lower() for marker in config.status_markers}
    return markers.get(normalized_note.upper())


def map_row_to_invoice(row: Mapping[str, str], config: SourceConfig) -> InvoiceRecord:
    """Map one raw CSV row into the canonical invoice shape."""
    mapped_values: dict[str, object] = {"source_name": config.source_name}

    for canonical_name, field_mapping in config.fields.items():
        raw_value = row.get(field_mapping.source)
        mapped_values[canonical_name] = apply_transform(
            field_mapping.transform, raw_value, field_mapping.default
        )

    note = to_text(mapped_values.get("note"))
    mapped_values["note"] = note
    mapped_values["status"] = _extract_status(note, config)

    return InvoiceRecord(
        source_name=config.source_name,
        invoice_id=to_text(mapped_values.get("invoice_id"), default="") or "",
        customer_name=to_text(mapped_values.get("customer_name"), default="") or "",
        trans_amount=mapped_values["trans_amount"],
        trans_date=mapped_values["trans_date"],
        adjustment=mapped_values["adjustment"],
        term_schedule_days=mapped_values["term_schedule_days"],
        paid_amount=mapped_values["paid_amount"],
        paid_at=mapped_values.get("paid_at"),
        billing_address=to_text(mapped_values.get("billing_address")),
        shipping_address=to_text(mapped_values.get("shipping_address")),
        raw_items_json=to_text(mapped_values.get("raw_items_json")),
        note=note,
        status=to_text(mapped_values.get("status")),
    )
