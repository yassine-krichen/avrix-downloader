import threading
import time
from concurrent.futures import Future, ThreadPoolExecutor

from app.contracts.queue import QueueExecutionState, QueueItemStatus
from app.services.download_errors import DownloadCancelled, describe_download_error, run_ydl_attempts
from app.services.download_options import build_ydl_attempts, resolve_ffmpeg_location, resolve_js_runtime_path
from app.services.queue_service import queue_service
from app.services.settings_service import settings_service


class DownloadEngineService:
    def __init__(self):
        self._lock = threading.Lock()
        self._running = False
        self._stop_event = threading.Event()
        self._dispatcher_thread: threading.Thread | None = None
        self._executor: ThreadPoolExecutor | None = None
        self._active_futures: dict[str, Future] = {}
        self._active_item_urls: dict[str, str] = {}

    def get_state(self) -> QueueExecutionState:
        with self._lock:
            max_concurrent = settings_service.get_settings().max_concurrent_downloads
            pending_count = queue_service.count_pending()
            return QueueExecutionState(
                running=self._running,
                active_item_ids=list(self._active_futures.keys()),
                pending_count=pending_count,
                max_concurrent=max_concurrent,
            )

    def start(self, retry_failed: bool, retry_cancelled: bool) -> QueueExecutionState:
        with self._lock:
            if self._running:
                pass
            else:
                queue_service.bulk_retry(retry_failed=retry_failed, retry_cancelled=retry_cancelled)

                self._stop_event.clear()
                max_concurrent = settings_service.get_settings().max_concurrent_downloads
                self._executor = ThreadPoolExecutor(max_workers=max_concurrent, thread_name_prefix="avrix-dl")
                self._running = True
                self._dispatcher_thread = threading.Thread(target=self._dispatch_loop, daemon=True)
                self._dispatcher_thread.start()

        return self.get_state()

    def stop(self) -> QueueExecutionState:
        with self._lock:
            self._stop_event.set()
            for item_id in list(self._active_futures.keys()):
                queue_service.update_item_fields(item_id, status=QueueItemStatus.CANCELLED)

        return self.get_state()

    def _dispatch_loop(self):
        try:
            while True:
                if self._stop_event.is_set() and not self._get_active_ids():
                    break

                self._cleanup_finished()

                with self._lock:
                    if not self._running or self._executor is None:
                        break
                    max_concurrent = settings_service.get_settings().max_concurrent_downloads
                    active_ids = set(self._active_futures.keys())
                    active_urls = set(self._active_item_urls.values())

                while not self._stop_event.is_set() and len(active_ids) < max_concurrent:
                    next_item = queue_service.find_next_pending(excluded_ids=active_ids, excluded_urls=active_urls)
                    if next_item is None:
                        break

                    queue_service.update_item_fields(
                        next_item.id,
                        status=QueueItemStatus.DOWNLOADING,
                        progress=0.0,
                        error_message=None,
                    )

                    with self._lock:
                        if self._executor is None:
                            break
                        future = self._executor.submit(self._run_download, next_item.id)
                        self._active_futures[next_item.id] = future
                        self._active_item_urls[next_item.id] = next_item.url
                        active_ids.add(next_item.id)
                        active_urls.add(next_item.url)

                if not self._get_active_ids() and queue_service.count_pending() == 0:
                    break

                time.sleep(0.2)
        finally:
            with self._lock:
                if self._executor is not None:
                    self._executor.shutdown(wait=False, cancel_futures=False)
                    self._executor = None
                self._active_futures = {}
                self._active_item_urls = {}
                self._running = False
                self._stop_event.clear()

    def _cleanup_finished(self):
        with self._lock:
            done_ids = [item_id for item_id, future in self._active_futures.items() if future.done()]
            for item_id in done_ids:
                self._active_futures.pop(item_id, None)
                self._active_item_urls.pop(item_id, None)

    def _get_active_ids(self) -> list[str]:
        with self._lock:
            return list(self._active_futures.keys())

    def _run_download(self, item_id: str):
        item = queue_service.get_item(item_id)

        def progress_hook(data: dict):
            if self._stop_event.is_set():
                raise DownloadCancelled("Queue processing stopped")

            status = data.get("status")
            if status == "downloading":
                downloaded = data.get("downloaded_bytes", 0) or 0
                total = data.get("total_bytes") or data.get("total_bytes_estimate") or 0
                percent = (downloaded / total * 100.0) if total else float(data.get("_percent_str", "0").strip("%") or 0)
                queue_service.update_item_fields(item_id, progress=max(0.0, min(percent, 99.0)))
            elif status == "finished":
                queue_service.update_item_fields(item_id, progress=100.0)

        file_tag = f"{item.format_type}-{item.quality}-{item.id[:8]}"
        output_template = f"{item.download_path}/%(title)s [{file_tag}].%(ext)s"

        def record_title(info: dict):
            title = info.get("title")
            if title:
                queue_service.update_item_fields(item_id, title=title)

        try:
            # Built inside the try so a config error (e.g. missing ffmpeg for
            # strict quality) marks the item failed instead of leaving it
            # stuck in "downloading".
            attempts = build_ydl_attempts(
                format_type=item.format_type,
                quality=item.quality,
                download_policy=item.download_policy,
                output_template=output_template,
                progress_hook=progress_hook,
                download_subtitles=item.download_subtitles,
                subtitle_languages=item.subtitle_languages,
                embed_thumbnail=item.embed_thumbnail,
                ffmpeg_location=resolve_ffmpeg_location(),
                js_runtime_path=resolve_js_runtime_path(),
            )
            run_ydl_attempts(attempts, item.url, record_title)

            if self._stop_event.is_set():
                queue_service.update_item_fields(item_id, status=QueueItemStatus.CANCELLED)
            else:
                queue_service.update_item_fields(item_id, status=QueueItemStatus.COMPLETED, progress=100.0)
        except DownloadCancelled:
            queue_service.update_item_fields(item_id, status=QueueItemStatus.CANCELLED)
        except Exception as exc:
            queue_service.update_item_fields(
                item_id,
                status=QueueItemStatus.FAILED,
                error_message=describe_download_error(exc),
            )


download_engine_service = DownloadEngineService()
