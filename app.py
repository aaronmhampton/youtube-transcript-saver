"""Tkinter desktop UI for saving YouTube transcripts.

This module is intentionally limited to UI layout and event wiring.
Core logic for transcript retrieval, file output, and settings persistence
lives in service modules to keep future refactors straightforward.
"""

from __future__ import annotations

from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from file_service import sanitize_filename, write_transcript_file
from settings import SettingsValidationError, load_settings, save_settings
from transcript_service import TranscriptServiceError, fetch_transcript_text

SETTINGS_FILE = Path("settings.json")


class TranscriptSaverApp:
    """Main Tkinter application class."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("YouTube Transcript Saver")
        self.root.geometry("700x480")

        self.settings = self._load_settings_safe()
        self._build_ui()

    def _load_settings_safe(self) -> dict[str, str]:
        try:
            return load_settings(SETTINGS_FILE)
        except SettingsValidationError:
            return {
                "output_directory": str(Path.cwd()),
                "output_format": "txt",
            }

    def _build_ui(self) -> None:
        container = ttk.Frame(self.root, padding=12)
        container.pack(fill="both", expand=True)

        ttk.Label(container, text="YouTube URL or video ID").pack(anchor="w")
        self.url_var = tk.StringVar()
        ttk.Entry(container, textvariable=self.url_var).pack(
            fill="x", pady=(0, 12)
        )

        output_row = ttk.Frame(container)
        output_row.pack(fill="x", pady=(0, 12))
        ttk.Label(output_row, text="Output directory").pack(anchor="w")
        dir_inner = ttk.Frame(output_row)
        dir_inner.pack(fill="x")
        self.output_dir_var = tk.StringVar(
            value=self.settings["output_directory"]
        )
        ttk.Entry(
            dir_inner,
            textvariable=self.output_dir_var,
        ).pack(side="left", fill="x", expand=True)
        ttk.Button(
            dir_inner,
            text="Browse",
            command=self._choose_directory,
        ).pack(side="left", padx=(8, 0))

        format_row = ttk.Frame(container)
        format_row.pack(fill="x", pady=(0, 12))
        ttk.Label(format_row, text="Output format").pack(anchor="w")
        self.format_var = tk.StringVar(value=self.settings["output_format"])
        ttk.Combobox(
            format_row,
            textvariable=self.format_var,
            values=["txt", "md"],
            state="readonly",
        ).pack(anchor="w")

        self.save_button = ttk.Button(
            container,
            text="Fetch + Save Transcript",
            command=self._on_save,
        )
        self.save_button.pack(anchor="w", pady=(0, 12))

        ttk.Label(container, text="Transcript preview").pack(anchor="w")
        self.preview_text = tk.Text(container, wrap="word", height=14)
        self.preview_text.pack(fill="both", expand=True)

    def _choose_directory(self) -> None:
        selected = filedialog.askdirectory(
            initialdir=self.output_dir_var.get() or str(Path.cwd())
        )
        if selected:
            self.output_dir_var.set(selected)

    def _on_save(self) -> None:
        source = self.url_var.get().strip()
        output_dir = self.output_dir_var.get().strip()
        output_format = self.format_var.get().strip().lower()

        if not source:
            messagebox.showerror(
                "Missing input",
                "Please provide a YouTube URL or video ID.",
            )
            return

        if not output_dir:
            messagebox.showerror(
                "Missing output directory",
                "Please choose an output directory.",
            )
            return

        try:
            video_id, transcript_text = fetch_transcript_text(source)
            file_path = write_transcript_file(
                output_directory=output_dir,
                filename_base=sanitize_filename(video_id),
                transcript_text=transcript_text,
                output_format=output_format,
            )
            save_settings(
                SETTINGS_FILE,
                {
                    "output_directory": output_dir,
                    "output_format": output_format,
                },
            )
        except (
            TranscriptServiceError,
            ValueError,
            SettingsValidationError,
        ) as exc:
            messagebox.showerror("Error", str(exc))
            return

        self.preview_text.delete("1.0", tk.END)
        self.preview_text.insert(tk.END, transcript_text)
        messagebox.showinfo("Saved", f"Transcript saved to:\n{file_path}")


def main() -> None:
    """Run the Tkinter application."""
    root = tk.Tk()
    TranscriptSaverApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
