import threading
import time
from concurrent.futures import Future, ThreadPoolExecutor

import yt_dlp

from app.contracts.queue import QueueExecutionState, QueueItemStatus
from app.services.queue_service import queue_service
from app.services.settings_service import settings_service


class DownloadCancelled(Exception):
    pass


class DownloadEngineService:
    def __init__(self):
        self._lock = threading.Lock()
        self._running = False
        self._stop_event = threading.Event()
        self._dispatcher_thread: threading.Thread | None = None
        self._executor: ThreadPoolExecutor | None = None
        self._active_futures: dict[str, Future] = {}

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

                while not self._stop_event.is_set() and len(active_ids) < max_concurrent:
                    next_item = queue_service.find_next_pending(excluded_ids=active_ids)
                    if next_item is None:
                        break

                    queue_service.update_item_fields(
                        next_item.id,
                        status=QueueItemStatus.DOWNLOADING,
                        progress=0.0,
                    )

                    with self._lock:
                        if self._executor is None:
                            break
                        future = self._executor.submit(self._run_download, next_item.id)
                        self._active_futures[next_item.id] = future
                        active_ids.add(next_item.id)

                if not self._get_active_ids() and queue_service.count_pending() == 0:
                    break

                time.sleep(0.2)
        finally:
            with self._lock:
                if self._executor is not None:
                    self._executor.shutdown(wait=False, cancel_futures=False)
                    self._executor = None
                self._active_futures = {}
                self._running = False
                self._stop_event.clear()

    def _cleanup_finished(self):
        with self._lock:
            done_ids = [item_id for item_id, future in self._active_futures.items() if future.done()]
            for item_id in done_ids:
                self._active_futures.pop(item_id, None)

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

        ydl_opts = {
            "outtmpl": f"{item.download_path}/%(title)s.%(ext)s",
            "progress_hooks": [progress_hook],
            "noplaylist": False,
            "quiet": True,
            "no_warnings": True,
        }

        if item.format_type == "mp3":
            ydl_opts.update(
                {
                    "format": "bestaudio/best",
                    "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3"}],
                }
            )
        else:
            if item.quality == "best":
                ydl_opts["format"] = "bestvideo+bestaudio/best"
            else:
                ydl_opts["format"] = f"bestvideo[height<={item.quality.rstrip('p')}]+bestaudio/best"

        if item.download_subtitles:
            ydl_opts["writesubtitles"] = True
            ydl_opts["subtitleslangs"] = [lang.strip() for lang in item.subtitle_languages.split(",") if lang.strip()]

        if item.embed_thumbnail:
            ydl_opts["writethumbnail"] = True

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(item.url, download=False)
                title = info.get("title") if isinstance(info, dict) else None
                if title:
                    queue_service.update_item_fields(item_id, title=title)
                ydl.download([item.url])

            if self._stop_event.is_set():
                queue_service.update_item_fields(item_id, status=QueueItemStatus.CANCELLED)
            else:
                queue_service.update_item_fields(item_id, status=QueueItemStatus.COMPLETED, progress=100.0)
        except DownloadCancelled:
            queue_service.update_item_fields(item_id, status=QueueItemStatus.CANCELLED)
        except Exception:
            queue_service.update_item_fields(item_id, status=QueueItemStatus.FAILED)


download_engine_service = DownloadEngineService()
