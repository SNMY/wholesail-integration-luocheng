"""CSV file discovery and reading helpers."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


def discover_csv_files(input_dir: Path) -> list[Path]:
    """Return all CSV files found in the input directory."""
    if not input_dir.exists():
        return []
    return sorted(input_dir.glob("*.csv"))


def read_csv_headers(path: Path) -> list[str]:
    """Read only the header row from a CSV file."""
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        return next(reader, [])


def read_csv_rows(path: Path) -> list[dict[str, Any]]:
    """Read a CSV file into a list of dictionaries."""
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader)
