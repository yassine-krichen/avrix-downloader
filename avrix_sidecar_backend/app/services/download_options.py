import os
import shutil
from typing import Callable


def resolve_ffmpeg_location() -> str | None:
    """Bundled ffmpeg (packaged builds set FFMPEG_PATH) takes priority over PATH."""
    bundled = os.environ.get("FFMPEG_PATH")
    if bundled and os.path.isfile(bundled):
        return bundled
    return shutil.which("ffmpeg")


def build_ydl_attempts(
    *,
    format_type: str,
    quality: str,
    download_policy: str,
    output_template: str,
    progress_hook: Callable[[dict], None],
    download_subtitles: bool,
    subtitle_languages: str,
    embed_thumbnail: bool,
    ffmpeg_location: str | None,
) -> list[dict]:
    """Build the ordered list of yt-dlp option sets to try for a download.

    strict_quality yields exactly one attempt with no fallback; best_effort
    appends a looser second attempt so transient 403s on the preferred
    format don't fail the whole download.
    """
    base_opts: dict = {
        "outtmpl": output_template,
        "progress_hooks": [progress_hook],
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "prefer_ffmpeg": True,
        "retries": 10,
        "fragment_retries": 10,
        "extractor_retries": 3,
        "file_access_retries": 3,
        "concurrent_fragment_downloads": 1,
        "skip_unavailable_fragments": download_policy == "best_effort",
    }

    if download_policy == "best_effort":
        base_opts["extractor_args"] = {
            "youtube": {
                "player_client": ["android", "web"],
            }
        }

    if download_subtitles:
        base_opts["writesubtitles"] = True
        base_opts["subtitleslangs"] = [lang.strip() for lang in subtitle_languages.split(",") if lang.strip()]

    if embed_thumbnail:
        base_opts["writethumbnail"] = True

    if ffmpeg_location:
        base_opts["ffmpeg_location"] = ffmpeg_location

    attempts: list[dict] = []

    if format_type == "mp3":
        postprocessors = [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3"}]
        attempts.append({"format": "bestaudio[ext=m4a]/bestaudio/best", "postprocessors": postprocessors})
        attempts.append({"format": "bestaudio/best", "postprocessors": postprocessors})
    else:
        if download_policy == "strict_quality" and not ffmpeg_location:
            raise RuntimeError("Strict quality video download requires ffmpeg in PATH")

        if quality == "best":
            preferred_format = "bestvideo+bestaudio"
        else:
            preferred_format = f"bestvideo[height<={quality.rstrip('p')}]+bestaudio"

        attempts.append({"format": preferred_format, "merge_output_format": "mp4"})

        if download_policy == "best_effort":
            attempts.append({"format": "best[ext=mp4]/best", "merge_output_format": "mp4"})

    return [{**base_opts, **attempt} for attempt in attempts]
