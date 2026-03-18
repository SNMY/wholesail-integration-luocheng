"""Resolve which source configuration matches a CSV file."""

from __future__ import annotations

from fnmatch import fnmatch
from pathlib import Path

from wholesail.domain.models import SourceConfig
from wholesail.ingestion.csv_reader import read_csv_headers


def resolve_source(path: Path, configs: list[SourceConfig]) -> SourceConfig | None:
    """Find the first config whose filename pattern and headers match the file."""
    headers = set(read_csv_headers(path))
    filename = path.name

    for config in configs:
        pattern_match = any(fnmatch(filename, pattern) for pattern in config.filename_patterns)
        header_match = set(config.required_headers).issubset(headers)
        if pattern_match and header_match:
            return config

    for config in configs:
        header_match = set(config.required_headers).issubset(headers)
        if header_match:
            return config

    return None
