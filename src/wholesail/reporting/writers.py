"""Output helpers for report artifacts."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


def write_json_report(path: Path, payload: dict[str, Any]) -> None:
    """Write a JSON report and create parent directories if needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_csv_report(path: Path, rows: list[dict[str, str]]) -> None:
    """Write a CSV report and create parent directories if needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["customer", "outstanding_balance", "past_due_balance"]

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
