"""File and filename utilities for transcript export.

This module handles filename sanitization and UTF-8 writing to text and
markdown files used by the transcript saver application.
"""

from __future__ import annotations

import re
from pathlib import Path

INVALID_FILENAME_CHARS = r'[<>:"/\\|?*\x00-\x1F]'
ALLOWED_OUTPUT_FORMATS = {"txt", "md", "both"}


def sanitize_filename(name: str, fallback: str = "transcript") -> str:
    """Convert arbitrary text into a filesystem-safe filename base."""
    cleaned = re.sub(INVALID_FILENAME_CHARS, "_", name)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" .")
    return cleaned or fallback


def write_transcript_file(
    output_directory: str | Path,
    filename_base: str,
    transcript_text: str,
    output_format: str,
) -> list[Path]:
    """Write transcript content as UTF-8 .txt/.md files and return paths."""
    normalized_format = output_format.lower().strip()
    if normalized_format not in ALLOWED_OUTPUT_FORMATS:
        raise ValueError("output_format must be 'txt', 'md', or 'both'")

    file_extensions = ["txt", "md"] if normalized_format == "both" else [
        normalized_format
    ]

    safe_base = sanitize_filename(filename_base)
    destination_dir = Path(output_directory)
    destination_dir.mkdir(parents=True, exist_ok=True)

    saved_paths: list[Path] = []
    for extension in file_extensions:
        destination = destination_dir / f"{safe_base}.{extension}"
        with destination.open("w", encoding="utf-8") as outfile:
            outfile.write(transcript_text)
        saved_paths.append(destination)

    return saved_paths
