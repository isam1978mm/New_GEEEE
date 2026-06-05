from __future__ import annotations

import json
from contextlib import asynccontextmanager
from pathlib import Path

from alembic import command
from alembic.config import Config
from fastapi import FastAPI
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

from app.api.artifacts import router as artifacts_router
from app.api.earth_engine import router as earth_engine_router
from app.api.errors import add_exception_handlers, public_error_response
from app.api.health import router as health_router
from app.api.roi_preview import router as roi_preview_router
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
        _apply_database_migrations(settings)
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
    app.state.settings = settings

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
    app.include_router(earth_engine_router)
    app.include_router(health_router)
    app.include_router(roi_preview_router)
    app.include_router(runs_router)
    app.include_router(artifacts_router)
    frontend_v2_dist_dir = Path(__file__).resolve().parent.parent / "frontend-v2" / "dist"
    if frontend_v2_dist_dir.is_dir():
        frontend_v2_index_path = frontend_v2_dist_dir / "index.html"
        frontend_v2_assets_dir = frontend_v2_dist_dir / "assets"

        if frontend_v2_assets_dir.is_dir():
            app.mount(
                "/v2/assets",
                StaticFiles(directory=frontend_v2_assets_dir),
                name="frontend-v2-assets",
            )

        @app.get("/", include_in_schema=False)
        async def frontend_index() -> FileResponse:
            return FileResponse(frontend_v2_index_path)

        @app.get("/v2", include_in_schema=False)
        async def frontend_v2_index() -> FileResponse:
            return FileResponse(frontend_v2_index_path)

        @app.get("/v2/{path:path}", include_in_schema=False)
        async def frontend_v2_fallback(path: str) -> FileResponse:
            return FileResponse(frontend_v2_index_path)

        @app.middleware("http")
        async def react_spa_fallback(request, call_next):
            response = await call_next(request)
            if response.status_code != 404 or not _is_react_ui_path(request.url.path):
                return response
            return FileResponse(frontend_v2_index_path)

    return app


app = create_app()


def _is_react_ui_path(path: str) -> bool:
    if path in {"/openapi.json", "/docs", "/redoc", "/healthz", "/readyz"}:
        return False
    if path.startswith("/runs"):
        return False
    if path.startswith("/v2/assets"):
        return False
    if "." in Path(path).name:
        return False
    return True


def _apply_database_migrations(settings: Settings) -> None:
    alembic_ini = Path(__file__).resolve().parent.parent / "alembic.ini"
    cfg = Config(str(alembic_ini))
    cfg.set_main_option("sqlalchemy.url", settings.database_url.replace("+aiosqlite", ""))
    command.upgrade(cfg, "head")
