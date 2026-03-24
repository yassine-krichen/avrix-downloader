from datetime import datetime, timezone
from enum import Enum
from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, Field


class ErrorCode(str, Enum):
    INTERNAL_ERROR = "internal_error"
    VALIDATION_ERROR = "validation_error"
    BAD_REQUEST = "bad_request"
    NOT_FOUND = "not_found"
    SERVICE_UNAVAILABLE = "service_unavailable"


class ErrorDetail(BaseModel):
    field: Optional[str] = None
    message: str


class ErrorResponse(BaseModel):
    code: ErrorCode
    message: str
    details: list[ErrorDetail] = Field(default_factory=list)
    trace_id: str


T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    data: T


class EventEnvelope(BaseModel):
    event_type: str
    event_version: str = "v1"
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    payload: dict[str, Any] = Field(default_factory=dict)
