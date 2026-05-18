from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

from app.errors import RedactionViolationError

FORBIDDEN_KEYS = {
    "lat",
    "latitude",
    "lon",
    "lng",
    "long",
    "longitude",
    "coords",
    "coordinates",
    "geometry",
    "bounds",
    "bbox",
    "crstransform",
    "path",
    "absolute_path",
    "hash",
    "checksum",
    "fingerprint",
}
ABSOLUTE_PATH_PATTERN = re.compile(r"([A-Za-z]:\\[^\s]+)|(/[^\s]+)")
HEX_HASH_PATTERN = re.compile(r"\b[a-fA-F0-9]{32,64}\b")
COORDINATE_PAIR_PATTERN = re.compile(r"-?\d{1,3}\.\d+\s*,\s*-?\d{1,3}\.\d+")


def redact_for_log(message: str) -> str:
    redacted = ABSOLUTE_PATH_PATTERN.sub("[REDACTED_PATH]", message)
    redacted = HEX_HASH_PATTERN.sub("[REDACTED_HASH]", redacted)
    redacted = COORDINATE_PAIR_PATTERN.sub("[REDACTED_COORDS]", redacted)
    return redacted


def verify_redacted(payload: Any) -> None:
    _verify_node(payload)


def _verify_node(node: Any) -> None:
    if isinstance(node, Mapping):
        for key, value in node.items():
            normalized_key = str(key).lower()
            if normalized_key in FORBIDDEN_KEYS:
                raise RedactionViolationError()
            _verify_node(value)
        return

    if isinstance(node, Sequence) and not isinstance(node, (str, bytes, bytearray)):
        for item in node:
            _verify_node(item)
        return

    if isinstance(node, str):
        if ABSOLUTE_PATH_PATTERN.search(node):
            raise RedactionViolationError()
        if HEX_HASH_PATTERN.search(node):
            raise RedactionViolationError()
        if COORDINATE_PAIR_PATTERN.search(node):
            raise RedactionViolationError()
