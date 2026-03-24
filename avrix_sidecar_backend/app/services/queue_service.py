import json
import threading
from pathlib import Path

from app.contracts.common import ErrorCode, ErrorDetail
from app.contracts.queue import QueueCreateRequest, QueueItem, QueueItemStatus
from app.core.config import settings
from app.core.errors import AppError


class QueueService:
    def __init__(self, file_path: Path):
        self._file_path = file_path
        self._lock = threading.Lock()

    def list_items(self) -> list[QueueItem]:
        with self._lock:
            return self._load()

    def get_item(self, item_id: str) -> QueueItem:
        with self._lock:
            items = self._load()
            for item in items:
                if item.id == item_id:
                    return item
            self._raise_not_found(item_id)

    def count_pending(self) -> int:
        with self._lock:
            items = self._load()
            return len([item for item in items if item.status == QueueItemStatus.PENDING])

    def find_next_pending(self, excluded_ids: set[str], excluded_urls: set[str] | None = None) -> QueueItem | None:
        with self._lock:
            items = self._load()
            blocked_urls = excluded_urls or set()
            for item in items:
                if (
                    item.status == QueueItemStatus.PENDING
                    and item.id not in excluded_ids
                    and item.url not in blocked_urls
                ):
                    return item
            return None

    def update_item_fields(self, item_id: str, **changes) -> QueueItem:
        with self._lock:
            items = self._load()
            index = self._find_index(items, item_id)
            updated = items[index].model_copy(update=changes)
            items[index] = updated
            self._save(items)
            return updated

    def bulk_retry(self, retry_failed: bool, retry_cancelled: bool):
        with self._lock:
            items = self._load()
            changed = False
            for index, item in enumerate(items):
                if retry_failed and item.status == QueueItemStatus.FAILED:
                    items[index] = item.model_copy(update={"status": QueueItemStatus.PENDING, "progress": 0.0})
                    changed = True
                    continue
                if retry_cancelled and item.status == QueueItemStatus.CANCELLED:
                    items[index] = item.model_copy(update={"status": QueueItemStatus.PENDING, "progress": 0.0})
                    changed = True
            if changed:
                self._save(items)

    def add_item(self, payload: QueueCreateRequest) -> QueueItem:
        with self._lock:
            items = self._load()

            duplicate = next(
                (
                    item
                    for item in items
                    if item.url == payload.url
                    and item.format_type == payload.format_type
                    and item.quality == payload.quality
                    and item.status in {QueueItemStatus.PENDING, QueueItemStatus.DOWNLOADING}
                ),
                None,
            )
            if duplicate:
                raise AppError(
                    code=ErrorCode.BAD_REQUEST,
                    message="Item already exists in queue",
                    details=[ErrorDetail(field="url", message="Duplicate active queue item")],
                    status_code=409,
                )

            item = QueueItem(
                url=payload.url,
                format_type=payload.format_type,
                quality=payload.quality,
                download_policy=payload.download_policy,
                download_path=payload.download_path,
                download_subtitles=payload.download_subtitles,
                subtitle_languages=payload.subtitle_languages,
                embed_thumbnail=payload.embed_thumbnail,
            )
            items.append(item)
            self._save(items)
            return item

    def remove_item(self, item_id: str):
        with self._lock:
            items = self._load()
            filtered = [item for item in items if item.id != item_id]
            if len(filtered) == len(items):
                self._raise_not_found(item_id)
            self._save(filtered)

    def move_item(self, item_id: str, direction: str) -> list[QueueItem]:
        with self._lock:
            items = self._load()
            index = self._find_index(items, item_id)

            if direction == "up" and index > 0:
                items[index - 1], items[index] = items[index], items[index - 1]
            elif direction == "down" and index < len(items) - 1:
                items[index + 1], items[index] = items[index], items[index + 1]

            self._save(items)
            return items

    def clear_finished(self) -> list[QueueItem]:
        with self._lock:
            items = self._load()
            active = [
                item
                for item in items
                if item.status not in {QueueItemStatus.COMPLETED, QueueItemStatus.FAILED, QueueItemStatus.CANCELLED}
            ]
            self._save(active)
            return active

    def clear_all(self):
        with self._lock:
            self._save([])

    def _find_index(self, items: list[QueueItem], item_id: str) -> int:
        for index, item in enumerate(items):
            if item.id == item_id:
                return index
        self._raise_not_found(item_id)

    def _raise_not_found(self, item_id: str):
        raise AppError(
            code=ErrorCode.NOT_FOUND,
            message="Queue item not found",
            details=[ErrorDetail(field="id", message=f"No queue item with id '{item_id}'")],
            status_code=404,
        )

    def _load(self) -> list[QueueItem]:
        if not self._file_path.exists():
            return []

        try:
            data = json.loads(self._file_path.read_text(encoding="utf-8"))
            return [QueueItem(**item) for item in data]
        except Exception as exc:
            raise AppError(
                code=ErrorCode.INTERNAL_ERROR,
                message="Failed to read queue",
                details=[ErrorDetail(message=str(exc))],
                status_code=500,
            )

    def _save(self, items: list[QueueItem]):
        try:
            self._file_path.parent.mkdir(parents=True, exist_ok=True)
            self._file_path.write_text(
                json.dumps([item.model_dump() for item in items], indent=2),
                encoding="utf-8",
            )
        except Exception as exc:
            raise AppError(
                code=ErrorCode.INTERNAL_ERROR,
                message="Failed to save queue",
                details=[ErrorDetail(message=str(exc))],
                status_code=500,
            )


queue_service = QueueService(settings.config_root / "download_queue.json")
