from __future__ import annotations

import json
from fnmatch import fnmatchcase
from pathlib import Path
from typing import Any
from urllib.parse import quote

from app.config import Settings
from app.errors import ArtifactServeViolation
from app.schemas.operator_output import OperatorOutputFilePublic, OperatorOutputStatusPublic, OperatorOutputTreePublic
from app.services.storage import get_run_dir, resolve_run_artifact_path

SENSITIVE_FILENAMES = {
    ".env".casefold(),
    "PATH_MAP.local.json".casefold(),
}
SENSITIVE_SUFFIXES = (
    ".db",
    ".db-shm",
    ".db-wal",
    ".sqlite",
    ".sqlite3",
    ".log",
)
SENSITIVE_NAME_PARTS = (
    "service-account",
    "service_account",
    "credential",
    "credentials",
    "private-key",
    "private_key",
)
STATUS_NOT_IMPLEMENTED = "not_implemented_no_source_equivalent"
OPERATOR_VISIBLE_PATTERNS = (
    "DEM_GEO8_TIFS/*",
    "GEOTIFF_RADAR_BANDS/*",
    "NPY_RADAR_BANDS/*",
    "NPY_STACKS/*",
    "AI_READY_640/*.tif",
    "REPORT_640_*.tif",
    "QA/RUN_MANIFEST.json",
    "QA/REPORT_640_manifest.json",
    "QA/QA_GRID_*.tif",
    "QA/grid_dem/grid_guard_summary.json",
    "QA/grid_dem/dem_audit_summary.json",
    "QA/grid_dem/drift_audit.csv",
    "QA/sar/sar_pair_diagnostics.json",
    "QA/sar/sar_summary.csv",
    "QA/sar/sar_nodata_audit.csv",
    "QA/sar/sar_alignment_summary.json",
    "QA/sar/intermediates/sar_intermediate_manifest.json",
    "QA/sar/intermediates/post_rtc/*.npy",
    "QA/stacks/secret_layers_manifest.json",
    "QA/stacks/s2_indices_summary.json",
    "QA/stacks/thermal_summary.json",
    "NDVI.tif",
    "NDWI.tif",
    "NDMI.tif",
    "NBR.tif",
    "IRONOX.tif",
    "IRON_SWIR.tif",
    "BSI.tif",
    "lst.tif",
    "pca_anomaly.tif",
    "pca_eigenvalues.json",
    "hypercube.tif",
    "hypercube.npy",
    "hypercube_band_order.csv",
    "hypercube_band_stats.csv",
    "hypercube_norm_params.csv",
    "objects_index.csv",
    "clusters_summary.csv",
    "alignment_qa.json",
    "alignment_audit.csv",
    "alignment_mask_selection.json",
)


def build_operator_output_tree(*, settings: Settings, run_id: str) -> OperatorOutputTreePublic:
    run_dir = get_run_dir(settings, run_id)
    not_implemented = _collect_not_implemented(settings=settings, run_id=run_id)
    not_implemented_paths = {item.relative_path for item in not_implemented}
    outputs: list[OperatorOutputFilePublic] = []
    if run_dir.is_dir():
        for path in sorted((item for item in run_dir.rglob("*") if item.is_file()), key=_relative_sort_key(run_dir)):
            relative_path = path.relative_to(run_dir).as_posix()
            if not is_operator_visible_relative_path(relative_path):
                continue
            if relative_path in not_implemented_paths:
                continue
            outputs.append(_to_output_file(run_id=run_id, run_dir=run_dir, path=path))

    return OperatorOutputTreePublic(
        run_id=run_id,
        outputs=outputs,
        not_implemented=not_implemented,
    )


def resolve_operator_output_path(settings: Settings, run_id: str, relative_path: str) -> Path:
    if not is_operator_visible_relative_path(relative_path):
        raise ArtifactServeViolation()
    if relative_path in {item.relative_path for item in _collect_not_implemented(settings=settings, run_id=run_id)}:
        raise ArtifactServeViolation()
    path = resolve_run_artifact_path(settings, run_id, relative_path)
    if not path.is_file():
        raise ArtifactServeViolation()
    return path


def is_safe_operator_output_relative_path(relative_path: str) -> bool:
    try:
        parts = Path(relative_path).parts
    except (OSError, ValueError):
        return False
    if not parts:
        return False
    normalized = relative_path.replace("\\", "/")
    if normalized.startswith("/") or ".." in parts:
        return False
    if any(part in {"", ".", ".."} for part in parts):
        return False
    if any(part.startswith(".") for part in parts):
        return False
    lowered_parts = [part.casefold() for part in parts]
    if any(part in SENSITIVE_FILENAMES for part in lowered_parts):
        return False
    if any(part.endswith(SENSITIVE_SUFFIXES) for part in lowered_parts):
        return False
    for part in lowered_parts:
        for token in SENSITIVE_NAME_PARTS:
            if token in part:
                return False
        if "secret" in part:
            # Allow known notebook-compatible secret layer names and manifest
            if part.startswith("ai_ready_640_secret_") or part == "secret_layers_manifest.json":
                continue
            return False
    return True


def is_operator_visible_relative_path(relative_path: str) -> bool:
    normalized = relative_path.replace("\\", "/")
    if not is_safe_operator_output_relative_path(normalized):
        return False
    return any(fnmatchcase(normalized, pattern) for pattern in OPERATOR_VISIBLE_PATTERNS)


def _to_output_file(*, run_id: str, run_dir: Path, path: Path) -> OperatorOutputFilePublic:
    relative_path = path.relative_to(run_dir).as_posix()
    directory = path.parent.relative_to(run_dir).as_posix()
    if directory == ".":
        directory = ""
    extension = path.suffix
    return OperatorOutputFilePublic(
        relative_path=relative_path,
        filename=path.name,
        directory=directory,
        group=_group_for_relative_path(relative_path),
        size_bytes=path.stat().st_size,
        extension=extension,
        file_type=extension.removeprefix(".") or "file",
        status="implemented",
        download_url=f"/runs/{quote(run_id, safe='')}/outputs/download/{quote(relative_path, safe='/')}",
    )


def _collect_not_implemented(*, settings: Settings, run_id: str) -> list[OperatorOutputStatusPublic]:
    run_dir = get_run_dir(settings, run_id)
    items: list[OperatorOutputStatusPublic] = []
    items.extend(_read_report_640_manifest(run_dir / "QA" / "REPORT_640_manifest.json"))
    items.extend(_read_sar_intermediate_manifest(run_dir / "QA" / "sar" / "intermediates" / "sar_intermediate_manifest.json"))
    items.extend(_read_hypercube_manifest(run_dir / "stage_hypercube.manifest.json"))
    items.extend(_read_secret_layers_manifest(run_dir / "QA" / "stacks" / "secret_layers_manifest.json"))
    return sorted(
        (item for item in items if is_operator_visible_relative_path(item.relative_path)),
        key=lambda item: item.relative_path,
    )


def _read_report_640_manifest(path: Path) -> list[OperatorOutputStatusPublic]:
    payload = _read_json(path)
    reports = payload.get("reports") if isinstance(payload, dict) else None
    if not isinstance(reports, dict):
        return []
    items: list[OperatorOutputStatusPublic] = []
    for filename, report_payload in reports.items():
        if not isinstance(filename, str) or not isinstance(report_payload, dict):
            continue
        status = report_payload.get("status")
        if status != STATUS_NOT_IMPLEMENTED:
            continue
        items.append(_not_implemented_item(relative_path=filename, source="QA/REPORT_640_manifest.json"))
    return items


def _read_sar_intermediate_manifest(path: Path) -> list[OperatorOutputStatusPublic]:
    payload = _read_json(path)
    stages = payload.get("stages") if isinstance(payload, dict) else None
    if not isinstance(stages, dict):
        return []
    items: list[OperatorOutputStatusPublic] = []
    for stage_name, stage_payload in stages.items():
        if not isinstance(stage_name, str) or not isinstance(stage_payload, dict):
            continue
        if stage_payload.get("status") != STATUS_NOT_IMPLEMENTED:
            continue
        bands = stage_payload.get("bands")
        if isinstance(bands, dict):
            for relative_path in bands.values():
                if not isinstance(relative_path, str):
                    continue
                items.append(
                    _not_implemented_item(
                        relative_path=f"QA/sar/intermediates/{relative_path}",
                        source="QA/sar/intermediates/sar_intermediate_manifest.json",
                    )
                )
            continue
        items.append(
            _not_implemented_item(
                relative_path=f"QA/sar/intermediates/{stage_name}",
                source="QA/sar/intermediates/sar_intermediate_manifest.json",
            )
        )
    return items


def _read_hypercube_manifest(path: Path) -> list[OperatorOutputStatusPublic]:
    payload = _read_json(path)
    metadata = payload.get("metadata") if isinstance(payload, dict) else None
    if not isinstance(metadata, dict):
        return []
    notebook_statuses = metadata.get("notebook_output_statuses")
    if not isinstance(notebook_statuses, list):
        return []
    items: list[OperatorOutputStatusPublic] = []
    for item in notebook_statuses:
        if not isinstance(item, dict):
            continue
        filename = item.get("filename")
        status = item.get("status")
        if not isinstance(filename, str) or status != STATUS_NOT_IMPLEMENTED:
            continue
        items.append(_not_implemented_item(relative_path=f"NPY_STACKS/{filename}", source="stage_hypercube.manifest.json"))
    return items


def _read_secret_layers_manifest(path: Path) -> list[OperatorOutputStatusPublic]:
    payload = _read_json(path)
    if not isinstance(payload, dict):
        return []
    not_implemented = payload.get("not_implemented")
    if not isinstance(not_implemented, list):
        return []
    items: list[OperatorOutputStatusPublic] = []
    for layer in not_implemented:
        if not isinstance(layer, dict):
            continue
        name = layer.get("name")
        status = layer.get("status")
        if not isinstance(name, str) or status != STATUS_NOT_IMPLEMENTED:
            continue
        items.append(
            _not_implemented_item(
                relative_path=f"AI_READY_640/{name}.tif",
                source="QA/stacks/secret_layers_manifest.json",
            )
        )
    return items


def _not_implemented_item(*, relative_path: str, source: str) -> OperatorOutputStatusPublic:
    path = Path(relative_path)
    directory = path.parent.as_posix()
    if directory == ".":
        directory = ""
    return OperatorOutputStatusPublic(
        relative_path=relative_path,
        filename=path.name,
        directory=directory,
        group=_group_for_relative_path(relative_path),
        status=STATUS_NOT_IMPLEMENTED,
        source=source,
    )


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _group_for_relative_path(relative_path: str) -> str:
    first = relative_path.split("/", 1)[0]
    return first if "/" in relative_path else "root"


def _relative_sort_key(run_dir: Path):
    def sort_key(path: Path) -> str:
        return path.relative_to(run_dir).as_posix().casefold()

    return sort_key
