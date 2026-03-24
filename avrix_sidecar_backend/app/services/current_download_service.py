import threading

import yt_dlp

from app.contracts.common import ErrorCode, ErrorDetail
from app.contracts.download import CurrentDownloadStartRequest, CurrentDownloadState
from app.core.errors import AppError


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

        ydl_opts: dict = {
            "outtmpl": f"{payload.download_path}/%(title)s.%(ext)s",
            "progress_hooks": [progress_hook],
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
        }

        if payload.format_type == "mp3":
            ydl_opts.update(
                {
                    "format": "bestaudio/best",
                    "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3"}],
                }
            )
        else:
            if payload.quality == "best":
                ydl_opts["format"] = "bestvideo+bestaudio/best"
            else:
                ydl_opts["format"] = f"bestvideo[height<={payload.quality.rstrip('p')}]+bestaudio/best"

        if payload.download_subtitles:
            ydl_opts["writesubtitles"] = True
            ydl_opts["subtitleslangs"] = [lang.strip() for lang in payload.subtitle_languages.split(",") if lang.strip()]

        if payload.embed_thumbnail:
            ydl_opts["writethumbnail"] = True

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(payload.url, download=False)
                title = info.get("title") if isinstance(info, dict) else None
                thumbnail = info.get("thumbnail") if isinstance(info, dict) else None
                self._update_state(title=title, thumbnail_url=thumbnail)
                ydl.download([payload.url])

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
