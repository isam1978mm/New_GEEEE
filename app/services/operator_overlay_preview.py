from __future__ import annotations

from dataclasses import dataclass
import json
import math
from pathlib import Path
from typing import Any, Iterable, Mapping
import xml.etree.ElementTree as ET
import zipfile

from app.config import Settings
from app.pipeline.parity import resolve_run_output_path
from app.pipeline.parity.manifest import ParityPathError
from app.pipeline.parity.operator_overlay_access_foundation import (
    OverlayAccessRequest,
    build_audit_event,
    build_redacted_denial_response,
    evaluate_overlay_access,
)
from app.pipeline.parity.operator_overlay_implementation_design import ALLOWED_ACCESS_MODE
from app.pipeline.parity.private_map_artifact_comparator import (
    PHASE_D1_GEOJSON_FAMILY_ID,
    PHASE_D2_KMZ_FAMILY_ID,
    PHASE_D3_HEATMAP_FAMILY_ID,
)
from app.pipeline.parity.private_map_artifact_writers import (
    PRIVATE_GEOJSON_DEFAULT_FILENAME,
    PRIVATE_GEOJSON_DEFAULT_OUTPUT_DIR,
    PRIVATE_HEATMAP_DEFAULT_FILENAME,
    PRIVATE_HEATMAP_DEFAULT_OUTPUT_DIR,
    PRIVATE_KMZ_DEFAULT_FILENAME,
    PRIVATE_KMZ_DEFAULT_OUTPUT_DIR,
    PRIVATE_KMZ_KML_FILENAME,
)
from app.services.storage import get_run_dir


# Fixed, run-relative locations of the Phase D private map artifacts. The operator
# preview only ever reads these fixed locations under the run directory.
_FAMILY_RELATIVE_PATHS: dict[str, str] = {
    PHASE_D1_GEOJSON_FAMILY_ID: f"{PRIVATE_GEOJSON_DEFAULT_OUTPUT_DIR}/{PRIVATE_GEOJSON_DEFAULT_FILENAME}",
    PHASE_D2_KMZ_FAMILY_ID: f"{PRIVATE_KMZ_DEFAULT_OUTPUT_DIR}/{PRIVATE_KMZ_DEFAULT_FILENAME}",
    PHASE_D3_HEATMAP_FAMILY_ID: f"{PRIVATE_HEATMAP_DEFAULT_OUTPUT_DIR}/{PRIVATE_HEATMAP_DEFAULT_FILENAME}",
}
_FAMILY_PREVIEW_TYPES: dict[str, str] = {
    PHASE_D1_GEOJSON_FAMILY_ID: "geojson_feature_collection",
    PHASE_D2_KMZ_FAMILY_ID: "kmz_placemarks",
    PHASE_D3_HEATMAP_FAMILY_ID: "heatmap_points",
}

_HEATMAP_NUMERIC_KEYS = ("weight", "score", "probability")


@dataclass(frozen=True)
class OperatorOverlayPreviewResult:
    status_code: int
    body: dict[str, Any]
    decision_status: str
    allowed: bool
    audit_event: dict[str, Any]


def build_operator_overlay_preview(
    *,
    settings: Settings,
    run_id: str,
    requested_artifact_family: str,
    requested_access_mode: str,
    actor_id: str | None,
    is_authenticated: bool,
    roles: Iterable[str],
    authorized_run_ids: Iterable[str] | None,
    request_id: str,
) -> OperatorOverlayPreviewResult:
    """Decide operator-only private overlay access and build a private preview.

    Denied decisions never read an artifact file and return a generic redacted
    denial. Allowed decisions read only the requested private artifact under the run
    directory and return a coordinate-free operator-only preview. Every decision
    builds an audit event. No public download URL or artifact-serving URL is created.
    """

    request = OverlayAccessRequest(
        actor_id=actor_id,
        is_authenticated=is_authenticated,
        roles=tuple(roles),
        run_id=run_id,
        requested_artifact_family=requested_artifact_family,
        requested_access_mode=requested_access_mode,
        operator_overlay_preview_enabled=bool(settings.operator_private_overlay_preview_enabled),
        request_id=request_id,
        authorized_run_ids=tuple(authorized_run_ids) if authorized_run_ids is not None else None,
    )
    decision = evaluate_overlay_access(request)
    audit_event = build_audit_event(decision, actor_id=actor_id)

    if not decision.allowed:
        denial = build_redacted_denial_response(decision)
        body = {"outcome": "denied", **denial}
        return OperatorOverlayPreviewResult(
            status_code=403,
            body=body,
            decision_status=decision.status,
            allowed=False,
            audit_event=audit_event,
        )

    preview_type = _FAMILY_PREVIEW_TYPES[requested_artifact_family]
    audit_summary = {
        "event_type": audit_event["event_type"],
        "access_outcome": audit_event["access_outcome"],
        "reason_code": audit_event["reason_code"],
        "request_id": audit_event["request_id"],
    }
    artifact_path = _resolve_private_artifact_path(settings, run_id, requested_artifact_family)
    preview = _load_preview(requested_artifact_family, artifact_path)

    if preview is None:
        body = _operator_body(
            outcome="not_available",
            run_id=run_id,
            artifact_family=requested_artifact_family,
            preview_type=preview_type,
            item_count=None,
            preview_payload=None,
            audit_summary=audit_summary,
        )
        return OperatorOverlayPreviewResult(
            status_code=200,
            body=body,
            decision_status=decision.status,
            allowed=True,
            audit_event=audit_event,
        )

    item_count, preview_payload = preview
    body = _operator_body(
        outcome="allowed",
        run_id=run_id,
        artifact_family=requested_artifact_family,
        preview_type=preview_type,
        item_count=item_count,
        preview_payload=preview_payload,
        audit_summary=audit_summary,
    )
    return OperatorOverlayPreviewResult(
        status_code=200,
        body=body,
        decision_status=decision.status,
        allowed=True,
        audit_event=audit_event,
    )


def _operator_body(
    *,
    outcome: str,
    run_id: str,
    artifact_family: str,
    preview_type: str,
    item_count: int | None,
    preview_payload: dict[str, Any] | None,
    audit_summary: dict[str, Any],
) -> dict[str, Any]:
    return {
        "outcome": outcome,
        "run_id": run_id,
        "artifact_family": artifact_family,
        "access_mode": ALLOWED_ACCESS_MODE,
        "preview_type": preview_type,
        "item_count": item_count,
        "preview_payload": preview_payload,
        "audit_event_summary": audit_summary,
        "filesystem_only": True,
        "http_servable": False,
        "downloadable_via_api": False,
        "frontend_visible": "operator_only",
    }


def _resolve_private_artifact_path(
    settings: Settings,
    run_id: str,
    artifact_family: str,
) -> Path:
    run_dir = get_run_dir(settings, run_id)
    relative = _FAMILY_RELATIVE_PATHS[artifact_family]
    return _safe_run_relative_path(run_dir, relative)


def _safe_run_relative_path(run_dir: str | Path, relative_path: str) -> Path:
    """Resolve a run-relative path under run_dir and reject traversal/absolute paths."""

    return resolve_run_output_path(run_dir, relative_path)


def _load_preview(
    artifact_family: str,
    artifact_path: Path,
) -> tuple[int, dict[str, Any]] | None:
    if not artifact_path.is_file():
        return None
    if artifact_family == PHASE_D1_GEOJSON_FAMILY_ID:
        return _load_geojson_preview(artifact_path)
    if artifact_family == PHASE_D2_KMZ_FAMILY_ID:
        return _load_kmz_preview(artifact_path)
    return _load_heatmap_preview(artifact_path)


def _load_geojson_preview(path: Path) -> tuple[int, dict[str, Any]] | None:
    document = _load_json(path)
    if not isinstance(document, Mapping) or document.get("type") != "FeatureCollection":
        return None
    features = document.get("features")
    if not isinstance(features, list):
        return None
    kinds: set[str] = set()
    for feature in features:
        if not isinstance(feature, Mapping):
            continue
        geometry = feature.get("geometry")
        if isinstance(geometry, Mapping):
            kind = geometry.get("type")
            if isinstance(kind, str) and kind:
                kinds.add(kind)
    return len(features), {"feature_count": len(features), "feature_kinds": sorted(kinds)}


def _load_kmz_preview(path: Path) -> tuple[int, dict[str, Any]] | None:
    try:
        with zipfile.ZipFile(path) as archive:
            if PRIVATE_KMZ_KML_FILENAME not in set(archive.namelist()):
                return None
            kml_text = archive.read(PRIVATE_KMZ_KML_FILENAME).decode("utf-8")
    except (OSError, zipfile.BadZipFile, UnicodeDecodeError):
        return None
    try:
        root = ET.fromstring(kml_text)
    except ET.ParseError:
        return None
    placemark_count = sum(1 for element in root.iter() if _local_name(element.tag) == "Placemark")
    return placemark_count, {"placemark_count": placemark_count}


def _load_heatmap_preview(path: Path) -> tuple[int, dict[str, Any]] | None:
    document = _load_json(path)
    if not isinstance(document, Mapping):
        return None
    points = document.get("points")
    if not isinstance(points, list):
        return None
    weights: list[float] = []
    for point in points:
        if not isinstance(point, Mapping):
            continue
        for key in _HEATMAP_NUMERIC_KEYS:
            value = point.get(key)
            if isinstance(value, bool):
                continue
            if isinstance(value, (int, float)) and math.isfinite(float(value)):
                weights.append(float(value))
                break
    payload: dict[str, Any] = {"point_count": len(points)}
    if weights:
        payload["weight_summary"] = {
            "min": round(min(weights), 6),
            "max": round(max(weights), 6),
            "mean": round(sum(weights) / len(weights), 6),
        }
    else:
        payload["weight_summary"] = None
    return len(points), payload


def _load_json(path: Path) -> object | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _local_name(tag: object) -> str:
    if not isinstance(tag, str):
        return ""
    return tag.split("}")[-1]


__all__ = [
    "OperatorOverlayPreviewResult",
    "ParityPathError",
    "build_operator_overlay_preview",
    "_safe_run_relative_path",
]
