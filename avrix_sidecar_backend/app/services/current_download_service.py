import threading

import yt_dlp

from app.contracts.common import ErrorCode, ErrorDetail
from app.contracts.download import CurrentDownloadStartRequest, CurrentDownloadState
from app.core.errors import AppError
from app.services.download_options import build_ydl_attempts, resolve_ffmpeg_location


class DownloadCancelled(Exception):
    pass


class CurrentDownloadService:
    def __init__(self):
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._state = CurrentDownloadState()

    def get_state(self) -> CurrentDownloadState:
        with self._lock:
            return self._state.model_copy(deep=True)

    def start(self, payload: CurrentDownloadStartRequest) -> CurrentDownloadState:
        with self._lock:
            if self._state.running:
                raise AppError(
                    code=ErrorCode.BAD_REQUEST,
                    message="A download is already in progress",
                    details=[ErrorDetail(field="running", message="Cancel current download before starting a new one")],
                    status_code=409,
                )

            self._stop_event.clear()
            self._state = CurrentDownloadState(
                running=True,
                status="starting",
                url=payload.url,
                progress=0.0,
            )

        worker = threading.Thread(target=self._run_download, args=(payload,), daemon=True)
        self._thread = worker
        worker.start()

        return self.get_state()

    def cancel(self) -> CurrentDownloadState:
        with self._lock:
            if not self._state.running:
                return self._state.model_copy(deep=True)
            self._stop_event.set()
            self._state = self._state.model_copy(update={"status": "cancelled"})
            return self._state.model_copy(deep=True)

    def _update_state(self, **changes):
        with self._lock:
            self._state = self._state.model_copy(update=changes)

    def _run_download(self, payload: CurrentDownloadStartRequest):
        def progress_hook(data: dict):
            if self._stop_event.is_set():
                raise DownloadCancelled("Download cancelled")

            status = data.get("status")
            if status == "downloading":
                downloaded = int(data.get("downloaded_bytes", 0) or 0)
                total = int(data.get("total_bytes") or data.get("total_bytes_estimate") or 0)
                speed = float(data.get("speed", 0.0) or 0.0)
                eta = int(data.get("eta", 0) or 0)
                percent = (downloaded / total * 100.0) if total > 0 else 0.0
                self._update_state(
                    status="downloading",
                    downloaded_bytes=downloaded,
                    total_bytes=total,
                    speed_bps=speed,
                    eta_seconds=eta,
                    progress=max(0.0, min(percent, 99.5)),
                )
            elif status == "finished":
                self._update_state(progress=100.0)

        file_tag = f"single-{payload.format_type}-{payload.quality}"
        output_template = f"{payload.download_path}/%(title)s [{file_tag}].%(ext)s"

        attempts = build_ydl_attempts(
            format_type=payload.format_type,
            quality=payload.quality,
            download_policy=payload.download_policy,
            output_template=output_template,
            progress_hook=progress_hook,
            download_subtitles=payload.download_subtitles,
            subtitle_languages=payload.subtitle_languages,
            embed_thumbnail=payload.embed_thumbnail,
            ffmpeg_location=resolve_ffmpeg_location(),
        )

        try:
            last_error: Exception | None = None
            download_succeeded = False

            for ydl_opts in attempts:
                try:
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(payload.url, download=False)
                        title = info.get("title") if isinstance(info, dict) else None
                        thumbnail = info.get("thumbnail") if isinstance(info, dict) else None
                        self._update_state(title=title, thumbnail_url=thumbnail)
                        ydl.download([payload.url])

                    download_succeeded = True
                    break
                except DownloadCancelled:
                    raise
                except Exception as exc:
                    last_error = exc
                    continue

            if not download_succeeded:
                if last_error is not None:
                    raise last_error
                raise RuntimeError("Download failed for unknown reason")

            if self._stop_event.is_set():
                self._update_state(running=False, status="cancelled", speed_bps=0.0, eta_seconds=0)
            else:
                self._update_state(running=False, status="completed", progress=100.0, speed_bps=0.0, eta_seconds=0)
        except DownloadCancelled:
            self._update_state(running=False, status="cancelled", speed_bps=0.0, eta_seconds=0)
        except Exception as exc:
            self._update_state(
                running=False,
                status="failed",
                speed_bps=0.0,
                eta_seconds=0,
                error_message=str(exc),
            )
        finally:
            self._stop_event.clear()


current_download_service = CurrentDownloadService()
