from datetime import datetime, timezone
from enum import Enum
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field

from app.contracts.settings import FormatType, Quality


class QueueItemStatus(str, Enum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class QueueItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    url: str
    status: QueueItemStatus = QueueItemStatus.PENDING
    format_type: FormatType
    quality: Quality
    progress: float = 0.0

    download_path: str
    download_subtitles: bool = False
    subtitle_languages: str = "en"
    embed_thumbnail: bool = False

    title: str | None = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class QueueCreateRequest(BaseModel):
    url: str
    format_type: FormatType
    quality: Quality
    download_path: str
    download_subtitles: bool = False
    subtitle_languages: str = "en"
    embed_thumbnail: bool = False


class QueueMoveRequest(BaseModel):
    direction: Literal["up", "down"]


class QueueStartRequest(BaseModel):
    retry_failed: bool = True
    retry_cancelled: bool = False


class QueueExecutionState(BaseModel):
    running: bool
    active_item_ids: list[str]
    pending_count: int
    max_concurrent: int
