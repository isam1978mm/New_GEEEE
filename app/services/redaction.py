from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

from app.errors import RedactionViolationError

REDACTED_VALUE = "[REDACTED]"
REDACTED_COORDS = "[REDACTED_COORDS]"
REDACTED_HASH = "[REDACTED_HASH]"
REDACTED_PATH = "[REDACTED_PATH]"
REDACTED_GEOMETRY = "[REDACTED_GEOMETRY]"

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
    "geom",
    "bounds",
    "bbox",
    "extent",
    "crs",
    "epsg",
    "projection",
    "spatial_ref",
    "crs_transform",
    "crstransform",
    "transform",
    "origin",
    "ul_x",
    "ul_y",
    "lr_x",
    "lr_y",
    "pixel_size",
    "gsd",
    "hash",
    "sha",
    "sha256",
    "md5",
    "checksum",
    "fingerprint",
    "filesystem_path",
    "abs_path",
    "full_path",
    "path",
    "request_body",
    "raw_input",
    "traceback",
    "stacktrace",
    "exception_repr",
}
CONTEXTUAL_FORBIDDEN_KEYS = {"x", "y", "input"}
SPATIAL_TERMS = {
    "coord",
    "point",
    "center",
    "vertex",
    "bbox",
    "bounds",
    "geometry",
    "geom",
    "location",
    "roi",
    "lat",
    "lon",
    "utm",
    "crs",
    "transform",
    "origin",
}
ABSOLUTE_PATH_PATTERN = re.compile(
    r"(?i)([A-Z]:\\(?:[^\\/:*?\"<>|\s\r\n]+\\)*[^\\/:*?\"<>|\s\r\n]*)|(/(?:Users|home|mnt)/\S+)"
)
HEX_HASH_PATTERN = re.compile(r"\b[a-fA-F0-9]{32,64}\b")
WKT_PATTERN = re.compile(
    r"\b(POINT|LINESTRING|POLYGON|MULTIPOLYGON|MULTILINESTRING|MULTIPOINT|GEOMETRYCOLLECTION)\s*\(",
    re.IGNORECASE,
)
INLINE_GEO_PATTERN = re.compile(
    r"(?i)(\"type\"\s*:\s*\"(?:Feature|FeatureCollection|Point|Polygon|MultiPolygon|LineString|MultiLineString|MultiPoint)\")|(<kml\b)|(<Placemark\b)"
)
COORDINATE_PAIR_PATTERN = re.compile(
    r"(?P<lat>-?\d{1,3}(?:\.\d+)?)\s*,\s*(?P<lon>-?\d{1,3}(?:\.\d+)?)"
)


def redact(payload: Any) -> Any:
    return _redact_node(payload, context=())


def redact_for_log(message: str, *, levelno: int | None = None) -> str:
    if levelno is not None and levelno < 20:
        return message

    redacted = ABSOLUTE_PATH_PATTERN.sub(REDACTED_PATH, message)
    redacted = HEX_HASH_PATTERN.sub(REDACTED_HASH, redacted)
    if WKT_PATTERN.search(redacted) or INLINE_GEO_PATTERN.search(redacted):
        redacted = WKT_PATTERN.sub(REDACTED_GEOMETRY, redacted)
        redacted = INLINE_GEO_PATTERN.sub(REDACTED_GEOMETRY, redacted)
    redacted = _redact_coordinate_pairs_in_text(redacted, context=("log", "coord"))
    return redacted


def verify_redacted(payload: Any) -> None:
    _verify_node(payload, context=())


def _redact_node(node: Any, *, context: tuple[str, ...]) -> Any:
    if isinstance(node, Mapping):
        redacted: dict[str, Any] = {}
        for key, value in node.items():
            key_str = str(key)
            if _is_forbidden_key(key_str, context):
                continue
            redacted[key_str] = _redact_node(value, context=context + (key_str.lower(),))
        return redacted

    if isinstance(node, Sequence) and not isinstance(node, (str, bytes, bytearray)):
        if _looks_like_spatial_pair(node, context):
            return REDACTED_COORDS
        return [_redact_node(item, context=context) for item in node]

    if isinstance(node, str):
        return _redact_text(node, context=context)

    return node


def _verify_node(node: Any, *, context: tuple[str, ...]) -> None:
    if isinstance(node, Mapping):
        for key, value in node.items():
            if _is_forbidden_key(str(key), context):
                raise RedactionViolationError()
            _verify_node(value, context=context + (str(key).lower(),))
        return

    if isinstance(node, Sequence) and not isinstance(node, (str, bytes, bytearray)):
        if _looks_like_spatial_pair(node, context):
            raise RedactionViolationError()
        for item in node:
            _verify_node(item, context=context)
        return

    if isinstance(node, str) and _text_needs_redaction(node, context):
        raise RedactionViolationError()


def _redact_text(value: str, *, context: tuple[str, ...]) -> str:
    redacted = ABSOLUTE_PATH_PATTERN.sub(REDACTED_PATH, value)
    redacted = HEX_HASH_PATTERN.sub(REDACTED_HASH, redacted)
    if WKT_PATTERN.search(redacted) or INLINE_GEO_PATTERN.search(redacted):
        return REDACTED_GEOMETRY
    return _redact_coordinate_pairs_in_text(redacted, context=context)


def _redact_coordinate_pairs_in_text(value: str, *, context: tuple[str, ...]) -> str:
    if not _has_spatial_context(context):
        return value

    def replace(match: re.Match[str]) -> str:
        lat = float(match.group("lat"))
        lon = float(match.group("lon"))
        if _is_plausible_lat_lon(lat, lon):
            return REDACTED_COORDS
        return match.group(0)

    return COORDINATE_PAIR_PATTERN.sub(replace, value)


def _text_needs_redaction(value: str, context: tuple[str, ...]) -> bool:
    if ABSOLUTE_PATH_PATTERN.search(value):
        return True
    if HEX_HASH_PATTERN.search(value):
        return True
    if WKT_PATTERN.search(value) or INLINE_GEO_PATTERN.search(value):
        return True
    if not _has_spatial_context(context):
        return False

    for match in COORDINATE_PAIR_PATTERN.finditer(value):
        lat = float(match.group("lat"))
        lon = float(match.group("lon"))
        if _is_plausible_lat_lon(lat, lon):
            return True
    return False


def _looks_like_spatial_pair(node: Sequence[Any], context: tuple[str, ...]) -> bool:
    if len(node) != 2 or not _has_spatial_context(context):
        return False
    if not all(isinstance(item, (int, float)) for item in node):
        return False
    first = float(node[0])
    second = float(node[1])
    return _is_plausible_lat_lon(first, second)


def _is_forbidden_key(key: str, context: tuple[str, ...]) -> bool:
    normalized = key.lower()
    if normalized in FORBIDDEN_KEYS:
        return True
    if normalized in CONTEXTUAL_FORBIDDEN_KEYS and _has_spatial_context(context):
        return True
    return False


def _has_spatial_context(context: tuple[str, ...]) -> bool:
    for item in context:
        lowered = item.lower()
        if any(term in lowered for term in SPATIAL_TERMS):
            return True
    return False


def _is_plausible_lat_lon(lat: float, lon: float) -> bool:
    return -90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0
