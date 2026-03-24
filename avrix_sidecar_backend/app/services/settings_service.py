import json
import threading
from pathlib import Path

from app.contracts.common import ErrorCode, ErrorDetail
from app.contracts.settings import AppSettings, SettingsPatchRequest
from app.core.config import settings
from app.core.errors import AppError


class SettingsService:
    def __init__(self, file_path: Path):
        self._file_path = file_path
        self._lock = threading.Lock()

    def get_settings(self) -> AppSettings:
        with self._lock:
            return self._load()

    def update_settings(self, patch: SettingsPatchRequest) -> AppSettings:
        with self._lock:
            current = self._load()
            changes = patch.model_dump(exclude_none=True)

            if "download_path" in changes:
                self._validate_and_prepare_path(changes["download_path"])

            updated = current.model_copy(update=changes)
            self._save(updated)
            return updated

    def _load(self) -> AppSettings:
        if not self._file_path.exists():
            defaults = AppSettings()
            self._save(defaults)
            return defaults

        try:
            raw = json.loads(self._file_path.read_text(encoding="utf-8"))
            return AppSettings(**raw)
        except Exception as exc:
            raise AppError(
                code=ErrorCode.INTERNAL_ERROR,
                message="Failed to read settings",
                details=[ErrorDetail(message=str(exc))],
                status_code=500,
            )

    def _save(self, model: AppSettings):
        try:
            self._file_path.parent.mkdir(parents=True, exist_ok=True)
            self._file_path.write_text(
                json.dumps(model.model_dump(), indent=2),
                encoding="utf-8",
            )
        except Exception as exc:
            raise AppError(
                code=ErrorCode.INTERNAL_ERROR,
                message="Failed to save settings",
                details=[ErrorDetail(message=str(exc))],
                status_code=500,
            )

    def _validate_and_prepare_path(self, target: str):
        if not target.strip():
            raise AppError(
                code=ErrorCode.VALIDATION_ERROR,
                message="Invalid settings payload",
                details=[ErrorDetail(field="download_path", message="download_path cannot be empty")],
                status_code=422,
            )

        try:
            Path(target).mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            raise AppError(
                code=ErrorCode.VALIDATION_ERROR,
                message="Invalid settings payload",
                details=[ErrorDetail(field="download_path", message=f"Unable to create/access path: {exc}")],
                status_code=422,
            )


settings_service = SettingsService(settings.config_root / "settings.json")
