from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import json
import math
from pathlib import Path
from typing import Any, Iterable, Mapping
import xml.etree.ElementTree as ET
import zipfile

from app.pipeline.parity import resolve_run_output_path


PHASE_E4_PRIVATE_MAP_ARTIFACT_COMPARATOR_SCHEMA_VERSION = (
    "phase_e4_private_map_artifact_comparator_v1"
)
PHASE_E4_PRIVATE_MAP_ARTIFACT_COMPARATOR_REPORT_RELATIVE_PATH = (
    "manifests/phase_e4_private_map_artifact_comparator.json"
)
PHASE_E4_COMPARATOR_ID = "phase_e4_private_map_artifact_comparator"

PHASE_D1_GEOJSON_FAMILY_ID = "phase_d1_private_geojson"
PHASE_D2_KMZ_FAMILY_ID = "phase_d2_private_kmz"
PHASE_D3_HEATMAP_FAMILY_ID = "phase_d3_private_heatmap_json"


@dataclass(frozen=True)
class _FamilySpec:
    family_id: str
    artifact_name: str
    artifact_type: str
    relative_path: str


# Canonical Phase D private map artifacts. Relative paths mirror the existing
# Phase D writers in app.pipeline.parity.private_map_artifact_writers. This module
# only reads existing artifacts; it does not write or change writer behavior.
PHASE_D_PRIVATE_MAP_ARTIFACT_SPECS: tuple[_FamilySpec, ...] = (
    _FamilySpec(
        family_id=PHASE_D1_GEOJSON_FAMILY_ID,
        artifact_name="private_features.geojson",
        artifact_type="GeoJSON FeatureCollection",
        relative_path="private_map_artifacts/geojson/private_features.geojson",
    ),
    _FamilySpec(
        family_id=PHASE_D2_KMZ_FAMILY_ID,
        artifact_name="private_points.kmz",
        artifact_type="KMZ",
        relative_path="private_map_artifacts/kmz/private_points.kmz",
    ),
    _FamilySpec(
        family_id=PHASE_D3_HEATMAP_FAMILY_ID,
        artifact_name="private_heatmap.json",
        artifact_type="Private Heatmap JSON",
        relative_path="private_map_artifacts/heatmap/private_heatmap.json",
    ),
)

PHASE_D_PRIVATE_MAP_ARTIFACT_FAMILIES: tuple[str, ...] = tuple(
    spec.family_id for spec in PHASE_D_PRIVATE_MAP_ARTIFACT_SPECS
)
_SPEC_BY_FAMILY: dict[str, _FamilySpec] = {
    spec.family_id: spec for spec in PHASE_D_PRIVATE_MAP_ARTIFACT_SPECS
}

PHASE_D2_KMZ_EXPECTED_KML_FILENAME = "doc.kml"
PHASE_D3_HEATMAP_NUMERIC_KEYS: tuple[str, ...] = (
    "weight",
    "score",
    "probability",
    "uncertainty",
    "rank",
)

ALLOWED_PHASE_E4_RESULT_STATUSES = {
    "passed",
    "failed",
    "reference_missing",
    "app_output_missing",
    "comparison_unavailable",
    "skipped_by_request",
    "error",
}

ALLOWED_PHASE_E4_OVERALL_STATUSES = {
    "passed",
    "failed",
    "incomplete",
    "comparison_unavailable",
    "error",
}


@dataclass(frozen=True)
class PhaseDPrivateMapArtifactComparatorResult:
    report_path: Path
    selected_artifacts: tuple[str, ...]
    results: tuple[dict[str, object], ...]
    overall_status: str
    runtime_output_verified: bool
    notebook_value_parity_verified: bool


def compare_phase_d_private_map_artifacts(
    *,
    app_output_dir: str | Path,
    reference_bundle_dir: str | Path,
    run_dir: str | Path,
    run_id: str,
    selected_artifacts: Iterable[str] | None = None,
    skipped_artifacts: Iterable[str] | None = None,
    coordinate_atol: float = 1e-6,
    weight_atol: float = 1e-6,
    report_relative_path: str | Path = PHASE_E4_PRIVATE_MAP_ARTIFACT_COMPARATOR_REPORT_RELATIVE_PATH,
) -> PhaseDPrivateMapArtifactComparatorResult:
    """Compare private Phase D map artifacts against frozen references.

    This is comparator/verifier work only. It reads existing Phase D private map
    artifacts and frozen notebook references and does not generate app outputs,
    change writer behavior, call Earth Engine, or expose private artifacts.
    """

    app_root = Path(app_output_dir)
    reference_root = Path(reference_bundle_dir)
    report_path = resolve_run_output_path(run_dir, report_relative_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    selected = _validate_selected_artifacts(selected_artifacts)
    skip_set = _validate_skip_artifacts(skipped_artifacts, selected)

    results = tuple(
        _compare_one_family(
            family_id,
            app_root=app_root,
            reference_root=reference_root,
            coordinate_atol=coordinate_atol,
            weight_atol=weight_atol,
            skipped=family_id in skip_set,
        )
        for family_id in selected
    )
    overall_status = _overall_status(results)
    runtime_output_verified = bool(results) and all(
        bool(item["app_output_present"]) for item in results
    )
    notebook_value_parity_verified = overall_status == "passed"

    payload = {
        "schema_version": PHASE_E4_PRIVATE_MAP_ARTIFACT_COMPARATOR_SCHEMA_VERSION,
        "run_id": run_id,
        "created_at": datetime.now(UTC).isoformat(),
        "comparator_id": PHASE_E4_COMPARATOR_ID,
        "selected_artifacts": list(selected),
        "results": list(results),
        "counts_by_status": _counts_by_status(results),
        "overall_status": overall_status,
        "runtime_output_verified": runtime_output_verified,
        "notebook_value_parity_verified": notebook_value_parity_verified,
        "reference_bundle_dir": str(reference_root),
        "app_output_dir": str(app_root),
        "report_path": str(report_path),
        "phase_e4_comparator_only": True,
        "runtime_added": False,
        "writer_added": False,
        "earth_engine_calls_added": False,
        "public_exposure_changes": False,
        "artifact_generation": False,
        "notes": (
            "Phase E4 compares private Phase D map artifacts (GeoJSON, KMZ, heatmap "
            "JSON) against frozen references. It does not create map artifacts or "
            "expose private artifacts through API, frontend, downloads, or overlays."
        ),
    }
    report_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return PhaseDPrivateMapArtifactComparatorResult(
        report_path=report_path,
        selected_artifacts=selected,
        results=results,
        overall_status=overall_status,
        runtime_output_verified=runtime_output_verified,
        notebook_value_parity_verified=notebook_value_parity_verified,
    )


def _compare_one_family(
    family_id: str,
    *,
    app_root: Path,
    reference_root: Path,
    coordinate_atol: float,
    weight_atol: float,
    skipped: bool,
) -> dict[str, object]:
    spec = _SPEC_BY_FAMILY[family_id]
    base = _base_result(spec, coordinate_atol=coordinate_atol, weight_atol=weight_atol)

    if skipped:
        return _finish(base, status="skipped_by_request", notes="Skipped at caller request.")

    app_path = _locate_artifact_file(app_root, spec)
    reference_path = _locate_reference_file(reference_root, spec)
    base["app_output_present"] = app_path is not None
    base["reference_present"] = reference_path is not None

    if app_path is None:
        return _finish(base, status="app_output_missing", notes="App output artifact is missing.")
    if reference_path is None:
        return _finish(
            base,
            status="reference_missing",
            runtime_output_verified=True,
            notes="Frozen reference artifact is missing.",
        )

    if family_id == PHASE_D1_GEOJSON_FAMILY_ID:
        return _compare_geojson(base, app_path, reference_path, coordinate_atol=coordinate_atol)
    if family_id == PHASE_D2_KMZ_FAMILY_ID:
        return _compare_kmz(base, app_path, reference_path, coordinate_atol=coordinate_atol)
    return _compare_heatmap(
        base,
        app_path,
        reference_path,
        coordinate_atol=coordinate_atol,
        weight_atol=weight_atol,
    )


# ---------------------------------------------------------------------------
# GeoJSON comparison
# ---------------------------------------------------------------------------
def _compare_geojson(
    base: dict[str, object],
    app_path: Path,
    reference_path: Path,
    *,
    coordinate_atol: float,
) -> dict[str, object]:
    app_doc = _load_json(app_path)
    reference_doc = _load_json(reference_path)
    if app_doc is None or reference_doc is None:
        return _finish(
            base,
            status="error",
            runtime_output_verified=True,
            notes="GeoJSON artifact could not be parsed as JSON.",
        )

    app_features = _feature_collection_features(app_doc)
    reference_features = _feature_collection_features(reference_doc)
    structure_match = app_features is not None and reference_features is not None
    base["structure_match"] = structure_match
    base["private_content_compared"] = True
    if not structure_match:
        return _finish(
            base,
            status="failed",
            runtime_output_verified=True,
            notes="GeoJSON structure is not a valid FeatureCollection.",
        )

    count_match = len(app_features) == len(reference_features)
    base["count_match"] = count_match
    if not count_match:
        return _finish(
            base,
            status="failed",
            runtime_output_verified=True,
            notes="GeoJSON feature count differs.",
        )

    diffs: list[float] = []
    for app_feature, reference_feature in zip(app_features, reference_features):
        app_geometry = app_feature.get("geometry") if isinstance(app_feature, Mapping) else None
        reference_geometry = (
            reference_feature.get("geometry") if isinstance(reference_feature, Mapping) else None
        )
        if not isinstance(app_geometry, Mapping) or not isinstance(reference_geometry, Mapping):
            return _finish(
                base,
                status="failed",
                runtime_output_verified=True,
                notes="GeoJSON feature geometry is malformed.",
            )
        if app_geometry.get("type") != reference_geometry.get("type"):
            return _finish(
                base,
                status="failed",
                runtime_output_verified=True,
                notes="GeoJSON geometry type differs.",
            )
        app_coords = _flatten_numbers(app_geometry.get("coordinates"))
        reference_coords = _flatten_numbers(reference_geometry.get("coordinates"))
        if app_coords is None or reference_coords is None or len(app_coords) != len(reference_coords):
            return _finish(
                base,
                status="failed",
                runtime_output_verified=True,
                notes="GeoJSON coordinate structure differs.",
            )
        diffs.extend(abs(a - b) for a, b in zip(app_coords, reference_coords))

    return _finalize_numeric(
        base,
        diffs=diffs,
        atol=coordinate_atol,
        match_notes="GeoJSON features match within coordinate tolerance.",
        mismatch_notes="GeoJSON coordinates differ outside tolerance.",
    )


# ---------------------------------------------------------------------------
# KMZ comparison
# ---------------------------------------------------------------------------
def _compare_kmz(
    base: dict[str, object],
    app_path: Path,
    reference_path: Path,
    *,
    coordinate_atol: float,
) -> dict[str, object]:
    base["private_content_compared"] = True
    app_kml = _read_kmz_doc_kml(app_path)
    reference_kml = _read_kmz_doc_kml(reference_path)
    if app_kml is _KMZ_UNREADABLE or reference_kml is _KMZ_UNREADABLE:
        return _finish(
            base,
            status="error",
            runtime_output_verified=True,
            notes="KMZ archive could not be opened as a ZIP container.",
        )

    structure_match = app_kml is not None and reference_kml is not None
    base["structure_match"] = structure_match
    if not structure_match:
        return _finish(
            base,
            status="failed",
            runtime_output_verified=True,
            notes=f"KMZ is missing the expected {PHASE_D2_KMZ_EXPECTED_KML_FILENAME} entry.",
        )

    app_placemarks = _parse_kml_placemarks(app_kml)
    reference_placemarks = _parse_kml_placemarks(reference_kml)
    if app_placemarks is None or reference_placemarks is None:
        return _finish(
            base,
            status="error",
            runtime_output_verified=True,
            notes="KMZ doc.kml could not be parsed as XML.",
        )

    count_match = len(app_placemarks) == len(reference_placemarks)
    base["count_match"] = count_match
    if not count_match:
        return _finish(
            base,
            status="failed",
            runtime_output_verified=True,
            notes="KMZ placemark count differs.",
        )

    diffs: list[float] = []
    for app_mark, reference_mark in zip(app_placemarks, reference_placemarks):
        if app_mark["name"] != reference_mark["name"]:
            return _finish(
                base,
                status="failed",
                runtime_output_verified=True,
                notes="KMZ placemark structural signature differs.",
            )
        app_coords = app_mark["coordinates"]
        reference_coords = reference_mark["coordinates"]
        if len(app_coords) != len(reference_coords):
            return _finish(
                base,
                status="failed",
                runtime_output_verified=True,
                notes="KMZ placemark coordinate structure differs.",
            )
        diffs.extend(abs(a - b) for a, b in zip(app_coords, reference_coords))

    return _finalize_numeric(
        base,
        diffs=diffs,
        atol=coordinate_atol,
        match_notes="KMZ placemarks match within coordinate tolerance.",
        mismatch_notes="KMZ placemark coordinates differ outside tolerance.",
    )


# ---------------------------------------------------------------------------
# Heatmap JSON comparison
# ---------------------------------------------------------------------------
def _compare_heatmap(
    base: dict[str, object],
    app_path: Path,
    reference_path: Path,
    *,
    coordinate_atol: float,
    weight_atol: float,
) -> dict[str, object]:
    base["private_content_compared"] = True
    app_doc = _load_json(app_path)
    reference_doc = _load_json(reference_path)
    if not isinstance(app_doc, Mapping) or not isinstance(reference_doc, Mapping):
        return _finish(
            base,
            status="error",
            runtime_output_verified=True,
            notes="Heatmap JSON could not be parsed as a JSON object.",
        )

    if app_doc.get("schema_version") != reference_doc.get("schema_version"):
        base["structure_match"] = False
        return _finish(
            base,
            status="failed",
            runtime_output_verified=True,
            notes="Heatmap schema_version differs.",
        )

    app_points = app_doc.get("points")
    reference_points = reference_doc.get("points")
    structure_match = isinstance(app_points, list) and isinstance(reference_points, list)
    base["structure_match"] = structure_match
    if not structure_match:
        return _finish(
            base,
            status="failed",
            runtime_output_verified=True,
            notes="Heatmap points payload is not a list.",
        )

    count_match = len(app_points) == len(reference_points)
    base["count_match"] = count_match
    if not count_match:
        return _finish(
            base,
            status="failed",
            runtime_output_verified=True,
            notes="Heatmap point count differs.",
        )

    coordinate_diffs: list[float] = []
    weight_diffs: list[float] = []
    for app_point, reference_point in zip(app_points, reference_points):
        if not isinstance(app_point, Mapping) or not isinstance(reference_point, Mapping):
            return _finish(
                base,
                status="failed",
                runtime_output_verified=True,
                notes="Heatmap point payload is malformed.",
            )
        for field_name in ("latitude", "longitude"):
            app_value = _as_finite_float(app_point.get(field_name))
            reference_value = _as_finite_float(reference_point.get(field_name))
            if app_value is None or reference_value is None:
                return _finish(
                    base,
                    status="failed",
                    runtime_output_verified=True,
                    notes="Heatmap coordinate field is missing or non-numeric.",
                )
            coordinate_diffs.append(abs(app_value - reference_value))
        if set(_present_numeric_keys(app_point)) != set(_present_numeric_keys(reference_point)):
            return _finish(
                base,
                status="failed",
                runtime_output_verified=True,
                notes="Heatmap weight/score fields differ structurally.",
            )
        for key in _present_numeric_keys(app_point):
            app_value = _as_finite_float(app_point.get(key))
            reference_value = _as_finite_float(reference_point.get(key))
            if app_value is None or reference_value is None:
                return _finish(
                    base,
                    status="failed",
                    runtime_output_verified=True,
                    notes="Heatmap weight/score field is non-numeric.",
                )
            weight_diffs.append(abs(app_value - reference_value))

    max_abs_error = max([*coordinate_diffs, *weight_diffs], default=0.0)
    mean_values = [*coordinate_diffs, *weight_diffs]
    mean_abs_error = (sum(mean_values) / len(mean_values)) if mean_values else 0.0
    base["max_abs_error"] = max_abs_error
    base["mean_abs_error"] = mean_abs_error

    coordinate_ok = all(diff <= coordinate_atol for diff in coordinate_diffs)
    weight_ok = all(diff <= weight_atol for diff in weight_diffs)
    if coordinate_ok and weight_ok:
        return _finish(
            base,
            status="passed",
            runtime_output_verified=True,
            notebook_value_parity_verified=True,
            notes="Heatmap points match within tolerance.",
        )
    return _finish(
        base,
        status="failed",
        runtime_output_verified=True,
        notes="Heatmap weights/scores or coordinates differ outside tolerance.",
    )


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------
def _finalize_numeric(
    base: dict[str, object],
    *,
    diffs: list[float],
    atol: float,
    match_notes: str,
    mismatch_notes: str,
) -> dict[str, object]:
    max_abs_error = max(diffs, default=0.0)
    mean_abs_error = (sum(diffs) / len(diffs)) if diffs else 0.0
    base["max_abs_error"] = max_abs_error
    base["mean_abs_error"] = mean_abs_error
    if all(diff <= atol for diff in diffs):
        return _finish(
            base,
            status="passed",
            runtime_output_verified=True,
            notebook_value_parity_verified=True,
            notes=match_notes,
        )
    return _finish(
        base,
        status="failed",
        runtime_output_verified=True,
        notes=mismatch_notes,
    )


def _base_result(
    spec: _FamilySpec,
    *,
    coordinate_atol: float,
    weight_atol: float,
) -> dict[str, object]:
    return {
        "artifact_name": spec.artifact_name,
        "family_id": spec.family_id,
        "artifact_type": spec.artifact_type,
        "status": "comparison_unavailable",
        "app_output_present": False,
        "reference_present": False,
        "structure_match": None,
        "count_match": None,
        "tolerance": {
            "coordinate_atol": float(coordinate_atol),
            "weight_atol": float(weight_atol),
        },
        "max_abs_error": None,
        "mean_abs_error": None,
        "private_content_compared": False,
        "runtime_output_verified": False,
        "notebook_value_parity_verified": False,
        "redacted_summary": {},
        "notes": "",
    }


def _finish(
    item: dict[str, object],
    *,
    status: str,
    notes: str,
    runtime_output_verified: bool = False,
    notebook_value_parity_verified: bool = False,
) -> dict[str, object]:
    if status not in ALLOWED_PHASE_E4_RESULT_STATUSES:
        raise ValueError(f"unsupported Phase E4 result status: {status}")
    item["status"] = status
    item["runtime_output_verified"] = runtime_output_verified
    item["notebook_value_parity_verified"] = notebook_value_parity_verified
    item["notes"] = notes
    item["redacted_summary"] = _redacted_summary(item)
    return item


def _redacted_summary(item: Mapping[str, object]) -> dict[str, object]:
    """Build a public-safe summary.

    The redacted summary intentionally excludes coordinates, raw geometry, KML
    contents, heatmap point payloads, error magnitudes, local filesystem paths,
    private hashes, and download URLs. It carries only structural status flags and
    integer-free boolean/enumeration fields.
    """

    return {
        "family_id": item["family_id"],
        "status": item["status"],
        "app_output_present": item["app_output_present"],
        "reference_present": item["reference_present"],
        "structure_match": item["structure_match"],
        "count_match": item["count_match"],
        "private_content_compared": item["private_content_compared"],
        "runtime_output_verified": item["runtime_output_verified"],
        "notebook_value_parity_verified": item["notebook_value_parity_verified"],
        "private_boundary": "filesystem_only; not http-servable; not frontend-visible",
    }


def _validate_selected_artifacts(
    selected_artifacts: Iterable[str] | None,
) -> tuple[str, ...]:
    selected = tuple(selected_artifacts or PHASE_D_PRIVATE_MAP_ARTIFACT_FAMILIES)
    unknown = sorted(set(selected) - set(PHASE_D_PRIVATE_MAP_ARTIFACT_FAMILIES))
    if unknown:
        raise ValueError(
            f"unsupported Phase D private map artifact families: {', '.join(unknown)}"
        )
    return selected


def _validate_skip_artifacts(
    skipped_artifacts: Iterable[str] | None,
    selected: tuple[str, ...],
) -> frozenset[str]:
    skip_set = frozenset(skipped_artifacts or ())
    unknown = sorted(skip_set - set(PHASE_D_PRIVATE_MAP_ARTIFACT_FAMILIES))
    if unknown:
        raise ValueError(
            f"unsupported Phase D skip families: {', '.join(unknown)}"
        )
    return frozenset(family_id for family_id in skip_set if family_id in selected)


def _locate_artifact_file(root: Path, spec: _FamilySpec) -> Path | None:
    direct = root / spec.relative_path
    if direct.is_file():
        return direct
    return _rglob_first(root, spec.artifact_name)


def _locate_reference_file(root: Path, spec: _FamilySpec) -> Path | None:
    candidates = (
        root / spec.relative_path,
        root / "references" / spec.family_id / spec.artifact_name,
        root / spec.artifact_name,
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return _rglob_first(root, spec.artifact_name)


def _rglob_first(root: Path, filename: str) -> Path | None:
    if not root.is_dir():
        return None
    for path in sorted(root.rglob(filename)):
        if path.is_file():
            return path
    return None


def _load_json(path: Path) -> object | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _feature_collection_features(doc: object) -> list[object] | None:
    if not isinstance(doc, Mapping):
        return None
    if doc.get("type") != "FeatureCollection":
        return None
    features = doc.get("features")
    if not isinstance(features, list):
        return None
    return features


def _flatten_numbers(value: object) -> list[float] | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        if not math.isfinite(float(value)):
            return None
        return [float(value)]
    if isinstance(value, (str, bytes, bytearray)):
        return None
    if isinstance(value, Iterable):
        flattened: list[float] = []
        for item in value:
            nested = _flatten_numbers(item)
            if nested is None:
                return None
            flattened.extend(nested)
        return flattened
    return None


_KMZ_UNREADABLE = object()


def _read_kmz_doc_kml(path: Path) -> str | None | object:
    try:
        with zipfile.ZipFile(path) as archive:
            names = set(archive.namelist())
            if PHASE_D2_KMZ_EXPECTED_KML_FILENAME not in names:
                return None
            return archive.read(PHASE_D2_KMZ_EXPECTED_KML_FILENAME).decode("utf-8")
    except (OSError, zipfile.BadZipFile, UnicodeDecodeError):
        return _KMZ_UNREADABLE


def _parse_kml_placemarks(kml_text: str) -> list[dict[str, object]] | None:
    try:
        root = ET.fromstring(kml_text)
    except ET.ParseError:
        return None
    placemarks: list[dict[str, object]] = []
    for element in root.iter():
        if _local_name(element.tag) != "Placemark":
            continue
        name = ""
        coordinates: list[float] = []
        for child in element.iter():
            local = _local_name(child.tag)
            if local == "name" and not name and child.text:
                name = child.text.strip()
            elif local == "coordinates" and child.text:
                coordinates = _parse_kml_coordinates(child.text)
        placemarks.append({"name": name, "coordinates": coordinates})
    return placemarks


def _parse_kml_coordinates(text: str) -> list[float]:
    values: list[float] = []
    for token in text.replace("\n", " ").split():
        for piece in token.split(","):
            piece = piece.strip()
            if not piece:
                continue
            try:
                number = float(piece)
            except ValueError:
                continue
            if math.isfinite(number):
                values.append(number)
    return values


def _local_name(tag: object) -> str:
    if not isinstance(tag, str):
        return ""
    return tag.split("}")[-1]


def _present_numeric_keys(point: Mapping[str, object]) -> tuple[str, ...]:
    return tuple(key for key in PHASE_D3_HEATMAP_NUMERIC_KEYS if key in point)


def _as_finite_float(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)) and math.isfinite(float(value)):
        return float(value)
    return None


def _overall_status(results: Iterable[Mapping[str, object]]) -> str:
    statuses = [str(item["status"]) for item in results]
    if not statuses:
        return "incomplete"
    if any(status == "error" for status in statuses):
        return "error"
    if any(status == "failed" for status in statuses):
        return "failed"
    if any(status == "comparison_unavailable" for status in statuses):
        return "comparison_unavailable"
    if any(
        status in {"reference_missing", "app_output_missing", "skipped_by_request"}
        for status in statuses
    ):
        return "incomplete"
    if all(status == "passed" for status in statuses):
        return "passed"
    return "incomplete"


def _counts_by_status(results: Iterable[Mapping[str, object]]) -> dict[str, int]:
    counts = {status: 0 for status in sorted(ALLOWED_PHASE_E4_RESULT_STATUSES)}
    for item in results:
        counts[str(item["status"])] += 1
    return counts
