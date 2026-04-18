"""Settings persistence for the YouTube transcript saver application.

This module provides validated JSON load/save helpers for app settings,
including default values and basic schema validation.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DEFAULT_SETTINGS: dict[str, Any] = {
    "default_folder": str(Path.cwd()),
    "ask_every_time": False,
    "preferred_output_format": "txt",
}

ALLOWED_OUTPUT_FORMATS = {"txt", "md", "both"}


class SettingsValidationError(ValueError):
    """Raised when settings content is invalid."""


def validate_settings(settings: dict[str, Any]) -> dict[str, Any]:
    """Validate and normalize settings."""
    default_folder = settings.get(
        "default_folder",
        DEFAULT_SETTINGS["default_folder"],
    )
    ask_every_time = settings.get(
        "ask_every_time",
        DEFAULT_SETTINGS["ask_every_time"],
    )
    preferred_output_format = settings.get(
        "preferred_output_format",
        DEFAULT_SETTINGS["preferred_output_format"],
    )

    if not isinstance(default_folder, str) or not default_folder.strip():
        raise SettingsValidationError(
            "'default_folder' must be a non-empty string"
        )

    if not isinstance(ask_every_time, bool):
        raise SettingsValidationError("'ask_every_time' must be a boolean")

    if preferred_output_format not in ALLOWED_OUTPUT_FORMATS:
        allowed = ", ".join(sorted(ALLOWED_OUTPUT_FORMATS))
        raise SettingsValidationError(
            f"'preferred_output_format' must be one of: {allowed}"
        )

    return {
        "default_folder": default_folder,
        "ask_every_time": ask_every_time,
        "preferred_output_format": preferred_output_format,
    }


def load_settings(settings_path: str | Path) -> dict[str, Any]:
    """Load settings from JSON and recover to defaults on invalid content."""
    path = Path(settings_path)
    if not path.exists():
        return DEFAULT_SETTINGS.copy()

    try:
        with path.open("r", encoding="utf-8") as infile:
            data = json.load(infile)
        if not isinstance(data, dict):
            raise SettingsValidationError("Settings JSON must contain an object")
        merged = {**DEFAULT_SETTINGS, **data}
        return validate_settings(merged)
    except (OSError, json.JSONDecodeError, SettingsValidationError):
        recovered = DEFAULT_SETTINGS.copy()
        save_settings(path, recovered)
        return recovered


def save_settings(settings_path: str | Path, settings: dict[str, Any]) -> None:
    """Validate and persist settings as UTF-8 JSON."""
    validated = validate_settings(settings)
    path = Path(settings_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as outfile:
        json.dump(validated, outfile, indent=2, ensure_ascii=False)
        outfile.write("\n")
