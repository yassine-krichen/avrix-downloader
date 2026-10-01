import re
from typing import Callable

import yt_dlp

MAX_ERROR_LENGTH = 300

_ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")

# Ordered: first match wins. Needles are lowercase substrings of yt-dlp's message.
_FRIENDLY_HINTS: list[tuple[tuple[str, ...], str]] = [
    (
        ("sign in to confirm", "not a bot", "confirm your age", "sign in to view"),
        "The site is asking for a sign-in or bot check. Wait a while or switch network, then retry.",
    ),
    (
        ("ffmpeg is not installed", "ffmpeg not found", "ffprobe and ffmpeg", "requires ffmpeg"),
        "ffmpeg is missing, so this format cannot be merged or converted. Reinstall Avrix or install ffmpeg.",
    ),
    (
        ("video unavailable", "private video", "has been removed", "this video is not available", "no longer available"),
        "This video is unavailable (private, removed or region-blocked).",
    ),
    (
        ("requested format is not available",),
        "The chosen quality is not offered for this video. Try Best or a lower quality.",
    ),
    (
        ("http error 403", "forbidden"),
        "The site refused the download (HTTP 403). Retry later; updating Avrix may also help.",
    ),
    (
        ("unable to download", "getaddrinfo", "timed out", "connection"),
        "Network problem while contacting the site. Check your connection and retry.",
    ),
]


class DownloadCancelled(Exception):
    pass


def describe_download_error(exc: Exception) -> str:
    """Single-line, length-bounded error text safe to show in the UI (no traceback)."""
    raw = _ANSI_ESCAPE.sub("", str(exc)).strip()
    first_line = raw.splitlines()[0] if raw else type(exc).__name__
    detail = re.sub(r"^ERROR:\s*", "", first_line)
    lowered = raw.lower()

    message = detail
    for needles, hint in _FRIENDLY_HINTS:
        if any(needle in lowered for needle in needles):
            message = f"{hint} ({detail})"
            break

    if len(message) > MAX_ERROR_LENGTH:
        message = message[: MAX_ERROR_LENGTH - 3] + "..."
    return message


def run_ydl_attempts(
    attempts: list[dict],
    url: str,
    on_info: Callable[[dict], None],
) -> None:
    """Try each option set in order; the first success wins.

    Raises the last attempt's error if all fail. DownloadCancelled is never
    retried.
    """
    last_error: Exception | None = None

    for ydl_opts in attempts:
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                on_info(info if isinstance(info, dict) else {})
                ydl.download([url])
            return
        except DownloadCancelled:
            raise
        except Exception as exc:
            last_error = exc

    if last_error is not None:
        raise last_error
    raise RuntimeError("Download failed for unknown reason")
