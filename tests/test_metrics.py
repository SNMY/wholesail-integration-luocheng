"""Unit tests for stable balance rules."""

from __future__ import annotations

import unittest
from datetime import date
from decimal import Decimal

from wholesail.domain.metrics import calculate_balance, is_outstanding, is_past_due
from wholesail.domain.models import InvalidRow, InvoiceRecord
from wholesail.reporting.summary_report import build_customer_balance_rows, build_run_summary


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

    def test_customer_balance_rows_group_by_customer(self) -> None:
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
                source_name="seller-a",
                invoice_id="inv-4",
                customer_name="buyer-3",
                trans_amount=Decimal("500"),
                trans_date=date(2022, 1, 1),
                adjustment=Decimal("0"),
                term_schedule_days=30,
                paid_amount=Decimal("0"),
                status="voided",
            ),
        ]

        rows = build_customer_balance_rows(
            as_of_date=date(2022, 3, 31),
            records=records,
            excluded_statuses={"voided"},
        )

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["customer"], "buyer-1")
        self.assertEqual(rows[0]["outstanding_balance"], "130.00")
        self.assertEqual(rows[0]["past_due_balance"], "80.00")
        self.assertEqual(rows[1]["customer"], "buyer-2")
        self.assertEqual(rows[1]["outstanding_balance"], "50.00")
        self.assertEqual(rows[1]["past_due_balance"], "50.00")

    def test_run_summary_tracks_generated_reports(self) -> None:
        payload = build_run_summary(
            as_of_date=date(2022, 3, 31),
            source_count=2,
            discovered_files=2,
            generated_reports=[
                {
                    "input_file": "a.csv",
                    "source_name": "seller-a",
                    "output_file": "a-report.csv",
                    "customer_count": 2,
                    "valid_record_count": 3,
                }
            ],
            unresolved_files=["b.csv"],
            invalid_rows=[
                InvalidRow(
                    source_name="seller-a",
                    file_name="a.csv",
                    row_number=3,
                    errors=["Invoice id is required."],
                )
            ],
            file_errors=[
                {
                    "file_name": "c.csv",
                    "source_name": "seller-c",
                    "error": "Permission denied",
                }
            ],
        )

        self.assertEqual(payload["run_summary"]["generated_report_count"], 1)
        self.assertEqual(payload["run_summary"]["invalid_row_count"], 1)
        self.assertEqual(payload["run_summary"]["file_error_count"], 1)
        self.assertEqual(payload["run_summary"]["unresolved_files"], ["b.csv"])


if __name__ == "__main__":
    unittest.main()
