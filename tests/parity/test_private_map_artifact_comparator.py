from __future__ import annotations

import inspect
import json
from pathlib import Path
import zipfile

from app.pipeline.parity.private_map_artifact_comparator import (
    PHASE_D1_GEOJSON_FAMILY_ID,
    PHASE_D2_KMZ_FAMILY_ID,
    PHASE_D3_HEATMAP_FAMILY_ID,
    PHASE_D_PRIVATE_MAP_ARTIFACT_FAMILIES,
    PHASE_E4_PRIVATE_MAP_ARTIFACT_COMPARATOR_SCHEMA_VERSION,
    compare_phase_d_private_map_artifacts,
)


FORBIDDEN_ARTIFACT_SUFFIXES = {
    ".tif",
    ".tiff",
    ".geojson",
    ".kmz",
    ".kml",
    ".html",
    ".png",
    ".jpg",
    ".jpeg",
    ".csv",
    ".npy",
    ".pt",
    ".pth",
    ".onnx",
    ".h5",
    ".pkl",
    ".joblib",
}

# Distinctive private tokens used to assert redaction of coordinate-bearing data.
_SECRET_LON = 36.142857142857
_SECRET_LAT = 35.271828182845
_SECRET_PLACEMARK_NAME = "Placemark_PRIVATE_TOKEN_ABC"
_SECRET_HEATMAP_NAME = "heatmap_PRIVATE_TOKEN_XYZ"
_SECRET_WEIGHT = 0.7654321


# ---------------------------------------------------------------------------
# Fixture builders (tiny artifacts under pytest tmp dirs only)
# ---------------------------------------------------------------------------
def _geojson_feature(lon: float, lat: float) -> dict[str, object]:
    return {
        "type": "Feature",
        "properties": {"class_label": "Class_1"},
        "geometry": {"type": "Point", "coordinates": [lon, lat]},
    }


def _write_geojson(root: Path, features: list[dict[str, object]]) -> Path:
    path = root / "private_map_artifacts" / "geojson" / "private_features.geojson"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"type": "FeatureCollection", "features": features}
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _build_kml(placemarks: list[tuple[str, float, float]]) -> str:
    blocks = []
    for name, lon, lat in placemarks:
        blocks.append(
            "    <Placemark>\n"
            f"      <name>{name}</name>\n"
            "      <Point>\n"
            f"        <coordinates>{lon:.12g},{lat:.12g},0</coordinates>\n"
            "      </Point>\n"
            "    </Placemark>"
        )
    placemark_xml = "\n".join(blocks)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<kml xmlns="http://www.opengis.net/kml/2.2">\n'
        "  <Document>\n"
        "    <name>Private KMZ point overlay</name>\n"
        f"{placemark_xml}\n"
        "  </Document>\n"
        "</kml>\n"
    )


def _write_kmz(
    root: Path,
    placemarks: list[tuple[str, float, float]],
    *,
    include_doc_kml: bool = True,
    bad_zip: bool = False,
) -> Path:
    path = root / "private_map_artifacts" / "kmz" / "private_points.kmz"
    path.parent.mkdir(parents=True, exist_ok=True)
    if bad_zip:
        path.write_text("this is not a zip archive", encoding="utf-8")
        return path
    kml = _build_kml(placemarks)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("doc.kml" if include_doc_kml else "other.kml", kml)
    return path


def _heatmap_point(name: str, lon: float, lat: float, weight: float) -> dict[str, object]:
    return {"name": name, "latitude": lat, "longitude": lon, "weight": weight}


def _write_heatmap(
    root: Path,
    points: list[dict[str, object]],
    *,
    schema_version: str = "private_heatmap_points_v1",
) -> Path:
    path = root / "private_map_artifacts" / "heatmap" / "private_heatmap.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": schema_version,
        "artifact_type": "Private Heatmap JSON",
        "point_count": len(points),
        "points": points,
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _matching_all_families(tmp_path: Path) -> tuple[Path, Path]:
    app_dir = tmp_path / "app"
    reference_dir = tmp_path / "refs"
    for root in (app_dir, reference_dir):
        _write_geojson(root, [_geojson_feature(36.1, 35.2), _geojson_feature(36.3, 35.4)])
        _write_kmz(root, [("p0", 36.1, 35.2), ("p1", 36.3, 35.4)])
        _write_heatmap(
            root,
            [_heatmap_point("h0", 36.1, 35.2, 0.5), _heatmap_point("h1", 36.3, 35.4, 0.9)],
        )
    return app_dir, reference_dir


# ---------------------------------------------------------------------------
# GeoJSON
# ---------------------------------------------------------------------------
def test_geojson_comparator_passes_for_matching_feature_collections(tmp_path: Path) -> None:
    app_dir = tmp_path / "app"
    reference_dir = tmp_path / "refs"
    features = [_geojson_feature(36.1, 35.2), _geojson_feature(36.3, 35.4)]
    _write_geojson(app_dir, features)
    _write_geojson(reference_dir, features)

    result = compare_phase_d_private_map_artifacts(
        app_output_dir=app_dir,
        reference_bundle_dir=reference_dir,
        run_dir=tmp_path / "run",
        run_id="phase-e4-geojson-pass",
        selected_artifacts=(PHASE_D1_GEOJSON_FAMILY_ID,),
    )

    assert result.overall_status == "passed"
    assert result.results[0]["status"] == "passed"
    assert result.results[0]["structure_match"] is True
    assert result.results[0]["count_match"] is True
    assert result.notebook_value_parity_verified is True


def test_geojson_comparator_fails_for_feature_count_mismatch(tmp_path: Path) -> None:
    app_dir = tmp_path / "app"
    reference_dir = tmp_path / "refs"
    _write_geojson(app_dir, [_geojson_feature(36.1, 35.2)])
    _write_geojson(reference_dir, [_geojson_feature(36.1, 35.2), _geojson_feature(36.3, 35.4)])

    result = compare_phase_d_private_map_artifacts(
        app_output_dir=app_dir,
        reference_bundle_dir=reference_dir,
        run_dir=tmp_path / "run",
        run_id="phase-e4-geojson-count",
        selected_artifacts=(PHASE_D1_GEOJSON_FAMILY_ID,),
    )

    assert result.overall_status == "failed"
    assert result.results[0]["status"] == "failed"
    assert result.results[0]["count_match"] is False


def test_geojson_comparator_returns_reference_missing(tmp_path: Path) -> None:
    app_dir = tmp_path / "app"
    reference_dir = tmp_path / "refs"
    _write_geojson(app_dir, [_geojson_feature(36.1, 35.2)])

    result = compare_phase_d_private_map_artifacts(
        app_output_dir=app_dir,
        reference_bundle_dir=reference_dir,
        run_dir=tmp_path / "run",
        run_id="phase-e4-geojson-ref-missing",
        selected_artifacts=(PHASE_D1_GEOJSON_FAMILY_ID,),
    )

    assert result.overall_status == "incomplete"
    assert result.results[0]["status"] == "reference_missing"
    assert result.notebook_value_parity_verified is False


def test_geojson_comparator_returns_app_output_missing(tmp_path: Path) -> None:
    app_dir = tmp_path / "app"
    reference_dir = tmp_path / "refs"
    _write_geojson(reference_dir, [_geojson_feature(36.1, 35.2)])

    result = compare_phase_d_private_map_artifacts(
        app_output_dir=app_dir,
        reference_bundle_dir=reference_dir,
        run_dir=tmp_path / "run",
        run_id="phase-e4-geojson-app-missing",
        selected_artifacts=(PHASE_D1_GEOJSON_FAMILY_ID,),
    )

    assert result.overall_status == "incomplete"
    assert result.results[0]["status"] == "app_output_missing"
    assert result.runtime_output_verified is False


def test_geojson_comparator_returns_error_for_malformed_json(tmp_path: Path) -> None:
    app_dir = tmp_path / "app"
    reference_dir = tmp_path / "refs"
    app_path = app_dir / "private_map_artifacts" / "geojson" / "private_features.geojson"
    app_path.parent.mkdir(parents=True, exist_ok=True)
    app_path.write_text("{ not valid json", encoding="utf-8")
    _write_geojson(reference_dir, [_geojson_feature(36.1, 35.2)])

    result = compare_phase_d_private_map_artifacts(
        app_output_dir=app_dir,
        reference_bundle_dir=reference_dir,
        run_dir=tmp_path / "run",
        run_id="phase-e4-geojson-malformed",
        selected_artifacts=(PHASE_D1_GEOJSON_FAMILY_ID,),
    )

    assert result.results[0]["status"] == "error"
    assert result.overall_status == "error"


# ---------------------------------------------------------------------------
# KMZ
# ---------------------------------------------------------------------------
def test_kmz_comparator_passes_for_matching_kmz_with_doc_kml(tmp_path: Path) -> None:
    app_dir = tmp_path / "app"
    reference_dir = tmp_path / "refs"
    placemarks = [("p0", 36.1, 35.2), ("p1", 36.3, 35.4)]
    _write_kmz(app_dir, placemarks)
    _write_kmz(reference_dir, placemarks)

    result = compare_phase_d_private_map_artifacts(
        app_output_dir=app_dir,
        reference_bundle_dir=reference_dir,
        run_dir=tmp_path / "run",
        run_id="phase-e4-kmz-pass",
        selected_artifacts=(PHASE_D2_KMZ_FAMILY_ID,),
    )

    assert result.overall_status == "passed"
    assert result.results[0]["status"] == "passed"
    assert result.results[0]["structure_match"] is True
    assert result.results[0]["count_match"] is True


def test_kmz_comparator_fails_when_doc_kml_is_missing(tmp_path: Path) -> None:
    app_dir = tmp_path / "app"
    reference_dir = tmp_path / "refs"
    placemarks = [("p0", 36.1, 35.2)]
    _write_kmz(app_dir, placemarks, include_doc_kml=False)
    _write_kmz(reference_dir, placemarks)

    result = compare_phase_d_private_map_artifacts(
        app_output_dir=app_dir,
        reference_bundle_dir=reference_dir,
        run_dir=tmp_path / "run",
        run_id="phase-e4-kmz-no-doc",
        selected_artifacts=(PHASE_D2_KMZ_FAMILY_ID,),
    )

    assert result.overall_status == "failed"
    assert result.results[0]["status"] == "failed"
    assert result.results[0]["structure_match"] is False


def test_kmz_comparator_fails_for_placemark_count_mismatch(tmp_path: Path) -> None:
    app_dir = tmp_path / "app"
    reference_dir = tmp_path / "refs"
    _write_kmz(app_dir, [("p0", 36.1, 35.2)])
    _write_kmz(reference_dir, [("p0", 36.1, 35.2), ("p1", 36.3, 35.4)])

    result = compare_phase_d_private_map_artifacts(
        app_output_dir=app_dir,
        reference_bundle_dir=reference_dir,
        run_dir=tmp_path / "run",
        run_id="phase-e4-kmz-count",
        selected_artifacts=(PHASE_D2_KMZ_FAMILY_ID,),
    )

    assert result.overall_status == "failed"
    assert result.results[0]["status"] == "failed"
    assert result.results[0]["count_match"] is False


def test_kmz_comparator_returns_error_for_non_zip(tmp_path: Path) -> None:
    app_dir = tmp_path / "app"
    reference_dir = tmp_path / "refs"
    _write_kmz(app_dir, [("p0", 36.1, 35.2)], bad_zip=True)
    _write_kmz(reference_dir, [("p0", 36.1, 35.2)])

    result = compare_phase_d_private_map_artifacts(
        app_output_dir=app_dir,
        reference_bundle_dir=reference_dir,
        run_dir=tmp_path / "run",
        run_id="phase-e4-kmz-bad-zip",
        selected_artifacts=(PHASE_D2_KMZ_FAMILY_ID,),
    )

    assert result.results[0]["status"] == "error"
    assert result.overall_status == "error"


# ---------------------------------------------------------------------------
# Heatmap JSON
# ---------------------------------------------------------------------------
def test_heatmap_comparator_passes_for_matching_heatmaps(tmp_path: Path) -> None:
    app_dir = tmp_path / "app"
    reference_dir = tmp_path / "refs"
    points = [_heatmap_point("h0", 36.1, 35.2, 0.5), _heatmap_point("h1", 36.3, 35.4, 0.9)]
    _write_heatmap(app_dir, points)
    _write_heatmap(reference_dir, points)

    result = compare_phase_d_private_map_artifacts(
        app_output_dir=app_dir,
        reference_bundle_dir=reference_dir,
        run_dir=tmp_path / "run",
        run_id="phase-e4-heatmap-pass",
        selected_artifacts=(PHASE_D3_HEATMAP_FAMILY_ID,),
    )

    assert result.overall_status == "passed"
    assert result.results[0]["status"] == "passed"
    assert result.results[0]["count_match"] is True


def test_heatmap_comparator_fails_for_point_count_mismatch(tmp_path: Path) -> None:
    app_dir = tmp_path / "app"
    reference_dir = tmp_path / "refs"
    _write_heatmap(app_dir, [_heatmap_point("h0", 36.1, 35.2, 0.5)])
    _write_heatmap(
        reference_dir,
        [_heatmap_point("h0", 36.1, 35.2, 0.5), _heatmap_point("h1", 36.3, 35.4, 0.9)],
    )

    result = compare_phase_d_private_map_artifacts(
        app_output_dir=app_dir,
        reference_bundle_dir=reference_dir,
        run_dir=tmp_path / "run",
        run_id="phase-e4-heatmap-count",
        selected_artifacts=(PHASE_D3_HEATMAP_FAMILY_ID,),
    )

    assert result.overall_status == "failed"
    assert result.results[0]["status"] == "failed"
    assert result.results[0]["count_match"] is False


def test_heatmap_comparator_fails_for_weight_mismatch_above_tolerance(tmp_path: Path) -> None:
    app_dir = tmp_path / "app"
    reference_dir = tmp_path / "refs"
    _write_heatmap(app_dir, [_heatmap_point("h0", 36.1, 35.2, 0.5)])
    _write_heatmap(reference_dir, [_heatmap_point("h0", 36.1, 35.2, 0.9)])

    result = compare_phase_d_private_map_artifacts(
        app_output_dir=app_dir,
        reference_bundle_dir=reference_dir,
        run_dir=tmp_path / "run",
        run_id="phase-e4-heatmap-weight",
        selected_artifacts=(PHASE_D3_HEATMAP_FAMILY_ID,),
        weight_atol=1e-6,
    )

    assert result.overall_status == "failed"
    assert result.results[0]["status"] == "failed"
    assert result.results[0]["max_abs_error"] > 1e-6


def test_heatmap_comparator_passes_within_weight_tolerance(tmp_path: Path) -> None:
    app_dir = tmp_path / "app"
    reference_dir = tmp_path / "refs"
    _write_heatmap(app_dir, [_heatmap_point("h0", 36.1, 35.2, 0.5000001)])
    _write_heatmap(reference_dir, [_heatmap_point("h0", 36.1, 35.2, 0.5)])

    result = compare_phase_d_private_map_artifacts(
        app_output_dir=app_dir,
        reference_bundle_dir=reference_dir,
        run_dir=tmp_path / "run",
        run_id="phase-e4-heatmap-tolerance",
        selected_artifacts=(PHASE_D3_HEATMAP_FAMILY_ID,),
        weight_atol=1e-5,
    )

    assert result.overall_status == "passed"
    assert result.results[0]["status"] == "passed"


# ---------------------------------------------------------------------------
# Selection, families, overall rules
# ---------------------------------------------------------------------------
def test_selected_artifact_filtering_works(tmp_path: Path) -> None:
    app_dir, reference_dir = _matching_all_families(tmp_path)
    selected = (PHASE_D2_KMZ_FAMILY_ID,)

    result = compare_phase_d_private_map_artifacts(
        app_output_dir=app_dir,
        reference_bundle_dir=reference_dir,
        run_dir=tmp_path / "run",
        run_id="phase-e4-filter",
        selected_artifacts=selected,
    )

    assert result.selected_artifacts == selected
    assert [item["family_id"] for item in result.results] == [PHASE_D2_KMZ_FAMILY_ID]


def test_all_three_phase_d_families_are_supported(tmp_path: Path) -> None:
    app_dir, reference_dir = _matching_all_families(tmp_path)

    result = compare_phase_d_private_map_artifacts(
        app_output_dir=app_dir,
        reference_bundle_dir=reference_dir,
        run_dir=tmp_path / "run",
        run_id="phase-e4-all-families",
    )

    assert PHASE_D_PRIVATE_MAP_ARTIFACT_FAMILIES == (
        PHASE_D1_GEOJSON_FAMILY_ID,
        PHASE_D2_KMZ_FAMILY_ID,
        PHASE_D3_HEATMAP_FAMILY_ID,
    )
    assert {item["family_id"] for item in result.results} == set(
        PHASE_D_PRIVATE_MAP_ARTIFACT_FAMILIES
    )
    assert result.overall_status == "passed"


def test_overall_status_fails_when_any_selected_artifact_fails(tmp_path: Path) -> None:
    app_dir, reference_dir = _matching_all_families(tmp_path)
    # Break heatmap parity only.
    _write_heatmap(app_dir, [_heatmap_point("h0", 36.1, 35.2, 0.1)])
    _write_heatmap(reference_dir, [_heatmap_point("h0", 36.1, 35.2, 0.9)])

    result = compare_phase_d_private_map_artifacts(
        app_output_dir=app_dir,
        reference_bundle_dir=reference_dir,
        run_dir=tmp_path / "run",
        run_id="phase-e4-overall-fail",
    )

    assert result.overall_status == "failed"
    assert result.notebook_value_parity_verified is False


def test_notebook_value_parity_true_only_when_all_selected_pass(tmp_path: Path) -> None:
    app_dir, reference_dir = _matching_all_families(tmp_path)

    passing = compare_phase_d_private_map_artifacts(
        app_output_dir=app_dir,
        reference_bundle_dir=reference_dir,
        run_dir=tmp_path / "run-pass",
        run_id="phase-e4-parity-pass",
    )
    assert passing.notebook_value_parity_verified is True

    _write_geojson(app_dir, [_geojson_feature(36.1, 35.2)])  # count now differs from reference
    failing = compare_phase_d_private_map_artifacts(
        app_output_dir=app_dir,
        reference_bundle_dir=reference_dir,
        run_dir=tmp_path / "run-fail",
        run_id="phase-e4-parity-fail",
    )
    assert failing.notebook_value_parity_verified is False


def test_runtime_output_verified_false_if_any_selected_app_output_missing(tmp_path: Path) -> None:
    app_dir, reference_dir = _matching_all_families(tmp_path)
    # Remove one selected app output.
    (app_dir / "private_map_artifacts" / "kmz" / "private_points.kmz").unlink()

    result = compare_phase_d_private_map_artifacts(
        app_output_dir=app_dir,
        reference_bundle_dir=reference_dir,
        run_dir=tmp_path / "run",
        run_id="phase-e4-runtime-missing",
    )

    assert result.runtime_output_verified is False
    statuses = {item["family_id"]: item["status"] for item in result.results}
    assert statuses[PHASE_D2_KMZ_FAMILY_ID] == "app_output_missing"


def test_skipped_by_request_is_not_success(tmp_path: Path) -> None:
    app_dir, reference_dir = _matching_all_families(tmp_path)

    result = compare_phase_d_private_map_artifacts(
        app_output_dir=app_dir,
        reference_bundle_dir=reference_dir,
        run_dir=tmp_path / "run",
        run_id="phase-e4-skip",
        skipped_artifacts=(PHASE_D3_HEATMAP_FAMILY_ID,),
    )

    statuses = {item["family_id"]: item["status"] for item in result.results}
    assert statuses[PHASE_D3_HEATMAP_FAMILY_ID] == "skipped_by_request"
    assert result.overall_status == "incomplete"
    assert result.notebook_value_parity_verified is False


# ---------------------------------------------------------------------------
# Redaction
# ---------------------------------------------------------------------------
def _redacted_text_for_all_families(tmp_path: Path) -> str:
    app_dir = tmp_path / "app"
    reference_dir = tmp_path / "refs"
    for root in (app_dir, reference_dir):
        _write_geojson(root, [_geojson_feature(_SECRET_LON, _SECRET_LAT)])
        _write_kmz(root, [(_SECRET_PLACEMARK_NAME, _SECRET_LON, _SECRET_LAT)])
        _write_heatmap(
            root, [_heatmap_point(_SECRET_HEATMAP_NAME, _SECRET_LON, _SECRET_LAT, _SECRET_WEIGHT)]
        )

    result = compare_phase_d_private_map_artifacts(
        app_output_dir=app_dir,
        reference_bundle_dir=reference_dir,
        run_dir=tmp_path / "run",
        run_id="phase-e4-redaction",
    )
    summaries = [item["redacted_summary"] for item in result.results]
    return json.dumps(summaries, sort_keys=True)


def test_redacted_summary_contains_no_exact_coordinates(tmp_path: Path) -> None:
    text = _redacted_text_for_all_families(tmp_path)
    assert "36.142857142857" not in text
    assert "35.271828182845" not in text
    assert "36.142857" not in text
    assert "35.271828" not in text


def test_redacted_summary_contains_no_raw_geometry(tmp_path: Path) -> None:
    text = _redacted_text_for_all_families(tmp_path)
    assert "coordinates" not in text
    assert "geometry" not in text
    assert "FeatureCollection" not in text


def test_redacted_summary_contains_no_kml_content(tmp_path: Path) -> None:
    text = _redacted_text_for_all_families(tmp_path)
    assert "Placemark" not in text
    assert _SECRET_PLACEMARK_NAME not in text
    assert "<kml" not in text
    assert "doc.kml" not in text


def test_redacted_summary_contains_no_heatmap_point_payloads(tmp_path: Path) -> None:
    text = _redacted_text_for_all_families(tmp_path)
    assert _SECRET_HEATMAP_NAME not in text
    assert "0.7654321" not in text
    assert "weight" not in text
    assert "points" not in text


def test_redacted_summary_contains_no_local_filesystem_path(tmp_path: Path) -> None:
    app_dir = tmp_path / "app"
    reference_dir = tmp_path / "refs"
    for root in (app_dir, reference_dir):
        _write_geojson(root, [_geojson_feature(_SECRET_LON, _SECRET_LAT)])

    result = compare_phase_d_private_map_artifacts(
        app_output_dir=app_dir,
        reference_bundle_dir=reference_dir,
        run_dir=tmp_path / "run",
        run_id="phase-e4-redaction-path",
        selected_artifacts=(PHASE_D1_GEOJSON_FAMILY_ID,),
    )
    text = json.dumps(result.results[0]["redacted_summary"], sort_keys=True)
    assert str(tmp_path) not in text
    assert str(app_dir) not in text
    assert str(reference_dir) not in text
    assert ".geojson" not in text


def test_redacted_summary_contains_no_private_hashes(tmp_path: Path) -> None:
    text = _redacted_text_for_all_families(tmp_path).lower()
    assert "sha256" not in text
    assert "sha1" not in text
    assert "md5" not in text
    assert "hash" not in text


# ---------------------------------------------------------------------------
# Report shape and safety
# ---------------------------------------------------------------------------
def test_report_writes_and_parses_under_run_dir(tmp_path: Path) -> None:
    app_dir, reference_dir = _matching_all_families(tmp_path)
    run_dir = tmp_path / "run"

    result = compare_phase_d_private_map_artifacts(
        app_output_dir=app_dir,
        reference_bundle_dir=reference_dir,
        run_dir=run_dir,
        run_id="phase-e4-report",
    )
    payload = json.loads(result.report_path.read_text(encoding="utf-8"))

    assert result.report_path == run_dir / "manifests" / "phase_e4_private_map_artifact_comparator.json"
    assert result.report_path.resolve().relative_to(run_dir.resolve())
    assert payload["schema_version"] == PHASE_E4_PRIVATE_MAP_ARTIFACT_COMPARATOR_SCHEMA_VERSION
    assert payload["comparator_id"] == "phase_e4_private_map_artifact_comparator"
    assert payload["phase_e4_comparator_only"] is True
    assert payload["runtime_added"] is False
    assert payload["writer_added"] is False
    assert payload["earth_engine_calls_added"] is False
    assert payload["public_exposure_changes"] is False
    assert payload["artifact_generation"] is False
    assert set(payload["counts_by_status"]) >= {
        "passed",
        "failed",
        "reference_missing",
        "app_output_missing",
        "comparison_unavailable",
        "skipped_by_request",
        "error",
    }


def test_report_result_fields_are_complete(tmp_path: Path) -> None:
    app_dir, reference_dir = _matching_all_families(tmp_path)

    result = compare_phase_d_private_map_artifacts(
        app_output_dir=app_dir,
        reference_bundle_dir=reference_dir,
        run_dir=tmp_path / "run",
        run_id="phase-e4-fields",
        selected_artifacts=(PHASE_D1_GEOJSON_FAMILY_ID,),
    )
    item = result.results[0]
    assert set(item) >= {
        "artifact_name",
        "family_id",
        "artifact_type",
        "status",
        "app_output_present",
        "reference_present",
        "structure_match",
        "count_match",
        "tolerance",
        "max_abs_error",
        "mean_abs_error",
        "private_content_compared",
        "runtime_output_verified",
        "notebook_value_parity_verified",
        "redacted_summary",
        "notes",
    }


def test_report_creates_no_disallowed_artifacts_under_run_dir(tmp_path: Path) -> None:
    app_dir, reference_dir = _matching_all_families(tmp_path)
    run_dir = tmp_path / "run"

    compare_phase_d_private_map_artifacts(
        app_output_dir=app_dir,
        reference_bundle_dir=reference_dir,
        run_dir=run_dir,
        run_id="phase-e4-no-artifacts",
    )

    created = [
        path
        for path in run_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in FORBIDDEN_ARTIFACT_SUFFIXES
    ]
    assert created == []


def test_comparator_adds_no_earth_engine_runtime_or_public_serving_calls() -> None:
    import app.pipeline.parity.private_map_artifact_comparator as module

    source = inspect.getsource(module)

    assert "ee.Authenticate" not in source
    assert "import ee" not in source
    assert "earthengine" not in source.lower()
    assert "google.colab" not in source
    assert "drive.mount" not in source
    assert "/content/drive" not in source
    assert "enqueue_core_pipeline_run" not in source
    assert "run_core_pipeline" not in source
    assert "serve_artifact_response" not in source
    assert "can_serve_artifact" not in source
    assert "FileResponse" not in source
    assert "StreamingResponse" not in source
