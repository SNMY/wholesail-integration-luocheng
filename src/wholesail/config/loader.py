"""Helpers for loading source configuration files."""

from __future__ import annotations

import tomllib
from pathlib import Path

from wholesail.domain.models import FieldMapping, SourceConfig


def load_source_configs(config_dir: Path) -> list[SourceConfig]:
    """Load every TOML source configuration from the target directory."""
    configs: list[SourceConfig] = []
    if not config_dir.exists():
        return configs

    for path in sorted(config_dir.glob("*.toml")):
        with path.open("rb") as handle:
            data = tomllib.load(handle)

        fields = {
            canonical_name: FieldMapping(
                source=details["source"],
                transform=details.get("transform"),
                default=details.get("default"),
            )
            for canonical_name, details in data.get("fields", {}).items()
        }

        config = SourceConfig(
            source_name=data["source_name"],
            filename_patterns=data.get("match", {}).get("filename_patterns", []),
            required_headers=data.get("match", {}).get("required_headers", []),
            fields=fields,
            status_markers=data.get("rules", {}).get("status_markers", []),
            metrics_excluded_statuses=data.get("rules", {}).get(
                "metrics_excluded_statuses", []
            ),
        )
        configs.append(config)

    return configs
