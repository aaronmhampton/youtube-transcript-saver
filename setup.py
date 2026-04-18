"""py2app setup script for youtube-transcript-saver."""

from setuptools import setup

APP = ["app.py"]
OPTIONS = {
    "argv_emulation": False,
    "plist": {
        "CFBundleName": "YouTube Transcript Saver",
        "CFBundleDisplayName": "YouTube Transcript Saver",
        "CFBundleIdentifier": "com.example.youtube-transcript-saver",
        "CFBundleVersion": "0.1.0",
        "CFBundleShortVersionString": "0.1.0",
    },
}

setup(
    app=APP,
    name="youtube-transcript-saver",
    version="0.1.0",
    description="Tkinter app to fetch and save YouTube transcripts",
    options={"py2app": OPTIONS},
    setup_requires=["py2app>=0.28.8,<1.0.0"],
    install_requires=["youtube-transcript-api>=0.6.2,<1.0.0"],
)
