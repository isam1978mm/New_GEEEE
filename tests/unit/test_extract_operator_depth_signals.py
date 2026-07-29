from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from scripts.build_operator_local_depth_package import build_operator_local_depth_package
from scripts.extract_operator_depth_signals import (
    OperatorSignalExtractionError,
    extract_operator_depth_signals,
)
from scripts.run_operator_local_depth_for_existing_run import (
    run_operator_depth_for_existing_run,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _write_run_quality(run_dir: Path, *, status: str = "PASS", is_usable: bool = True) -> None:
    _write_json(
        run_dir / "QA" / "run_quality" / "run_quality_summary.json",
        {
            "schema": "run_quality_summary_v1",
            "stage": "run_quality",
            "status": status,
            "is_usable": is_usable,
        },
    )


def _write_signal_raster(run_dir: Path) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    columns = np.arange(40, dtype=np.float32) * np.float32(0.1)
    array = np.repeat(columns[np.newaxis, :], 40, axis=0)
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
        dataset.write(array, 1)


def _polygon(xmin: float, ymin: float, xmax: float, ymax: float) -> dict:
    return {
        "type": "Polygon",
        "coordinates": [
            [
                [xmin, ymin],
                [xmax, ymin],
                [xmax, ymax],
                [xmin, ymax],
                [xmin, ymin],
            ]
        ],
    }


def _feature(
    feature_id: str,
    role: str,
    geometry: dict,
    *,
    depth: tuple[float, float, float] | None = None,
) -> dict:
    properties: dict = {"feature_id": feature_id, "role": role}
    if depth is not None:
        properties.update(
            {
                "depth_min_m": depth[0],
                "depth_best_m": depth[1],
                "depth_max_m": depth[2],
            }
        )
    return {
        "type": "Feature",
        "properties": properties,
        "geometry": geometry,
    }


def _write_reviewed_polygons(path: Path) -> None:
    _write_json(
        path,
        {
            "type": "FeatureCollection",
            "features": [
                _feature(
                    "anchor-shallow",
                    "anchor",
                    _polygon(20, 280, 120, 380),
                    depth=(0.4, 0.5, 0.6),
                ),
                _feature(
                    "anchor-deep",
                    "anchor",
                    _polygon(250, 280, 350, 380),
                    depth=(1.4, 1.5, 1.6),
                ),
                _feature(
                    "candidate-mid",
                    "candidate",
                    _polygon(140, 120, 240, 220),
                ),
            ],
        },
    )


def _setup(tmp_path: Path) -> tuple[Path, Path]:
    run_dir = tmp_path / "run"
    polygon_path = tmp_path / "reviewed.geojson"
    _write_signal_raster(run_dir)
    _write_run_quality(run_dir)
    _write_reviewed_polygons(polygon_path)
    return run_dir, polygon_path


def test_extracts_anchor_and_candidate_signals_without_copying_geometry(tmp_path: Path) -> None:
    run_dir, polygon_path = _setup(tmp_path)
    output_dir = tmp_path / "extracted"

    result = extract_operator_depth_signals(
        run_dir=run_dir,
        polygons_path=polygon_path,
        output_dir=output_dir,
        site_id="local-site",
        method_version="local-method-v1",
        calibration_dataset_version="local-data-v1",
        input_crs="EPSG:32613",
        erosion_pixels=1,
        minimum_valid_pixels=20,
    )

    assert result["status"] == "signals_extracted_review_required"
    assert result["anchor_count"] == 2
    assert result["candidate_count"] == 1
    assert result["geometry_copied_to_outputs"] is False
    assert result["depth_estimation_executed"] is False

    config = json.loads((output_dir / "operator_depth_config.json").read_text(encoding="utf-8"))
    candidates = json.loads(
        (output_dir / "operator_depth_candidates.json").read_text(encoding="utf-8")
    )
    assert config["signal_name"] == "run_logRatio_dB_mean"
    assert len(config["anchors"]) == 2
    assert config["anchors"][0]["signal_value"] < config["anchors"][1]["signal_value"]
    assert candidates["candidates"][0]["signal_uncertainty"] > 0
    assert "geometry" not in json.dumps(config).lower()
    assert "coordinates" not in json.dumps(candidates).lower()

    with (output_dir / "extracted_signals.csv").open(
        "r", encoding="utf-8", newline=""
    ) as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 3
    assert all(int(row["valid_pixel_count"]) >= 20 for row in rows)
    assert all(int(row["mask_pixel_count"]) < int(row["raw_mask_pixel_count"]) for row in rows)


def test_extracted_files_build_package_and_produce_local_range(tmp_path: Path) -> None:
    run_dir, polygon_path = _setup(tmp_path)
    output_dir = tmp_path / "extracted"
    extract_operator_depth_signals(
        run_dir=run_dir,
        polygons_path=polygon_path,
        output_dir=output_dir,
        site_id="local-site",
        method_version="local-method-v1",
        calibration_dataset_version="local-data-v1",
        input_crs="EPSG:32613",
        erosion_pixels=1,
        minimum_valid_pixels=20,
    )

    package_dir = tmp_path / "package"
    build_operator_local_depth_package(
        config_path=output_dir / "operator_depth_config.json",
        output_dir=package_dir,
    )
    result = run_operator_depth_for_existing_run(
        run_dir=run_dir,
        package_dir=package_dir,
        candidate_input=output_dir / "operator_depth_candidates.json",
    )

    assert result["status"] == "calibrated_range"
    assert result["estimated_count"] == 1
    with (run_dir / "depth" / "depth_estimates.csv").open(
        "r", encoding="utf-8", newline=""
    ) as handle:
        row = next(csv.DictReader(handle))
    assert row["candidate_id"] == "candidate-mid"
    assert row["estimated_depth_best_m"] != ""
    assert "signal_uncertainty_applied" in row["warnings"]
    assert "no_extrapolation" in row["warnings"]


def test_rejects_overlapping_eroded_feature_interiors(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    _write_signal_raster(run_dir)
    _write_run_quality(run_dir)
    polygon_path = tmp_path / "overlap.geojson"
    _write_json(
        polygon_path,
        {
            "type": "FeatureCollection",
            "features": [
                _feature("a1", "anchor", _polygon(20, 200, 180, 360), depth=(0.4, 0.5, 0.6)),
                _feature("a2", "anchor", _polygon(120, 200, 280, 360), depth=(1.4, 1.5, 1.6)),
            ],
        },
    )

    with pytest.raises(OperatorSignalExtractionError, match="interiors overlap"):
        extract_operator_depth_signals(
            run_dir=run_dir,
            polygons_path=polygon_path,
            output_dir=tmp_path / "output",
            site_id="site",
            method_version="method",
            calibration_dataset_version="data",
            input_crs="EPSG:32613",
            erosion_pixels=1,
            minimum_valid_pixels=20,
        )


def test_rejects_blocked_run_quality(tmp_path: Path) -> None:
    run_dir, polygon_path = _setup(tmp_path)
    _write_run_quality(run_dir, status="BLOCKED", is_usable=False)

    with pytest.raises(OperatorSignalExtractionError, match="run quality"):
        extract_operator_depth_signals(
            run_dir=run_dir,
            polygons_path=polygon_path,
            output_dir=tmp_path / "output",
            site_id="site",
            method_version="method",
            calibration_dataset_version="data",
            input_crs="EPSG:32613",
        )


def test_rejects_feature_that_collapses_after_erosion(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    _write_signal_raster(run_dir)
    _write_run_quality(run_dir)
    polygon_path = tmp_path / "small.geojson"
    _write_json(
        polygon_path,
        {
            "type": "FeatureCollection",
            "features": [
                _feature("small", "anchor", _polygon(20, 300, 50, 330), depth=(0.4, 0.5, 0.6)),
                _feature("large", "anchor", _polygon(250, 200, 380, 350), depth=(1.4, 1.5, 1.6)),
            ],
        },
    )

    with pytest.raises(OperatorSignalExtractionError, match="after erosion"):
        extract_operator_depth_signals(
            run_dir=run_dir,
            polygons_path=polygon_path,
            output_dir=tmp_path / "output",
            site_id="site",
            method_version="method",
            calibration_dataset_version="data",
            input_crs="EPSG:32613",
            erosion_pixels=1,
            minimum_valid_pixels=5,
        )


def test_requires_canonical_log_ratio_raster(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    _write_run_quality(run_dir)
    polygon_path = tmp_path / "reviewed.geojson"
    _write_reviewed_polygons(polygon_path)

    with pytest.raises(FileNotFoundError, match="logRatio_dB.tif"):
        extract_operator_depth_signals(
            run_dir=run_dir,
            polygons_path=polygon_path,
            output_dir=tmp_path / "output",
            site_id="site",
            method_version="method",
            calibration_dataset_version="data",
            input_crs="EPSG:32613",
        )
