"""Tkinter desktop UI for saving YouTube transcripts.

This module is intentionally limited to UI layout and event wiring.
Core logic for transcript retrieval, file output, and settings persistence
lives in service modules to keep future refactors straightforward.
"""

from __future__ import annotations

from pathlib import Path
import tkinter as tk
from tkinter import filedialog, ttk

from file_service import sanitize_filename, write_transcript_file
from settings import load_settings, save_settings
from transcript_service import (
    InvalidVideoSourceError,
    TranscriptBlockedError,
    TranscriptRequestError,
    TranscriptServiceError,
    TranscriptUnavailableError,
    fetch_transcript_text,
)

SETTINGS_FILE = Path("settings.json")


class TranscriptSaverApp:
    """Main Tkinter application class."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("YouTube Transcript Saver")
        self.root.geometry("700x320")

        self.settings = self._load_settings_safe()
        self._build_ui()

    def _load_settings_safe(self) -> dict[str, object]:
        return load_settings(SETTINGS_FILE)

    def _build_ui(self) -> None:
        container = ttk.Frame(self.root, padding=12)
        container.pack(fill="both", expand=True)

        ttk.Label(container, text="YouTube URL or video ID").pack(anchor="w")
        self.url_var = tk.StringVar()
        ttk.Entry(container, textvariable=self.url_var).pack(
            fill="x", pady=(0, 12)
        )

        format_row = ttk.Frame(container)
        format_row.pack(fill="x", pady=(0, 12))
        ttk.Label(format_row, text="Output format").pack(anchor="w")
        self.format_var = tk.StringVar(
            value=self.settings["preferred_output_format"]
        )
        self.format_combo = ttk.Combobox(
            format_row,
            textvariable=self.format_var,
            values=["txt", "md", "both"],
            state="readonly",
        )
        self.format_combo.pack(anchor="w")
        self.format_combo.bind("<<ComboboxSelected>>", self._on_settings_change)

        save_mode_row = ttk.Frame(container)
        save_mode_row.pack(fill="x", pady=(0, 12))
        ttk.Label(save_mode_row, text="Save mode").pack(anchor="w")
        self.save_mode_var = tk.StringVar(
            value=(
                "ask_every_time"
                if self.settings["ask_every_time"]
                else "default_folder"
            )
        )
        ttk.Radiobutton(
            save_mode_row,
            text="Ask every time",
            value="ask_every_time",
            variable=self.save_mode_var,
            command=self._on_save_mode_change,
        ).pack(anchor="w")
        ttk.Radiobutton(
            save_mode_row,
            text="Use default folder",
            value="default_folder",
            variable=self.save_mode_var,
            command=self._on_save_mode_change,
        ).pack(anchor="w")

        self.default_dir_row = ttk.Frame(container)
        self.default_dir_row.pack(fill="x", pady=(0, 12))
        ttk.Label(self.default_dir_row, text="Default folder").pack(anchor="w")
        dir_inner = ttk.Frame(self.default_dir_row)
        dir_inner.pack(fill="x")
        self.output_dir_var = tk.StringVar(
            value=self.settings["default_folder"]
        )
        self.default_dir_entry = ttk.Entry(
            dir_inner,
            textvariable=self.output_dir_var,
        )
        self.default_dir_entry.pack(side="left", fill="x", expand=True)
        self.default_dir_button = ttk.Button(
            dir_inner,
            text="Browse",
            command=self._choose_directory,
        )
        self.default_dir_button.pack(side="left", padx=(8, 0))

        self.save_button = ttk.Button(
            container,
            text="Save Transcript",
            command=self._on_save,
        )
        self.save_button.pack(anchor="w", pady=(0, 12))

        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(container, textvariable=self.status_var)
        self.status_label.pack(anchor="w")

        self._toggle_directory_inputs()

    def _toggle_directory_inputs(self) -> None:
        using_default = self.save_mode_var.get() == "default_folder"
        state = "normal" if using_default else "disabled"
        self.default_dir_entry.config(state=state)
        self.default_dir_button.config(state=state)

    def _choose_directory(self) -> None:
        try:
            selected = filedialog.askdirectory(
                initialdir=self.output_dir_var.get() or str(Path.cwd())
            )
            if selected:
                self.output_dir_var.set(selected)
                self._persist_settings()
                self._set_status("Default folder updated.")
        except Exception:
            self._set_error("Unable to open folder picker.")

    def _persist_settings(self) -> None:
        save_settings(
            SETTINGS_FILE,
            {
                "default_folder": self.output_dir_var.get().strip(),
                "ask_every_time": self.save_mode_var.get().strip()
                == "ask_every_time",
                "preferred_output_format": self.format_var.get().strip().lower(),
            },
        )

    def _on_save_mode_change(self) -> None:
        self._toggle_directory_inputs()
        try:
            self._persist_settings()
            self._set_status("Save mode updated.")
        except Exception as exc:
            self._set_error(self._status_message_for_error(exc))

    def _on_settings_change(self, _event: tk.Event) -> None:
        try:
            self._persist_settings()
            self._set_status("Output format updated.")
        except Exception as exc:
            self._set_error(self._status_message_for_error(exc))

    def _set_error(self, message: str) -> None:
        self.status_var.set(f"Error: {message}")

    def _set_status(self, message: str) -> None:
        self.status_var.set(message)

    def _status_message_for_error(self, exc: Exception) -> str:
        if isinstance(exc, InvalidVideoSourceError):
            return "Enter a valid YouTube URL or video ID."
        if isinstance(exc, TranscriptUnavailableError):
            return "Transcript unavailable for this video."
        if isinstance(exc, TranscriptBlockedError):
            return "Transcript blocked or disabled for this video."
        if isinstance(exc, TranscriptRequestError):
            return "Network/request failure while loading transcript."
        if isinstance(exc, ValueError):
            return str(exc)
        if isinstance(exc, TranscriptServiceError):
            return "Transcript could not be loaded."
        return "Unexpected error."

    def _resolve_output_directory(self) -> str:
        save_mode = self.save_mode_var.get().strip()
        if save_mode == "ask_every_time":
            selected = filedialog.askdirectory(initialdir=str(Path.cwd()))
            if not selected:
                raise ValueError("Save canceled")
            return selected

        output_dir = self.output_dir_var.get().strip()
        if not output_dir:
            raise ValueError("Please choose a default folder.")
        return output_dir

    def _on_save(self) -> None:
        source = self.url_var.get().strip()
        output_format = self.format_var.get().strip().lower()
        ask_every_time = self.save_mode_var.get().strip() == "ask_every_time"

        if not source:
            self._set_error("Please provide a YouTube URL or video ID.")
            return

        try:
            output_dir = self._resolve_output_directory()
            video_id, transcript_text = fetch_transcript_text(source)
            file_paths = write_transcript_file(
                output_directory=output_dir,
                filename_base=sanitize_filename(video_id),
                transcript_text=transcript_text,
                output_format=output_format,
            )
            if not ask_every_time:
                self.output_dir_var.set(output_dir)
            self._persist_settings()
        except Exception as exc:
            if isinstance(exc, ValueError) and str(exc) == "Save canceled":
                self._set_status("Save canceled")
                return
            self._set_error(self._status_message_for_error(exc))
            return

        saved_list = ", ".join(str(path) for path in file_paths)
        self._set_status(f"Saved: {saved_list}")


def main() -> None:
    """Run the Tkinter application."""
    root = tk.Tk()
    TranscriptSaverApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
