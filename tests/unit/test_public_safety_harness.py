"""A4 public safety verification harness.

Tests-first verification that public API/schema surfaces do not expose exact
coordinates, coordinate-like strings, WKT/GeoJSON, CRS transforms, bounds/bbox,
local filesystem paths, hashes/checksums/fingerprints, coordinate-bearing CSV
columns, or private artifact paths/filenames. These tests assert existing
production behavior; they do not relax any safety rule.
"""

from __future__ import annotations

import ast
import inspect
import sys
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from pydantic import BaseModel, ValidationError

# Mock heavy geospatial/Earth Engine modules so that importing the API route
# modules (which transitively import pipeline stages) does not require rasterio
# or ee to be installed. This mirrors tests/unit/test_curvature_variants.py.
for _heavy_module in (
    "rasterio",
    "rasterio.transform",
    "rasterio.features",
    "rasterio.warp",
    "rasterio.enums",
    "ee",
):
    sys.modules.setdefault(_heavy_module, MagicMock())

from app.db.models import Artifact
from app.db.models.enums import ArtifactClass, RunStatus
from app.schemas.artifact import ArtifactPublic
from app.schemas.run import (
    CleanupRunSuggestionPublic,
    RunCleanupSummaryPublic,
    RunCreate,
    RunDeletePublic,
    RunDeletionAuditPublic,
    RunDeletionAuditRecordPublic,
    RunDetailPublic,
    RunHistoryEventPublic,
    RunPublic,
    RunStageProgressPublic,
)
from app.services.redaction import verify_redacted

# Forbidden public keys/values per the A4 contract.
FORBIDDEN_PUBLIC_KEYS = {
    "latitude",
    "longitude",
    "lat",
    "lon",
    "coordinates",
    "geometry",
    "bounds",
    "bbox",
    "transform",
    "path",
    "hash",
    "checksum",
    "fingerprint",
}

# Coordinate-bearing CSV-style column names that must never appear as public fields.
FORBIDDEN_CSV_COLUMN_KEYS = {
    "lat",
    "lon",
    "latitude",
    "longitude",
    "x",
    "y",
    "easting",
    "northing",
    "geometry",
    "wkt",
}

_NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _build_public_dtos() -> dict[str, BaseModel]:
    """Instantiate every public DTO with representative safe values."""
    stage = RunStageProgressPublic(name="dem", label="DEM", status="running")
    history_event = RunHistoryEventPublic(
        timestamp=_NOW,
        event_type="stage_started",
        label="DEM started",
        message="DEM stage started.",
        stage_name="dem",
    )
    artifact = ArtifactPublic(
        name="objects_index",
        artifact_class=ArtifactClass.REDACTED_PUBLIC,
        created_at=_NOW,
    )
    run_public = RunPublic(
        id="11111111-1111-1111-1111-111111111111",
        name="release run",
        status=RunStatus.DONE,
        created_at=_NOW,
        disk_usage_bytes=1024,
        output_file_count=3,
        last_disk_scan_at=_NOW,
    )
    run_detail = RunDetailPublic(
        id="11111111-1111-1111-1111-111111111111",
        name="release run",
        status=RunStatus.DONE,
        created_at=_NOW,
        disk_usage_bytes=1024,
        output_file_count=3,
        last_disk_scan_at=_NOW,
        current_stage="dem",
        stages=[stage],
        history=[history_event],
        artifacts=[artifact],
    )
    delete_public = RunDeletePublic(
        run_id="11111111-1111-1111-1111-111111111111",
        deleted=True,
        deleted_files_count=2,
        deleted_dirs_count=1,
        freed_bytes=4096,
        status="deleted",
        message="Run deleted.",
    )
    audit_record = RunDeletionAuditRecordPublic(
        run_id="11111111-1111-1111-1111-111111111111",
        run_name="release run",
        deleted_at=_NOW,
        deleted_files_count=2,
        deleted_dirs_count=1,
        freed_bytes=4096,
        status="deleted",
        message="Run deleted.",
    )
    audit_public = RunDeletionAuditPublic(total_freed_bytes=4096, records=[audit_record])
    suggestion = CleanupRunSuggestionPublic(
        id="11111111-1111-1111-1111-111111111111",
        name="release run",
        status=RunStatus.DONE,
        created_at=_NOW,
        disk_usage_bytes=1024,
        output_file_count=3,
        last_disk_scan_at=_NOW,
    )
    cleanup_summary = RunCleanupSummaryPublic(
        total_runs=1,
        total_disk_usage_bytes=1024,
        terminal_runs_count=1,
        active_runs_count=0,
        deleted_runs_count=0,
        total_freed_bytes=0,
        largest_runs=[suggestion],
        oldest_terminal_runs=[suggestion],
        stale_failed_runs=[],
        cleanup_recommended=False,
        warning_reason="Storage healthy.",
        threshold_bytes=10 * 1024 * 1024 * 1024,
    )
    return {
        "RunPublic": run_public,
        "RunDetailPublic": run_detail,
        "RunStageProgressPublic": stage,
        "RunHistoryEventPublic": history_event,
        "RunDeletePublic": delete_public,
        "RunDeletionAuditPublic": audit_public,
        "RunCleanupSummaryPublic": cleanup_summary,
        "ArtifactPublic": artifact,
    }


def _iter_keys(node: object):
    if isinstance(node, dict):
        for key, value in node.items():
            yield str(key)
            yield from _iter_keys(value)
    elif isinstance(node, (list, tuple)):
        for item in node:
            yield from _iter_keys(item)


# --- 1. Public DTO redaction verification -----------------------------------


@pytest.mark.parametrize("dto_name", sorted(_build_public_dtos()))
def test_public_dtos_pass_verify_redacted(dto_name: str) -> None:
    dto = _build_public_dtos()[dto_name]
    verify_redacted(dto.model_dump())


@pytest.mark.parametrize("dto_name", sorted(_build_public_dtos()))
def test_public_dtos_have_no_forbidden_keys(dto_name: str) -> None:
    dto = _build_public_dtos()[dto_name]
    keys = {key.casefold() for key in _iter_keys(dto.model_dump())}
    leaked = keys & FORBIDDEN_PUBLIC_KEYS
    assert leaked == set(), f"{dto_name} exposes forbidden public keys: {leaked}"


@pytest.mark.parametrize("dto_name", sorted(_build_public_dtos()))
def test_public_dtos_have_no_coordinate_bearing_csv_columns(dto_name: str) -> None:
    dto = _build_public_dtos()[dto_name]
    keys = {key.casefold() for key in _iter_keys(dto.model_dump())}
    leaked = keys & FORBIDDEN_CSV_COLUMN_KEYS
    assert leaked == set(), f"{dto_name} exposes coordinate-bearing CSV columns: {leaked}"


def test_artifact_public_does_not_expose_path_fields() -> None:
    field_names = {name.casefold() for name in ArtifactPublic.model_fields}
    assert "relative_path" not in field_names
    assert "path" not in field_names
    assert "absolute_path" not in field_names
    assert field_names == {"name", "artifact_class", "created_at"}


# --- 2. Run-name sanitization ------------------------------------------------


def test_run_create_accepts_safe_name() -> None:
    payload = RunCreate(lat=35.0, lon=36.0, name="release run")
    assert payload.name == "release run"


def test_run_create_accepts_missing_name() -> None:
    payload = RunCreate(lat=35.0, lon=36.0)
    assert payload.name is None


def test_run_create_accepts_private_local_coordinate_like_name() -> None:
    for name in ("35.12345, 36.54321", "near -12.3456,-45.6789"):
        payload = RunCreate(lat=35.0, lon=36.0, name=name)
        assert payload.name == name


@pytest.mark.parametrize(
    "term",
    [
        "latitude",
        "longitude",
        "coordinates",
        "geometry",
        "bbox",
        "transform",
        "path",
        "hash",
        "checksum",
        "fingerprint",
    ],
)
def test_run_create_accepts_private_local_terms_in_name(term: str) -> None:
    payload = RunCreate(lat=35.0, lon=36.0, name=f"my {term} run")
    assert payload.name == f"my {term} run"


# --- 3. Public artifact listing safety ---------------------------------------


def _artifact(name: str, relative_path: str, artifact_class: ArtifactClass) -> Artifact:
    return Artifact(
        run_id="run-1",
        name=name,
        relative_path=relative_path,
        size_bytes=1,
        sha256=None,
        artifact_class=artifact_class,
        http_servable=True,
    )


def test_redacted_public_artifact_is_listable() -> None:
    from app.api.runs import _is_publicly_listable_artifact

    artifact = _artifact("objects_index", "objects_index.csv", ArtifactClass.REDACTED_PUBLIC)
    assert _is_publicly_listable_artifact(artifact) is True


def test_preview_only_artifact_is_listable() -> None:
    from app.api.runs import _is_publicly_listable_artifact

    artifact = _artifact("preview", "preview.png", ArtifactClass.PREVIEW_ONLY)
    assert _is_publicly_listable_artifact(artifact) is True


def test_local_sensitive_artifact_is_not_listable() -> None:
    from app.api.runs import _is_publicly_listable_artifact

    artifact = _artifact("internal_array", "internal.npy", ArtifactClass.LOCAL_SENSITIVE)
    assert _is_publicly_listable_artifact(artifact) is False


def test_filesystem_only_artifact_is_not_listable() -> None:
    from app.api.runs import _is_publicly_listable_artifact

    artifact = _artifact("kmz_bundle", "exports/site.kmz", ArtifactClass.FILESYSTEM_ONLY)
    assert _is_publicly_listable_artifact(artifact) is False


def test_experimental_named_redacted_public_artifact_is_listable() -> None:
    from app.api.runs import _is_publicly_listable_artifact

    artifact = _artifact("experimental_summary", "summary.json", ArtifactClass.REDACTED_PUBLIC)
    assert _is_publicly_listable_artifact(artifact) is True


def test_experimental_relative_path_redacted_public_artifact_is_listable() -> None:
    from app.api.runs import _is_publicly_listable_artifact

    artifact = _artifact("summary", "experimental/summary.json", ArtifactClass.REDACTED_PUBLIC)
    assert _is_publicly_listable_artifact(artifact) is True


# --- 4. Artifact download route safety (static / AST) ------------------------

API_MODULES = (
    "app.api.runs",
    "app.api.artifacts",
    "app.api.earth_engine",
    "app.api.operator_overlays",
    "app.api.roi_preview",
    "app.api.health",
)


@pytest.mark.parametrize("module_name", API_MODULES)
def test_api_modules_do_not_construct_file_or_streaming_responses(module_name: str) -> None:
    """API route modules must not build FileResponse/StreamingResponse directly.

    All artifact byte serving must flow through the approved
    ``serve_artifact_response`` / ``serve_operator_output_response`` service.
    """
    import importlib

    module = importlib.import_module(module_name)
    source = inspect.getsource(module)
    tree = ast.parse(source)

    called_names = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert "FileResponse" not in called_names, f"{module_name} constructs FileResponse directly"
    assert "StreamingResponse" not in called_names, f"{module_name} constructs StreamingResponse directly"
    # Defense in depth: the symbols should not even be referenced in route modules.
    assert "StreamingResponse" not in source, f"{module_name} references StreamingResponse"


def test_artifacts_routes_delegate_to_serve_artifact_response() -> None:
    import app.api.artifacts as artifacts_module

    source = inspect.getsource(artifacts_module)
    assert "serve_artifact_response" in source
    assert "serve_operator_output_response" in source
    assert "FileResponse" not in source


def test_only_artifact_response_service_constructs_file_response() -> None:
    import app.services.artifact_response as service_module

    source = inspect.getsource(service_module)
    assert "FileResponse" in source
    # The serving service is gated by can_serve_artifact.
    assert "can_serve_artifact" in source
