from __future__ import annotations

import json
import logging

from app.services.redaction import redact_for_log


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "level": record.levelname,
            "logger": record.name,
            "message": redact_for_log(record.getMessage()),
        }
        return json.dumps(payload)


def configure_logging() -> None:
    root_logger = logging.getLogger()
    if root_logger.handlers:
        return
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(handler)

