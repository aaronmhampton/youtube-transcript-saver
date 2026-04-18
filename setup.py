"""Packaging metadata for youtube-transcript-saver."""

from setuptools import setup

setup(
    name="youtube-transcript-saver",
    version="0.1.0",
    description="Tkinter app to fetch and save YouTube transcripts",
    py_modules=["app", "transcript_service", "file_service", "settings"],
    install_requires=["youtube-transcript-api>=0.6.2,<1.0.0"],
)
