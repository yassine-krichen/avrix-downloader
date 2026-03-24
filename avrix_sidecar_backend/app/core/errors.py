from dataclasses import dataclass

from app.contracts.common import ErrorCode, ErrorDetail


@dataclass
class AppError(Exception):
    code: ErrorCode
    message: str
    details: list[ErrorDetail] | None = None
    status_code: int = 400
