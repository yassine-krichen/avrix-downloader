from fastapi import APIRouter

from app.api.v1.health import router as health_router
from app.api.v1.settings import router as settings_router

router = APIRouter(prefix="/api/v1")
router.include_router(health_router)
router.include_router(settings_router)
