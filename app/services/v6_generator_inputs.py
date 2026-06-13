"""Input models for app-side V6 package generation.

The models in this module are intentionally small and safe. They connect the
synthetic V6 package generator to app-input fixtures without introducing Earth
Engine execution, real geometry, notebook globals, or provider integrations.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import math
from pathlib import Path
import re
from typing import Any, Mapping, Sequence


_SAFE_ID_PATTERN = re.compile(r"^[A-Za-z0-9_.:-]+$")
_DISALLOWED_KEYS = {"coordinates", "features", "geometry", "geojson"}
_DEFAULT_TIMESTAMP = "20260101T120000Z"


@dataclass(frozen=True)
class V6InputCandidate:
    cell_id: str
    candidate_score: float
    v6_review_priority_score: float


@dataclass(frozen=True)
class V6InputRequestZone:
    request_zone_id: str
    primary_cell_id: str
    quote_id: str
    quote_score: float = 0.0


@dataclass(frozen=True)
class V6GenerationInput:
    run_id: str
    timestamp: str
    candidates: tuple[V6InputCandidate, ...]
    request_zones: tuple[V6InputRequestZone, ...]


def build_synthetic_v6_generation_input(*, timestamp: str = _DEFAULT_TIMESTAMP) -> V6GenerationInput:
    """Return the default synthetic fixture used by generator unit tests."""

    return V6GenerationInput(
        run_id="SYNTH_RUN_001",
        timestamp=timestamp,
        candidates=(
            V6InputCandidate(
                cell_id="SYNTH_CELL_001",
                candidate_score=0.81,
                v6_review_priority_score=0.91,
            ),
            V6InputCandidate(
                cell_id="SYNTH_CELL_002",
                candidate_score=0.63,
                v6_review_priority_score=0.72,
            ),
        ),
        request_zones=(
            V6InputRequestZone(
                request_zone_id="SYNTH_ZONE_001",
                primary_cell_id="SYNTH_CELL_001",
                quote_id="SYNTH_QUOTE_001",
                quote_score=0.0,
            ),
        ),
    )


def load_v6_generation_input_json(path: str | Path) -> V6GenerationInput:
    """Load a V6 generation input fixture from JSON."""

    source = Path(path)
    payload = json.loads(source.read_text(encoding="utf-8-sig"))
    return v6_generation_input_from_mapping(payload)


def v6_generation_input_from_mapping(payload: Mapping[str, Any]) -> V6GenerationInput:
    """Build a safe V6GenerationInput from a JSON-like mapping."""

    _reject_disallowed_keys(payload, "root")
    run_id = _safe_id(payload.get("run_id", "APP_INPUT_RUN_001"), field_name="run_id")
    timestamp = _safe_timestamp(str(payload.get("timestamp", _DEFAULT_TIMESTAMP)))

    candidates_raw = payload.get("candidates")
    if not isinstance(candidates_raw, Sequence) or isinstance(candidates_raw, (str, bytes)):
        raise ValueError("candidates must be a list")
    if not candidates_raw:
        raise ValueError("candidates must not be empty")

    candidates = tuple(_candidate_from_mapping(item, index) for index, item in enumerate(candidates_raw))

    zones_raw = payload.get("request_zones")
    if zones_raw is None:
        zones = _default_request_zones_from_candidates(candidates)
    else:
        if not isinstance(zones_raw, Sequence) or isinstance(zones_raw, (str, bytes)):
            raise ValueError("request_zones must be a list")
        zones = tuple(_zone_from_mapping(item, index) for index, item in enumerate(zones_raw))

    if not zones:
        raise ValueError("request_zones must not be empty")

    candidate_ids = {candidate.cell_id for candidate in candidates}
    for zone in zones:
        if zone.primary_cell_id not in candidate_ids:
            raise ValueError(f"request zone references unknown primary_cell_id:{zone.primary_cell_id}")

    return V6GenerationInput(
        run_id=run_id,
        timestamp=timestamp,
        candidates=candidates,
        request_zones=zones,
    )


def _candidate_from_mapping(item: object, index: int) -> V6InputCandidate:
    if not isinstance(item, Mapping):
        raise ValueError(f"candidate must be an object at index {index}")
    _reject_disallowed_keys(item, f"candidates[{index}]")
    return V6InputCandidate(
        cell_id=_safe_id(item.get("cell_id"), field_name=f"candidates[{index}].cell_id"),
        candidate_score=_safe_float(item.get("candidate_score"), field_name=f"candidates[{index}].candidate_score"),
        v6_review_priority_score=_safe_float(
            item.get("v6_review_priority_score", item.get("candidate_score")),
            field_name=f"candidates[{index}].v6_review_priority_score",
        ),
    )


def _zone_from_mapping(item: object, index: int) -> V6InputRequestZone:
    if not isinstance(item, Mapping):
        raise ValueError(f"request zone must be an object at index {index}")
    _reject_disallowed_keys(item, f"request_zones[{index}]")
    request_zone_id = _safe_id(
        item.get("request_zone_id"),
        field_name=f"request_zones[{index}].request_zone_id",
    )
    return V6InputRequestZone(
        request_zone_id=request_zone_id,
        primary_cell_id=_safe_id(
            item.get("primary_cell_id"),
            field_name=f"request_zones[{index}].primary_cell_id",
        ),
        quote_id=_safe_id(
            item.get("quote_id", f"QUOTE_{request_zone_id}"),
            field_name=f"request_zones[{index}].quote_id",
        ),
        quote_score=_safe_float(
            item.get("quote_score", 0.0),
            field_name=f"request_zones[{index}].quote_score",
        ),
    )


def _default_request_zones_from_candidates(
    candidates: tuple[V6InputCandidate, ...],
) -> tuple[V6InputRequestZone, ...]:
    first = candidates[0]
    return (
        V6InputRequestZone(
            request_zone_id="APP_INPUT_ZONE_001",
            primary_cell_id=first.cell_id,
            quote_id="APP_INPUT_QUOTE_001",
            quote_score=0.0,
        ),
    )


def _reject_disallowed_keys(payload: Mapping[str, Any], path: str) -> None:
    for key in payload:
        if str(key).lower() in _DISALLOWED_KEYS:
            raise ValueError(f"disallowed geometry-like key at {path}:{key}")


def _safe_id(value: object, *, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    normalized = value.strip()
    if not _SAFE_ID_PATTERN.fullmatch(normalized):
        raise ValueError(f"{field_name} contains unsupported characters")
    return normalized


def _safe_timestamp(value: str) -> str:
    if not re.fullmatch(r"\d{8}T\d{6}Z", value):
        raise ValueError("timestamp must use YYYYMMDDTHHMMSSZ format")
    return value


def _safe_float(value: object, *, field_name: str) -> float:
    if isinstance(value, bool) or value is None:
        raise ValueError(f"{field_name} must be a finite number")
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be a finite number") from exc
    if not math.isfinite(result):
        raise ValueError(f"{field_name} must be a finite number")
    return result
