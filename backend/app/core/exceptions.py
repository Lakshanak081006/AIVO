from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class AppException(Exception):
    def __init__(
        self,
        message: str,
        *,
        code: str = "APPLICATION_ERROR",
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Any = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details


class ResourceNotFoundError(AppException):
    def __init__(self, message: str = "Requested resource was not found") -> None:
        super().__init__(message, code="RESOURCE_NOT_FOUND", status_code=404)


class DuplicateResourceError(AppException):
    def __init__(self, message: str = "Resource already exists") -> None:
        super().__init__(message, code="DUPLICATE_RESOURCE", status_code=409)




class ConflictError(AppException):
    def __init__(self, message: str = "The requested operation conflicts with the current state") -> None:
        super().__init__(message, code="CONFLICT", status_code=409)

class ValidationFailureError(AppException):
    def __init__(self, message: str = "Validation failed", details: Any = None) -> None:
        super().__init__(message, code="VALIDATION_FAILURE", status_code=422, details=details)


class AuthenticationError(AppException):
    def __init__(self, message: str = "Authentication failed") -> None:
        super().__init__(message, code="AUTHENTICATION_FAILED", status_code=401)


class PermissionDeniedError(AppException):
    def __init__(self, message: str = "Permission denied") -> None:
        super().__init__(message, code="PERMISSION_DENIED", status_code=403)


class DatabaseOperationError(AppException):
    def __init__(self, message: str = "Database operation failed") -> None:
        super().__init__(message, code="DATABASE_OPERATION_FAILED", status_code=500)


class ExternalServiceError(AppException):
    def __init__(self, message: str = "External service failed") -> None:
        super().__init__(message, code="EXTERNAL_SERVICE_FAILED", status_code=502)


class LyzrUnavailableError(ExternalServiceError):
    def __init__(self, message: str = "Lyzr service is unavailable") -> None:
        super().__init__(message)
        self.code = "LYZR_UNAVAILABLE"


class LyzrAuthenticationError(AppException):
    def __init__(self, message: str = "Lyzr authentication failed — check LYZR_API_KEY") -> None:
        super().__init__(message, code="LYZR_AUTH_FAILED", status_code=502)


class LyzrRateLimitError(LyzrUnavailableError):
    def __init__(self, message: str = "Lyzr rate limit exceeded") -> None:
        super().__init__(message)
        self.code = "LYZR_RATE_LIMIT"


class LyzrResponseError(AppException):
    def __init__(self, message: str = "Lyzr returned an unexpected response") -> None:
        super().__init__(message, code="LYZR_RESPONSE_ERROR", status_code=502)


class WorkflowError(AppException):
    def __init__(self, message: str = "Workflow execution failed") -> None:
        super().__init__(message, code="WORKFLOW_FAILED", status_code=500)


def _error_payload(code: str, message: str, details: Any = None) -> dict[str, Any]:
    return {
        "success": False,
        "error": {"code": code, "message": message, "details": details},
    }


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppException)
    async def app_exception_handler(_: Request, exc: AppException) -> JSONResponse:
        headers = {"WWW-Authenticate": "Bearer"} if exc.status_code == 401 else None
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_payload(exc.code, exc.message, exc.details),
            headers=headers,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        _: Request, exc: RequestValidationError
    ) -> JSONResponse:
        serializable_errors: list[dict[str, Any]] = []
        for item in exc.errors():
            cleaned = dict(item)
            if isinstance(cleaned.get("ctx"), dict):
                cleaned["ctx"] = {
                    key: str(value) for key, value in cleaned["ctx"].items()
                }
            serializable_errors.append(cleaned)
        return JSONResponse(
            status_code=422,
            content=_error_payload(
                "REQUEST_VALIDATION_ERROR", "Invalid request data", serializable_errors
            ),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content=_error_payload("INTERNAL_SERVER_ERROR", "An unexpected error occurred"),
        )
