from __future__ import annotations

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
                    "feature_id": "candidate_middle",
                    "role": "candidate",
                },
                "geometry": _polygon(140, 260),
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
        "calibration_dataset_version": "test-v1",
        "method_version": "operator-local-depth-test-v1",
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


def test_service_returns_local_range_without_geometry_or_paths(tmp_path: Path) -> None:
    settings = _settings(tmp_path, enabled=True)
    run_id = "run-1"
    run_dir = _completed_run(settings, run_id)

    result = run_operator_local_depth_app(
        settings=settings,
        run_id=run_id,
        geojson=_geojson(),
        site_id="test-site",
        calibration_dataset_version="test-v1",
        method_version="operator-local-depth-test-v1",
        input_crs="EPSG:32613",
        operator_confirmed_review=True,
    )

    assert result["outcome"] == "completed"
    assert result["anchor_count"] == 2
    assert result["candidate_count"] == 1
    assert result["estimated_count"] == 1
    assert result["estimates"][0]["candidate_id"] == "candidate_middle"
    assert result["estimates"][0]["depth_status"] == "calibrated_range"
    assert result["estimates"][0]["estimated_depth_best_m"] is not None
    assert result["geometry_returned"] is False
    assert result["filesystem_only"] is True
    assert "geojson" not in json.dumps(result).lower()
    assert str(tmp_path) not in json.dumps(result)
    assert (run_dir / "operator" / "local_depth_app" / "reviewed_zones.geojson").is_file()
    assert (run_dir / "depth" / "depth_estimates.csv").is_file()


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


def test_api_runs_private_local_depth_and_passes_redaction_middleware(tmp_path: Path) -> None:
    settings = _settings(tmp_path, enabled=True)
    run_id = "run-api"
    _completed_run(settings, run_id)

    with TestClient(create_app(settings)) as client:
        response = client.post(
            f"/runs/{run_id}/operator/local-depth",
            json=_request_payload(),
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["outcome"] == "completed"
    assert payload["estimated_count"] == 1
    assert payload["estimates"][0]["depth_status"] == "calibrated_range"
    assert payload["geometry_returned"] is False
    serialized = json.dumps(payload).lower()
    assert "coordinates" not in serialized
    assert "reviewed_zones" not in serialized
    assert str(tmp_path).lower() not in serialized


def test_second_request_requires_explicit_replacement(tmp_path: Path) -> None:
    settings = _settings(tmp_path, enabled=True)
    run_id = "run-repeat"
    _completed_run(settings, run_id)
    kwargs = {
        "settings": settings,
        "run_id": run_id,
        "geojson": _geojson(),
        "site_id": "test-site",
        "calibration_dataset_version": "test-v1",
        "method_version": "operator-local-depth-test-v1",
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
    assert replaced["estimated_count"] == 1
