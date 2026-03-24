from fastapi import APIRouter

from app.contracts.settings import AppSettings, SettingsPatchRequest
from app.services.settings_service import settings_service

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=AppSettings)
def get_settings() -> AppSettings:
    return settings_service.get_settings()


@router.patch("", response_model=AppSettings)
def patch_settings(payload: SettingsPatchRequest) -> AppSettings:
    return settings_service.update_settings(payload)
