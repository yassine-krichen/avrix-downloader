from fastapi import APIRouter

from app.services.readiness import check_storage_ready
from app.core.config import settings

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live")
def get_liveness() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
def get_readiness() -> dict[str, str]:
    ready, reason = check_storage_ready(settings.config_root)
    return {
        "status": "ready" if ready else "not_ready",
        "reason": reason,
    }
