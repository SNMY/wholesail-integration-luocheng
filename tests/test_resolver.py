"""Tests for source resolution against headers and file names."""

from __future__ import annotations

import shutil
import unittest
from pathlib import Path

from wholesail.domain.models import FieldMapping, SourceConfig
from wholesail.ingestion.source_resolver import resolve_source


class ResolverTests(unittest.TestCase):
    """Verify source matching behavior."""

    def test_resolve_source_matches_header_and_filename(self) -> None:
        config = SourceConfig(
            source_name="golden_gate_produce",
            filename_patterns=["*golden-gate-produce*.csv"],
            required_headers=["id", "customer", "amount"],
            fields={"invoice_id": FieldMapping(source="id")},
        )

        temp_dir = Path("data/output/test-temp")
        temp_dir.mkdir(parents=True, exist_ok=True)
        path = temp_dir / "data-golden-gate-produce-10.csv"

        try:
            path.write_text("id,customer,amount\n1,customer-1,100\n", encoding="utf-8")
            resolved = resolve_source(path, [config])
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

        self.assertIsNotNone(resolved)
        self.assertEqual(resolved.source_name, "golden_gate_produce")


if __name__ == "__main__":
    unittest.main()
