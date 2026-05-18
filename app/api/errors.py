from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.errors import AppError
from app.schemas.errors import ErrorPublic
from app.services.redaction import verify_redacted


def public_error_response(status_code: int, code: str, message: str | None = None) -> JSONResponse:
    payload = ErrorPublic(error=code, message=message or "Request could not be processed.").model_dump()
    try:
        verify_redacted(payload)
    except AppError:
        payload = ErrorPublic(
            error="internal_error",
            message="Request could not be processed.",
        ).model_dump()
    return JSONResponse(status_code=status_code, content=payload)


def add_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(_: Request, exc: AppError) -> JSONResponse:
        return public_error_response(
            status_code=exc.status_code,
            code=exc.public_code,
            message=exc.public_message,
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(_: Request, __: RequestValidationError) -> JSONResponse:
        return public_error_response(status_code=422, code="validation_error")

    @app.exception_handler(HTTPException)
    async def handle_http_exception(_: Request, exc: HTTPException) -> JSONResponse:
        return public_error_response(status_code=exc.status_code, code="http_error")

    @app.exception_handler(Exception)
    async def handle_unexpected_error(_: Request, __: Exception) -> JSONResponse:
        return public_error_response(status_code=500, code="internal_error")

