"""Unit tests for stable balance rules."""

from __future__ import annotations

import unittest
from datetime import date
from decimal import Decimal

from wholesail.domain.metrics import calculate_balance, is_outstanding, is_past_due
from wholesail.domain.models import InvalidRow, InvoiceRecord
from wholesail.reporting.summary_report import build_report_summary


class MetricsTests(unittest.TestCase):
    """Verify the core reporting formulas."""

    def test_balance_formula(self) -> None:
        record = InvoiceRecord(
            source_name="sample",
            invoice_id="inv-1",
            customer_name="customer-1",
            trans_amount=Decimal("100"),
            trans_date=date(2022, 1, 1),
            adjustment=Decimal("5"),
            term_schedule_days=30,
            paid_amount=Decimal("25"),
        )
        self.assertEqual(calculate_balance(record), Decimal("80"))

    def test_outstanding_balance(self) -> None:
        record = InvoiceRecord(
            source_name="sample",
            invoice_id="inv-2",
            customer_name="customer-1",
            trans_amount=Decimal("100"),
            trans_date=date(2022, 1, 1),
            adjustment=Decimal("0"),
            term_schedule_days=30,
            paid_amount=Decimal("10"),
        )
        self.assertTrue(is_outstanding(record))

    def test_past_due_balance(self) -> None:
        record = InvoiceRecord(
            source_name="sample",
            invoice_id="inv-3",
            customer_name="customer-1",
            trans_amount=Decimal("100"),
            trans_date=date(2022, 1, 1),
            adjustment=Decimal("0"),
            term_schedule_days=21,
            paid_amount=Decimal("0"),
        )
        self.assertTrue(is_past_due(record, as_of_date=date(2022, 3, 31)))

    def test_summary_groups_by_seller_and_customer(self) -> None:
        records = [
            InvoiceRecord(
                source_name="seller-a",
                invoice_id="inv-1",
                customer_name="buyer-1",
                trans_amount=Decimal("100"),
                trans_date=date(2022, 1, 1),
                adjustment=Decimal("0"),
                term_schedule_days=30,
                paid_amount=Decimal("20"),
            ),
            InvoiceRecord(
                source_name="seller-a",
                invoice_id="inv-2",
                customer_name="buyer-1",
                trans_amount=Decimal("50"),
                trans_date=date(2022, 3, 20),
                adjustment=Decimal("0"),
                term_schedule_days=30,
                paid_amount=Decimal("0"),
            ),
            InvoiceRecord(
                source_name="seller-a",
                invoice_id="inv-3",
                customer_name="buyer-2",
                trans_amount=Decimal("90"),
                trans_date=date(2022, 1, 10),
                adjustment=Decimal("10"),
                term_schedule_days=15,
                paid_amount=Decimal("50"),
            ),
            InvoiceRecord(
                source_name="seller-b",
                invoice_id="inv-4",
                customer_name="buyer-1",
                trans_amount=Decimal("500"),
                trans_date=date(2022, 1, 1),
                adjustment=Decimal("0"),
                term_schedule_days=30,
                paid_amount=Decimal("0"),
                status="voided",
            ),
        ]

        payload = build_report_summary(
            as_of_date=date(2022, 3, 31),
            records=records,
            invalid_rows=[
                InvalidRow(
                    source_name="seller-a",
                    file_name="sample.csv",
                    row_number=3,
                    errors=["Invoice id is required."],
                )
            ],
            source_count=2,
            discovered_files=2,
            resolved_files=[
                {"file": "a.csv", "source_name": "seller-a"},
                {"file": "b.csv", "source_name": "seller-b"},
            ],
            unresolved_files=[],
            excluded_statuses={"voided"},
        )

        self.assertEqual(payload["run_summary"]["valid_record_count"], 4)
        self.assertEqual(payload["run_summary"]["records_in_metrics"], 3)
        self.assertEqual(
            payload["balances_report"]["total_outstanding_balance"],
            "180.00",
        )
        self.assertEqual(
            payload["balances_report"]["total_past_due_balance"],
            "130.00",
        )
        self.assertEqual(len(payload["balances_report"]["balances_by_seller"]), 1)
        self.assertEqual(
            payload["balances_report"]["balances_by_seller"][0]["customers"][0]["customer_name"],
            "buyer-1",
        )
        self.assertEqual(
            payload["balances_report"]["balances_by_seller"][0]["customers"][0]["outstanding_balance"],
            "130.00",
        )
        self.assertEqual(
            payload["balances_report"]["balances_by_seller"][0]["customers"][0]["past_due_balance"],
            "80.00",
        )
        self.assertEqual(payload["run_summary"]["invalid_row_count"], 1)


if __name__ == "__main__":
    unittest.main()
