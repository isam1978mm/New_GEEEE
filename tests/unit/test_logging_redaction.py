from __future__ import annotations

import json
import logging

from app.logging_config import JsonFormatter


def test_info_logs_are_redacted() -> None:
    formatter = JsonFormatter()
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="roi_center 12.34, 56.78 C:\\tmp\\secret deadbeefdeadbeefdeadbeefdeadbeef",
        args=(),
        exc_info=None,
    )

    payload = json.loads(formatter.format(record))
    assert payload["message"] == "roi_center [REDACTED_COORDS] [REDACTED_PATH] [REDACTED_HASH]"


def test_debug_logs_are_not_redacted_by_formatter() -> None:
    formatter = JsonFormatter()
    record = logging.LogRecord(
        name="test",
        level=logging.DEBUG,
        pathname=__file__,
        lineno=1,
        msg="roi_center 12.34, 56.78 C:\\tmp\\secret",
        args=(),
        exc_info=None,
    )

    payload = json.loads(formatter.format(record))
    assert payload["message"] == "roi_center 12.34, 56.78 C:\\tmp\\secret"
