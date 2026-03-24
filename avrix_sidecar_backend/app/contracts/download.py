from typing import Literal

from pydantic import BaseModel

from app.contracts.settings import FormatType, Quality


class CurrentDownloadStartRequest(BaseModel):
    url: str
    format_type: FormatType
    quality: Quality
    download_path: str
    download_subtitles: bool = False
    subtitle_languages: str = "en"
    embed_thumbnail: bool = False


DownloadStatus = Literal["idle", "starting", "downloading", "completed", "failed", "cancelled"]


class CurrentDownloadState(BaseModel):
    running: bool = False
    status: DownloadStatus = "idle"
    url: str = ""
    title: str | None = None
    thumbnail_url: str | None = None
    progress: float = 0.0
    downloaded_bytes: int = 0
    total_bytes: int = 0
    speed_bps: float = 0.0
    eta_seconds: int = 0
    error_message: str | None = None
