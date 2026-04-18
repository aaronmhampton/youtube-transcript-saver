"""Settings persistence for the YouTube transcript saver application.

This module provides validated JSON load/save helpers for app settings,
including default values and basic schema validation.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DEFAULT_SETTINGS: dict[str, Any] = {
    "output_directory": str(Path.cwd()),
    "output_format": "txt",
}

ALLOWED_OUTPUT_FORMATS = {"txt", "md"}


class SettingsValidationError(ValueError):
    """Raised when settings content is invalid."""


def validate_settings(settings: dict[str, Any]) -> dict[str, Any]:
    """Validate and normalize settings."""
    output_directory = settings.get(
        "output_directory",
        DEFAULT_SETTINGS["output_directory"],
    )
    output_format = settings.get(
        "output_format",
        DEFAULT_SETTINGS["output_format"],
    )

    if not isinstance(output_directory, str) or not output_directory.strip():
        raise SettingsValidationError(
            "'output_directory' must be a non-empty string"
        )

    if output_format not in ALLOWED_OUTPUT_FORMATS:
        allowed = ", ".join(sorted(ALLOWED_OUTPUT_FORMATS))
        raise SettingsValidationError(
            f"'output_format' must be one of: {allowed}"
        )

    return {
        "output_directory": output_directory,
        "output_format": output_format,
    }


def load_settings(settings_path: str | Path) -> dict[str, Any]:
    """Load settings from JSON; return defaults if the file is absent."""
    path = Path(settings_path)
    if not path.exists():
        return DEFAULT_SETTINGS.copy()

    with path.open("r", encoding="utf-8") as infile:
        data = json.load(infile)

    if not isinstance(data, dict):
        raise SettingsValidationError("Settings JSON must contain an object")

    merged = {**DEFAULT_SETTINGS, **data}
    return validate_settings(merged)


def save_settings(settings_path: str | Path, settings: dict[str, Any]) -> None:
    """Validate and persist settings as UTF-8 JSON."""
    validated = validate_settings(settings)
    path = Path(settings_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as outfile:
        json.dump(validated, outfile, indent=2, ensure_ascii=False)
        outfile.write("\n")
