"""YouTube transcript retrieval helpers.

This module handles URL parsing, video ID extraction, and transcript fetching
through the `youtube-transcript-api` package.
"""

from __future__ import annotations

from urllib.parse import parse_qs, urlparse

from youtube_transcript_api import YouTubeTranscriptApi


class TranscriptServiceError(Exception):
    """Base error type for transcript service failures."""


class InvalidVideoSourceError(TranscriptServiceError):
    """Raised when a YouTube URL/ID is missing or invalid."""


class TranscriptUnavailableError(TranscriptServiceError):
    """Raised when a transcript cannot be found or is empty."""


class TranscriptBlockedError(TranscriptServiceError):
    """Raised when transcripts are disabled or access is blocked."""


class TranscriptRequestError(TranscriptServiceError):
    """Raised when transcript retrieval fails due to request/network issues."""


def extract_video_id(url_or_id: str) -> str:
    """Extract a YouTube video ID from a URL or return the ID directly."""
    raw = url_or_id.strip()
    if not raw:
        raise InvalidVideoSourceError(
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

    raise InvalidVideoSourceError("Could not parse a valid YouTube video ID.")


def fetch_transcript_text(url_or_id: str) -> tuple[str, str]:
    """Fetch and flatten transcript text from a YouTube URL or video ID."""
    try:
        video_id = extract_video_id(url_or_id)
        transcript_segments = YouTubeTranscriptApi.get_transcript(video_id)
    except InvalidVideoSourceError:
        raise
    except Exception as exc:
        exc_name = exc.__class__.__name__.lower()
        exc_text = str(exc).lower()
        signature = f"{exc_name} {exc_text}"

        if any(
            marker in signature
            for marker in (
                "transcriptsdisabled",
                "disabled",
                "requestblocked",
                "ipblocked",
                "blocked",
                "forbidden",
            )
        ):
            raise TranscriptBlockedError(
                "Transcript access is blocked or disabled for this video."
            ) from exc

        if any(
            marker in signature
            for marker in (
                "notranscript",
                "transcriptnotfound",
                "videounavailable",
                "unavailable",
                "agerequired",
                "agerestricted",
                "privatevideo",
            )
        ):
            raise TranscriptUnavailableError(
                "Transcript is unavailable for this video."
            ) from exc

        if any(
            marker in signature
            for marker in (
                "youtube request failed",
                "requestfailed",
                "toomanyrequests",
                "timeout",
                "connection",
                "network",
                "http",
            )
        ):
            raise TranscriptRequestError(
                "Unable to reach YouTube transcript service right now."
            ) from exc

        raise TranscriptRequestError(
            "Unexpected transcript retrieval failure."
        ) from exc

    transcript_text = "\n".join(
        segment.get("text", "") for segment in transcript_segments
    ).strip()
    if not transcript_text:
        raise TranscriptUnavailableError("Transcript was empty.")

    return video_id, transcript_text
