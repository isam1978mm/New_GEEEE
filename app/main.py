from __future__ import annotations

import json
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

from app.api.artifacts import router as artifacts_router
from app.api.errors import add_exception_handlers, public_error_response
from app.api.health import router as health_router
from app.api.runs import router as runs_router
from app.config import Settings, get_settings
from app.db.session import create_engine, create_session_factory
from app.logging_config import configure_logging
from app.services.redaction import verify_redacted
from app.services.run_state import mark_stale_running_runs
from app.services.storage import ensure_data_dirs


def create_app(settings: Settings | None = None) -> FastAPI:
    configure_logging()
    settings = settings or get_settings()
    ensure_data_dirs(settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.settings = settings
        app.state.engine = create_engine(settings)
        app.state.session_factory = create_session_factory(settings, engine=app.state.engine)
        async with app.state.session_factory() as session:
            await mark_stale_running_runs(session)
        try:
            yield
        finally:
            await app.state.engine.dispose()

    app = FastAPI(openapi_url=None, docs_url=None, redoc_url=None, lifespan=lifespan)

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
            return public_error_response(status_code=500, code="internal_error")

        return Response(
            content=body,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type,
            background=response.background,
        )

    add_exception_handlers(app)
    app.include_router(health_router)
    app.include_router(runs_router)
    app.include_router(artifacts_router)
    frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
    if frontend_dir.is_dir():
        index_path = frontend_dir / "index.html"
        app_js_path = frontend_dir / "app.js"
        style_path = frontend_dir / "style.css"
        vendor_dir = frontend_dir / "vendor"

        @app.get("/", include_in_schema=False)
        async def frontend_index() -> FileResponse:
            return FileResponse(index_path)

        @app.get("/app.js", include_in_schema=False)
        async def frontend_app_js() -> FileResponse:
            return FileResponse(app_js_path, media_type="application/javascript")

        @app.get("/style.css", include_in_schema=False)
        async def frontend_style_css() -> FileResponse:
            return FileResponse(style_path, media_type="text/css")

        if vendor_dir.is_dir():
            app.mount("/vendor", StaticFiles(directory=vendor_dir), name="frontend-vendor")

    return app


app = create_app()
