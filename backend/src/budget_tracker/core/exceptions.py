from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class DomainError(Exception):
    """Base class for errors caused by breaking a business rule."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class NotFoundError(DomainError):
    """The requested resource does not exist."""


class ConflictError(DomainError):
    """The request conflicts with existing data, e.g. a duplicate name."""


class InvalidFileError(DomainError):
    """An uploaded file cannot be read, e.g. a CSV with a wrong header."""


_DOMAIN_ERROR_STATUS: dict[type[DomainError], tuple[int, str]] = {
    NotFoundError: (status.HTTP_404_NOT_FOUND, "not_found"),
    ConflictError: (status.HTTP_409_CONFLICT, "conflict"),
    InvalidFileError: (status.HTTP_400_BAD_REQUEST, "invalid_file"),
}


def _error_response(
    status_code: int,
    code: str,
    message: str,
    details: list[dict[str, str]] | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message, "details": details or []}},
    )


async def _handle_domain_error(_request: Request, exc: DomainError) -> JSONResponse:
    status_code, code = _DOMAIN_ERROR_STATUS.get(
        type(exc), (status.HTTP_400_BAD_REQUEST, "bad_request")
    )

    return _error_response(status_code, code, exc.message)


async def _handle_validation_error(_request: Request, exc: RequestValidationError) -> JSONResponse:
    details = [
        {"field": ".".join(str(part) for part in error["loc"]), "message": error["msg"]}
        for error in exc.errors()
    ]
    return _error_response(
        status.HTTP_422_UNPROCESSABLE_CONTENT, "validation_error", "Invalid input.", details
    )


async def _handle_http_exception(_request: Request, exc: StarletteHTTPException) -> JSONResponse:
    return _error_response(exc.status_code, "http_error", str(exc.detail))


async def _handle_unexpected_error(_request: Request, _exc: Exception) -> JSONResponse:
    return _error_response(
        status.HTTP_500_INTERNAL_SERVER_ERROR, "internal_error", "Something went wrong."
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(DomainError, _handle_domain_error)
    app.add_exception_handler(RequestValidationError, _handle_validation_error)
    app.add_exception_handler(StarletteHTTPException, _handle_http_exception)
    app.add_exception_handler(Exception, _handle_unexpected_error)
