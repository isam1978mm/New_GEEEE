from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
import rasterio
from fastapi.testclient import TestClient
from rasterio.transform import from_origin

from app.config import Settings
from app.main import create_app
from app.services.operator_local_depth_app import (
    evaluate_operator_local_depth_access,
    get_operator_local_depth_result,
    run_operator_local_depth_app,
)


def _settings(tmp_path: Path, *, enabled: bool) -> Settings:
    return Settings(
        data_dir=tmp_path / "data",
        database_path=tmp_path / "data" / "test.db",
        operator_local_depth_app_enabled=enabled,
        allow_network_bind=False,
    )


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _write_classifier_findings(run_dir: Path) -> None:
    path = run_dir / "classifier" / "classifications.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        {
            "object_id": "1",
            "cluster_id": "10",
            "row_min": "5",
            "row_max": "15",
            "col_min": "14",
            "col_max": "25",
        },
        {
            "object_id": "2",
            "cluster_id": "20",
            "row_min": "4",
            "row_max": "12",
            "col_min": "0",
            "col_max": "3",
        },
        {
            "object_id": "3",
            "cluster_id": "30",
            "row_min": "8",
            "row_max": "18",
            "col_min": "36",
            "col_max": "39",
        },
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _completed_run(settings: Settings, run_id: str) -> Path:
    run_dir = settings.data_dir / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    _write_json(
        run_dir / "QA" / "run_quality" / "run_quality_summary.json",
        {
            "schema": "run_quality_summary_v1",
            "stage": "run_quality",
            "status": "PASS",
            "is_usable": True,
        },
    )
    columns = np.arange(40, dtype=np.float32) * np.float32(0.1)
    raster = np.repeat(columns[np.newaxis, :], 40, axis=0)
    with rasterio.open(
        run_dir / "logRatio_dB.tif",
        "w",
        driver="GTiff",
        width=40,
        height=40,
        count=1,
        dtype="float32",
        crs="EPSG:32613",
        transform=from_origin(0, 400, 10, 10),
        nodata=-9999.0,
    ) as dataset:
        dataset.write(raster, 1)
    _write_classifier_findings(run_dir)
    return run_dir


def _polygon(xmin: float, xmax: float) -> dict:
    return {
        "type": "Polygon",
        "coordinates": [
            [
                [xmin, 0],
                [xmax, 0],
                [xmax, 400],
                [xmin, 400],
                [xmin, 0],
            ]
        ],
    }


def _geojson() -> dict:
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "feature_id": "anchor_shallow",
                    "role": "anchor",
                    "depth_min_m": 0.9,
                    "depth_best_m": 1.0,
                    "depth_max_m": 1.1,
                },
                "geometry": _polygon(0, 120),
            },
            {
                "type": "Feature",
                "properties": {
                    "feature_id": "anchor_deep",
                    "role": "anchor",
                    "depth_min_m": 2.9,
                    "depth_best_m": 3.0,
                    "depth_max_m": 3.1,
                },
                "geometry": _polygon(280, 400),
            },
        ],
    }


def _request_payload() -> dict:
    return {
        "geojson": _geojson(),
        "site_id": "test-site",
        "calibration_dataset_version": "test-v2",
        "method_version": "operator-local-depth-test-v2",
        "input_crs": "EPSG:32613",
        "erosion_pixels": 2,
        "minimum_valid_pixels": 20,
        "operator_confirmed_review": True,
    }


def test_access_is_default_off_without_reading_run(tmp_path: Path) -> None:
    settings = _settings(tmp_path, enabled=False)
    decision = evaluate_operator_local_depth_access(
        settings=settings,
        run_id="missing-run",
        actor_id="local-operator",
        is_authenticated=True,
        roles=("operator",),
    )
    assert decision.allowed is False
    assert decision.reason == "local_depth_app_disabled"
    assert not (settings.data_dir / "runs").exists()


def test_local_development_operator_is_authorized_when_enabled(tmp_path: Path) -> None:
    settings = _settings(tmp_path, enabled=True)
    decision = evaluate_operator_local_depth_access(
        settings=settings,
        run_id="run-1",
        actor_id="local-operator",
        is_authenticated=True,
        roles=("operator",),
    )
    assert decision.allowed is True


def test_service_estimates_every_classifier_finding_without_manual_candidates(
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path, enabled=True)
    run_id = "run-1"
    run_dir = _completed_run(settings, run_id)

    result = run_operator_local_depth_app(
        settings=settings,
        run_id=run_id,
        geojson=_geojson(),
        site_id="test-site",
        calibration_dataset_version="test-v2",
        method_version="operator-local-depth-test-v2",
        input_crs="EPSG:32613",
        operator_confirmed_review=True,
    )

    assert result["outcome"] == "completed"
    assert result["anchor_count"] == 2
    assert result["candidate_count"] == 3
    assert result["estimated_count"] == 1
    assert [row["candidate_id"] for row in result["estimates"]] == [
        "finding-object-1",
        "finding-object-2",
        "finding-object-3",
    ]
    assert result["estimates"][0]["depth_status"] == "calibrated_range"
    assert result["estimates"][0]["estimated_depth_best_m"] is not None
    assert result["estimates"][1]["depth_status"] == "insufficient_data"
    assert result["estimates"][2]["depth_status"] == "insufficient_data"
    assert result["automatic_finding_candidates"] is True
    assert result["results_attached_to_findings"] is True
    assert result["geometry_returned"] is False
    assert result["filesystem_only"] is True
    assert "geojson" not in json.dumps(result).lower()
    assert str(tmp_path) not in json.dumps(result)
    assert (
        run_dir
        / "operator"
        / "local_depth_app"
        / "reviewed_anchors.geojson"
    ).is_file()
    assert (
        run_dir
        / "operator"
        / "local_depth_app"
        / "finding_depth_results.json"
    ).is_file()
    assert (run_dir / "depth" / "depth_estimates.csv").is_file()

    saved = get_operator_local_depth_result(settings=settings, run_id=run_id)
    assert saved["candidate_count"] == 3
    assert saved["estimates"] == result["estimates"]


def test_manual_candidate_polygon_is_rejected(tmp_path: Path) -> None:
    settings = _settings(tmp_path, enabled=True)
    run_id = "run-candidate-rejected"
    _completed_run(settings, run_id)
    payload = _geojson()
    payload["features"].append(
        {
            "type": "Feature",
            "properties": {
                "feature_id": "manual-candidate",
                "role": "candidate",
            },
            "geometry": _polygon(140, 260),
        }
    )

    try:
        run_operator_local_depth_app(
            settings=settings,
            run_id=run_id,
            geojson=payload,
            site_id="test-site",
            calibration_dataset_version="test-v2",
            input_crs="EPSG:32613",
            operator_confirmed_review=True,
        )
    except ValueError as exc:
        assert "Finding candidates are generated automatically" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("manual candidate polygons must be rejected")


def test_api_denies_when_default_off_before_run_files_exist(tmp_path: Path) -> None:
    settings = _settings(tmp_path, enabled=False)
    with TestClient(create_app(settings)) as client:
        response = client.post(
            "/runs/missing-run/operator/local-depth",
            json=_request_payload(),
        )
    assert response.status_code == 403
    assert response.json()["outcome"] == "denied"
    assert not (settings.data_dir / "runs" / "missing-run").exists()


def test_api_get_reports_not_available_before_calibration(tmp_path: Path) -> None:
    settings = _settings(tmp_path, enabled=True)
    run_id = "run-before-calibration"
    _completed_run(settings, run_id)

    with TestClient(create_app(settings)) as client:
        response = client.get(f"/runs/{run_id}/operator/local-depth")

    assert response.status_code == 200
    assert response.json()["outcome"] == "not_available"
    assert response.json()["candidate_count"] == 0


def test_api_runs_and_reads_per_finding_depth_results(tmp_path: Path) -> None:
    settings = _settings(tmp_path, enabled=True)
    run_id = "run-api"
    _completed_run(settings, run_id)

    with TestClient(create_app(settings)) as client:
        response = client.post(
            f"/runs/{run_id}/operator/local-depth",
            json=_request_payload(),
        )
        saved_response = client.get(
            f"/runs/{run_id}/operator/local-depth"
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["outcome"] == "completed"
    assert payload["candidate_count"] == 3
    assert payload["estimated_count"] == 1
    assert payload["estimates"][0]["depth_status"] == "calibrated_range"
    assert payload["geometry_returned"] is False
    serialized = json.dumps(payload).lower()
    assert "coordinates" not in serialized
    assert "reviewed_anchors" not in serialized
    assert str(tmp_path).lower() not in serialized

    assert saved_response.status_code == 200
    assert saved_response.json()["estimates"] == payload["estimates"]


def test_second_request_requires_explicit_replacement(tmp_path: Path) -> None:
    settings = _settings(tmp_path, enabled=True)
    run_id = "run-repeat"
    _completed_run(settings, run_id)
    kwargs = {
        "settings": settings,
        "run_id": run_id,
        "geojson": _geojson(),
        "site_id": "test-site",
        "calibration_dataset_version": "test-v2",
        "method_version": "operator-local-depth-test-v2",
        "input_crs": "EPSG:32613",
        "operator_confirmed_review": True,
    }
    run_operator_local_depth_app(**kwargs)

    try:
        run_operator_local_depth_app(**kwargs)
    except ValueError as exc:
        assert "already has operator local-depth inputs" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("second request should require replacement")

    replaced = run_operator_local_depth_app(**kwargs, force=True)
    assert replaced["candidate_count"] == 3
