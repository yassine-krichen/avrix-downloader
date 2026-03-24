from pathlib import Path
from typing import Literal, Optional

from pydantic import BaseModel, Field, model_validator


Quality = Literal["best", "2160p", "1440p", "1080p", "720p", "480p", "360p", "240p", "144p"]
FormatType = Literal["mp3", "mp4"]
ThemeMode = Literal["light", "dark"]
DownloadPolicy = Literal["best_effort", "strict_quality"]


class AppSettings(BaseModel):
    download_path: str = Field(default_factory=lambda: str(Path.home() / "Downloads" / "Avrix"))
    format_type: FormatType = "mp4"
    quality: Quality = "best"
    last_url: str = ""
    download_subtitles: bool = False
    subtitle_languages: str = "en"
    embed_thumbnail: bool = False
    notifications_enabled: bool = True
    max_concurrent_downloads: int = Field(default=3, ge=1, le=10)
    theme: ThemeMode = "light"
    download_policy: DownloadPolicy = "best_effort"


class SettingsPatchRequest(BaseModel):
    download_path: Optional[str] = None
    format_type: Optional[FormatType] = None
    quality: Optional[Quality] = None
    last_url: Optional[str] = None
    download_subtitles: Optional[bool] = None
    subtitle_languages: Optional[str] = None
    embed_thumbnail: Optional[bool] = None
    notifications_enabled: Optional[bool] = None
    max_concurrent_downloads: Optional[int] = Field(default=None, ge=1, le=10)
    theme: Optional[ThemeMode] = None
    download_policy: Optional[DownloadPolicy] = None

    @model_validator(mode="after")
    def validate_non_empty_patch(self):
        if not self.model_dump(exclude_none=True):
            raise ValueError("At least one setting must be provided")
        return self
