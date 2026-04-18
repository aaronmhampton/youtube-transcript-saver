"""YouTube transcript retrieval helpers.

This module handles URL parsing, video ID extraction, and transcript fetching
through the `youtube-transcript-api` package.
"""

from __future__ import annotations

from urllib.parse import parse_qs, urlparse

from youtube_transcript_api import YouTubeTranscriptApi


class TranscriptServiceError(Exception):
    """Base error type for transcript service failures."""


def extract_video_id(url_or_id: str) -> str:
    """Extract a YouTube video ID from a URL or return the ID directly."""
    raw = url_or_id.strip()
    if not raw:
        raise TranscriptServiceError(
            "Please provide a YouTube URL or video ID."
        )

    if len(raw) == 11 and "/" not in raw and "?" not in raw:
        return raw

    parsed = urlparse(raw)
    host = parsed.netloc.lower()
    path = parsed.path.strip("/")

    if "youtube.com" in host:
        if path == "watch":
            video_ids = parse_qs(parsed.query).get("v")
            if video_ids and video_ids[0]:
                return video_ids[0]
        elif path.startswith("shorts/"):
            candidate = path.split("/", 1)[1]
            if candidate:
                return candidate[:11]
    elif "youtu.be" in host and path:
        return path.split("/")[0][:11]

    raise TranscriptServiceError("Could not parse a valid YouTube video ID.")


def fetch_transcript_text(url_or_id: str) -> tuple[str, str]:
    """Fetch and flatten transcript text from a YouTube URL or video ID."""
    try:
        video_id = extract_video_id(url_or_id)
        transcript_segments = YouTubeTranscriptApi.get_transcript(video_id)
    except Exception as exc:
        if isinstance(exc, TranscriptServiceError):
            raise
        raise TranscriptServiceError(str(exc)) from exc

    transcript_text = "\n".join(
        segment.get("text", "") for segment in transcript_segments
    ).strip()
    if not transcript_text:
        raise TranscriptServiceError("Transcript was empty.")

    return video_id, transcript_text
