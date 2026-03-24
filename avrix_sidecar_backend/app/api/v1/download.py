from fastapi import APIRouter

from app.contracts.download import CurrentDownloadStartRequest, CurrentDownloadState
from app.services.current_download_service import current_download_service

router = APIRouter(prefix="/download", tags=["download"])


@router.get("/current", response_model=CurrentDownloadState)
def get_current_download() -> CurrentDownloadState:
    return current_download_service.get_state()


@router.post("/start", response_model=CurrentDownloadState)
def start_current_download(payload: CurrentDownloadStartRequest) -> CurrentDownloadState:
    return current_download_service.start(payload)


@router.post("/cancel", response_model=CurrentDownloadState)
def cancel_current_download() -> CurrentDownloadState:
    return current_download_service.cancel()
