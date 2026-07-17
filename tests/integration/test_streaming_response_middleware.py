from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock

for _heavy_module in (
    "rasterio",
    "rasterio.transform",
    "rasterio.features",
    "rasterio.warp",
    "rasterio.enums",
    "ee",
):
    sys.modules.setdefault(_heavy_module, MagicMock())

from fastapi.responses import StreamingResponse

from app.config import Settings
from app.main import create_app


def test_non_json_stream_preserves_asgi_body_chunks() -> None:
    asyncio.run(_run_non_json_stream_case())


async def _run_non_json_stream_case() -> None:
    with TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        settings = Settings(
            data_dir=root / "data",
            database_path=root / "data" / "gee_screening.db",
        )
        app = create_app(settings)

        async def stream_chunks():
            yield b"first-"
            yield b"second-"
            yield b"third"

        async def stream_endpoint():
            return StreamingResponse(
                stream_chunks(),
                media_type="application/octet-stream",
            )

        app.add_api_route(
            "/__streaming_middleware_test__",
            stream_endpoint,
            methods=["GET"],
        )

        messages: list[dict] = []

        async def receive() -> dict:
            return {
                "type": "http.request",
                "body": b"",
                "more_body": False,
            }

        async def send(message: dict) -> None:
            messages.append(message)

        scope = {
            "type": "http",
            "asgi": {"version": "3.0", "spec_version": "2.4"},
            "http_version": "1.1",
            "method": "GET",
            "scheme": "http",
            "path": "/__streaming_middleware_test__",
            "raw_path": b"/__streaming_middleware_test__",
            "query_string": b"",
            "root_path": "",
            "headers": [],
            "client": ("127.0.0.1", 50000),
            "server": ("testserver", 80),
            "state": {},
        }

        await app(scope, receive, send)

    body_messages = [
        message
        for message in messages
        if message["type"] == "http.response.body"
    ]

    assert [message.get("body", b"") for message in body_messages] == [
        b"first-",
        b"second-",
        b"third",
        b"",
    ]
    assert [message.get("more_body", False) for message in body_messages] == [
        True,
        True,
        True,
        False,
    ]
