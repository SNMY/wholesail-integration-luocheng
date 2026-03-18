"""Tests for config-driven row mapping."""

from __future__ import annotations

import unittest
from decimal import Decimal

from wholesail.domain.models import FieldMapping, SourceConfig
from wholesail.ingestion.row_mapper import map_row_to_invoice


class MappingTests(unittest.TestCase):
    """Verify that source-specific rows map into the canonical model."""

    def test_happy_fruits_amount_is_converted_from_cents(self) -> None:
        config = SourceConfig(
            source_name="happy_fruits",
            filename_patterns=["*happy-fruits*.csv"],
            required_headers=[],
            fields={
                "invoice_id": FieldMapping(source="invoiceId"),
                "customer_name": FieldMapping(source="buyer"),
                "trans_amount": FieldMapping(
                    source="transAmountCents", transform="cents_to_decimal"
                ),
                "trans_date": FieldMapping(source="transDate", transform="iso_date"),
                "adjustment": FieldMapping(
                    source="adjustmentAmountCents", transform="cents_to_decimal", default="0"
                ),
                "term_schedule_days": FieldMapping(
                    source="paymentTerm", transform="integer"
                ),
                "paid_amount": FieldMapping(
                    source="paidAmountCents", transform="cents_to_decimal", default="0"
                ),
                "paid_at": FieldMapping(source="paidAt", transform="iso_date_nullable"),
                "note": FieldMapping(source="memo"),
            },
            status_markers=["VOIDED"],
        )

        row = {
            "invoiceId": "hf-1",
            "buyer": "buyer-2",
            "transAmountCents": "10000",
            "transDate": "2021-12-31",
            "adjustmentAmountCents": "-538",
            "paymentTerm": "21",
            "paidAmountCents": "",
            "paidAt": "",
            "memo": "some-other-memo-1",
        }

        record = map_row_to_invoice(row, config)

        self.assertEqual(record.invoice_id, "hf-1")
        self.assertEqual(record.customer_name, "buyer-2")
        self.assertEqual(record.trans_amount, Decimal("100"))
        self.assertEqual(record.adjustment, Decimal("-5.38"))
        self.assertEqual(record.paid_amount, Decimal("0"))
        self.assertIsNone(record.status)

    def test_status_is_derived_from_note_markers(self) -> None:
        config = SourceConfig(
            source_name="golden_gate_produce",
            filename_patterns=["*golden-gate-produce*.csv"],
            required_headers=[],
            fields={
                "invoice_id": FieldMapping(source="id"),
                "customer_name": FieldMapping(source="customer"),
                "trans_amount": FieldMapping(source="amount", transform="decimal"),
                "trans_date": FieldMapping(source="date", transform="iso_date"),
                "adjustment": FieldMapping(source="adjustment", transform="decimal", default="0"),
                "term_schedule_days": FieldMapping(source="term_schedule", transform="integer"),
                "paid_amount": FieldMapping(source="paid_amount", transform="decimal", default="0"),
                "paid_at": FieldMapping(source="paid_at", transform="iso_date_nullable"),
                "note": FieldMapping(source="note"),
            },
            status_markers=["VOIDED"],
        )

        row = {
            "id": "id-7",
            "customer": "customer-0",
            "amount": "700",
            "date": "2022-01-01",
            "adjustment": "-53",
            "term_schedule": "21",
            "paid_amount": "",
            "paid_at": "",
            "note": "VOIDED",
        }

        record = map_row_to_invoice(row, config)

        self.assertEqual(record.status, "voided")


if __name__ == "__main__":
    unittest.main()
