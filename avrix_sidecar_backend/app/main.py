import logging
import uuid

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1.router import router as v1_router
from app.contracts.common import ErrorCode, ErrorDetail, ErrorResponse
from app.core.config import settings
from app.core.errors import AppError
from app.services.readiness import check_storage_ready


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("avrix.sidecar")

app = FastAPI(title=settings.app_name)
app.include_router(v1_router)


@app.middleware("http")
async def trace_middleware(request: Request, call_next):
    trace_id = request.headers.get("x-trace-id") or str(uuid.uuid4())
    request.state.trace_id = trace_id

    response = await call_next(request)
    response.headers["x-trace-id"] = trace_id
    return response


@app.exception_handler(AppError)
async def handle_app_error(request: Request, exc: AppError):
    trace_id = getattr(request.state, "trace_id", str(uuid.uuid4()))
    body = ErrorResponse(
        code=exc.code,
        message=exc.message,
        details=exc.details or [],
        trace_id=trace_id,
    )
    return JSONResponse(status_code=exc.status_code, content=body.model_dump())


@app.exception_handler(HTTPException)
async def handle_http_exception(request: Request, exc: HTTPException):
    trace_id = getattr(request.state, "trace_id", str(uuid.uuid4()))
    body = ErrorResponse(
        code=ErrorCode.BAD_REQUEST,
        message=str(exc.detail),
        details=[],
        trace_id=trace_id,
    )
    return JSONResponse(status_code=exc.status_code, content=body.model_dump())


@app.exception_handler(StarletteHTTPException)
async def handle_starlette_http_exception(request: Request, exc: StarletteHTTPException):
    trace_id = getattr(request.state, "trace_id", str(uuid.uuid4()))
    code = ErrorCode.NOT_FOUND if exc.status_code == 404 else ErrorCode.BAD_REQUEST

    body = ErrorResponse(
        code=code,
        message=str(exc.detail),
        details=[],
        trace_id=trace_id,
    )
    return JSONResponse(status_code=exc.status_code, content=body.model_dump())


@app.exception_handler(RequestValidationError)
async def handle_validation_error(request: Request, exc: RequestValidationError):
    trace_id = getattr(request.state, "trace_id", str(uuid.uuid4()))

    details = [
        ErrorDetail(
            field=".".join(str(part) for part in err.get("loc", [])),
            message=err.get("msg", "invalid value"),
        )
        for err in exc.errors()
    ]

    body = ErrorResponse(
        code=ErrorCode.VALIDATION_ERROR,
        message="Request validation failed",
        details=details,
        trace_id=trace_id,
    )
    return JSONResponse(status_code=422, content=body.model_dump())


@app.exception_handler(Exception)
async def handle_unexpected_error(request: Request, exc: Exception):
    trace_id = getattr(request.state, "trace_id", str(uuid.uuid4()))
    logger.exception("Unhandled error (trace_id=%s)", trace_id)

    body = ErrorResponse(
        code=ErrorCode.INTERNAL_ERROR,
        message="Unexpected server error",
        details=[],
        trace_id=trace_id,
    )
    return JSONResponse(status_code=500, content=body.model_dump())


@app.get("/")
def get_root() -> dict[str, str]:
    return {
        "name": settings.app_name,
        "environment": settings.app_env,
        "api": settings.api_prefix,
    }


@app.get("/health/live")
def get_liveness() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/ready")
def get_readiness() -> dict[str, str]:
    ready, reason = check_storage_ready(settings.config_root)
    return {
        "status": "ready" if ready else "not_ready",
        "reason": reason,
    }


if __name__ == "__main__":
    uvicorn.run("app.main:app", host=settings.app_host, port=settings.app_port, reload=False)
