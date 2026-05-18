from __future__ import annotations

import json

from fastapi import FastAPI
from fastapi.responses import JSONResponse, Response

from app.api.errors import add_exception_handlers, public_error_response
from app.api.health import router as health_router
from app.logging_config import configure_logging
from app.services.redaction import verify_redacted


def create_app() -> FastAPI:
    configure_logging()
    app = FastAPI(openapi_url=None, docs_url=None, redoc_url=None)

    @app.middleware("http")
    async def verify_public_json_responses(request, call_next):
        response = await call_next(request)
        body = b""
        async for chunk in response.body_iterator:
            body += chunk

        content_type = response.headers.get("content-type", "")
        if "application/json" not in content_type:
            return Response(
                content=body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
                background=response.background,
            )

        try:
            payload = json.loads(body)
            verify_redacted(payload)
        except Exception:
            return public_error_response(status_code=500, code="redaction_violation")

        return Response(
            content=body,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type,
            background=response.background,
        )

    add_exception_handlers(app)
    app.include_router(health_router)

    @app.get("/", response_class=JSONResponse)
    async def root() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
