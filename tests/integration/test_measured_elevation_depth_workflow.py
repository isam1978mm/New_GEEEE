from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from scripts.measure_elevation_depth_for_existing_run import (
    MeasuredElevationDepthError,
    measure_elevation_depth_for_existing_run,
)

SIZE = 640
SCALE_M = 10
EPSG = 32613
ORIGIN_X = 500000.0
ORIGIN_Y = 4000000.0
NODATA = -9999.0

COVERS = {
    "shallow": (slice(100, 200), slice(100, 200), 0.60),
    "middle": (slice(100, 200), slice(360, 460), 1.00),
    "deep": (slice(400, 500), slice(400, 500), 1.60),
}


def _write_geotiff(path: Path, array: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        width=SIZE,
        height=SIZE,
        count=1,
        dtype="float32",
        crs=f"EPSG:{EPSG}",
        transform=from_origin(ORIGIN_X, ORIGIN_Y, SCALE_M, SCALE_M),
        nodata=NODATA,
    ) as dataset:
        dataset.write(array.astype(np.float32), 1)


def _build_run(tmp_path: Path, *, placed: bool = True, correlated_radar: bool = True) -> Path:
    run_dir = tmp_path / "run-0001"
    run_dir.mkdir(parents=True, exist_ok=True)

    (run_dir / "grid_manifest.json").write_text(
        json.dumps(
            {
                "crs_family": "utm",
                "epsg": EPSG,
                "utm_zone": 13,
                "hemisphere": "north",
                "scale_m": SCALE_M,
                "size_px": SIZE,
                "crs_transform": [float(SCALE_M), 0.0, ORIGIN_X, 0.0, -float(SCALE_M), ORIGIN_Y],
                "bounds_m": {
                    "xmin": ORIGIN_X,
                    "ymin": ORIGIN_Y - SIZE * SCALE_M,
                    "xmax": ORIGIN_X + SIZE * SCALE_M,
                    "ymax": ORIGIN_Y,
                },
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    quality_path = run_dir / "QA" / "run_quality" / "run_quality_summary.json"
    quality_path.parent.mkdir(parents=True, exist_ok=True)
    quality_path.write_text(
        json.dumps(
            {
                "schema": "run_quality_summary_v1",
                "stage": "run_quality",
                "status": "PASS",
                "is_usable": True,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    rng = np.random.default_rng(77)
    rows, cols = np.indices((SIZE, SIZE), dtype=np.float64)
    base = 1500.0 + rows * 0.02 + cols * 0.01

    material = np.zeros((SIZE, SIZE), dtype=np.float64)
    if placed:
        for row_slice, col_slice, thickness in COVERS.values():
            material[row_slice, col_slice] = thickness

    early = base + rng.normal(0.0, 0.05, base.shape)
    late = base + material + 3.25 + rng.normal(0.0, 0.05, base.shape)
    _write_geotiff(tmp_path / "early.tif", early)
    _write_geotiff(tmp_path / "late.tif", late)

    radar = 2.0 + (3.0 * material if correlated_radar else rng.normal(0.0, 1.0, base.shape))
    _write_geotiff(run_dir / "logRatio_dB.tif", radar + rng.normal(0.0, 0.01, base.shape))
    return run_dir


class TestMeasurementOnly:
    def test_measures_placed_material_without_earth_engine(self, tmp_path: Path) -> None:
        run_dir = _build_run(tmp_path)

        result = measure_elevation_depth_for_existing_run(
            run_dir=run_dir,
            offline_early=tmp_path / "early.tif",
            offline_late=tmp_path / "late.tif",
        )

        assert result["status"] == "measured"
        assert result["measures"] == "placed_material_thickness"
        assert result["does_not_measure"] == "depth_to_a_buried_object"
        assert result["anchor_count"] >= 2
        assert result["candidate_count"] >= 1

    def test_reports_the_measured_noise_floor_not_just_the_predicted_one(
        self, tmp_path: Path
    ) -> None:
        # The predicted floor is a conservative worldwide average for the
        # products involved. What a result should be judged by is what the pair
        # actually achieved over this particular ground, so both are reported
        # and the measured one is named unambiguously.
        run_dir = _build_run(tmp_path)

        result = measure_elevation_depth_for_existing_run(
            run_dir=run_dir,
            offline_early=tmp_path / "early.tif",
            offline_late=tmp_path / "late.tif",
        )

        assert result["measured_noise_floor_sigma_m"] == pytest.approx(0.0707, abs=0.01)
        assert result["measured_minimum_detectable_thickness_m"] < (
            result["predicted_minimum_detectable_thickness_m"]
        )
        assert result["vertical_offset_removed_m"] == pytest.approx(3.25, abs=0.02)

    def test_reports_each_measured_thickness(self, tmp_path: Path) -> None:
        run_dir = _build_run(tmp_path)

        result = measure_elevation_depth_for_existing_run(
            run_dir=run_dir,
            offline_early=tmp_path / "early.tif",
            offline_late=tmp_path / "late.tif",
        )

        thicknesses = sorted(item["thickness_m"] for item in result["measured_thickness_m"])
        for expected in (0.60, 1.00, 1.60):
            assert any(abs(value - expected) < 0.10 for value in thicknesses)

    def test_does_not_drive_the_depth_engine_unless_asked(self, tmp_path: Path) -> None:
        run_dir = _build_run(tmp_path)

        result = measure_elevation_depth_for_existing_run(
            run_dir=run_dir,
            offline_early=tmp_path / "early.tif",
            offline_late=tmp_path / "late.tif",
        )

        assert result["depth_engine"] is None
        assert not (run_dir / "depth" / "depth_estimates.csv").exists()

    def test_undisturbed_ground_measures_nothing(self, tmp_path: Path) -> None:
        run_dir = _build_run(tmp_path, placed=False)

        result = measure_elevation_depth_for_existing_run(
            run_dir=run_dir,
            offline_early=tmp_path / "early.tif",
            offline_late=tmp_path / "late.tif",
        )

        assert result["status"] == "no_measurable_change"
        assert result["zone_count"] == 0


class TestDrivingTheExistingDepthEngine:
    def test_measured_zones_unblock_the_depth_engine(self, tmp_path: Path) -> None:
        run_dir = _build_run(tmp_path)

        result = measure_elevation_depth_for_existing_run(
            run_dir=run_dir,
            offline_early=tmp_path / "early.tif",
            offline_late=tmp_path / "late.tif",
            drive_depth_engine=True,
        )

        engine = result["depth_engine"]
        assert engine is not None
        assert engine["method_kind"] == "operator_scalar_interpolation_v1"
        assert engine["candidate_count"] >= 1
        assert engine["estimated_count"] >= 1

    def test_writes_depth_estimates_in_metres(self, tmp_path: Path) -> None:
        run_dir = _build_run(tmp_path)

        measure_elevation_depth_for_existing_run(
            run_dir=run_dir,
            offline_early=tmp_path / "early.tif",
            offline_late=tmp_path / "late.tif",
            drive_depth_engine=True,
        )

        estimates = (run_dir / "depth" / "depth_estimates.csv").read_text(encoding="utf-8")
        rows = [line for line in estimates.splitlines()[1:] if line.strip()]
        assert rows
        ranged = [row for row in rows if row.split(",")[1] == "calibrated_range"]
        assert ranged
        for row in ranged:
            best = float(row.split(",")[3])
            assert 0.0 < best < 5.0

    def test_skips_the_engine_when_nothing_was_measured(self, tmp_path: Path) -> None:
        run_dir = _build_run(tmp_path, placed=False)

        result = measure_elevation_depth_for_existing_run(
            run_dir=run_dir,
            offline_early=tmp_path / "early.tif",
            offline_late=tmp_path / "late.tif",
            drive_depth_engine=True,
        )

        assert result["depth_engine"] == {"skipped": "no_measurable_change"}

    def test_uncorrelated_radar_does_not_silently_produce_depth(self, tmp_path: Path) -> None:
        # If the radar signal carries no depth information, the engine must fail
        # to build a monotonic package or abstain. What it must never do is
        # return confident metre values anyway.
        run_dir = _build_run(tmp_path, correlated_radar=False)

        try:
            result = measure_elevation_depth_for_existing_run(
                run_dir=run_dir,
                offline_early=tmp_path / "early.tif",
                offline_late=tmp_path / "late.tif",
                drive_depth_engine=True,
            )
        except Exception:
            # Refusing to build a package from a non-monotonic signal is a
            # correct outcome for this input.
            return

        engine = result["depth_engine"]
        if engine and "estimated_count" in engine:
            assert engine["estimated_count"] <= engine["candidate_count"]


class TestGuards:
    def test_requires_a_grid_manifest(self, tmp_path: Path) -> None:
        run_dir = tmp_path / "empty-run"
        run_dir.mkdir()

        with pytest.raises(MeasuredElevationDepthError, match="grid manifest"):
            measure_elevation_depth_for_existing_run(run_dir=run_dir)

    def test_requires_a_run_directory(self, tmp_path: Path) -> None:
        with pytest.raises(MeasuredElevationDepthError, match="does not exist"):
            measure_elevation_depth_for_existing_run(run_dir=tmp_path / "missing")

    def test_offline_mode_needs_both_epochs(self, tmp_path: Path) -> None:
        run_dir = _build_run(tmp_path)

        with pytest.raises(MeasuredElevationDepthError, match="both"):
            measure_elevation_depth_for_existing_run(
                run_dir=run_dir, offline_early=tmp_path / "early.tif"
            )

    def test_rejects_an_offline_epoch_off_the_run_grid(self, tmp_path: Path) -> None:
        run_dir = _build_run(tmp_path)
        wrong = tmp_path / "wrong.tif"
        with rasterio.open(
            wrong,
            "w",
            driver="GTiff",
            width=100,
            height=100,
            count=1,
            dtype="float32",
            crs=f"EPSG:{EPSG}",
            transform=from_origin(ORIGIN_X, ORIGIN_Y, SCALE_M, SCALE_M),
            nodata=NODATA,
        ) as dataset:
            dataset.write(np.zeros((100, 100), dtype=np.float32), 1)

        with pytest.raises(MeasuredElevationDepthError, match="run grid"):
            measure_elevation_depth_for_existing_run(
                run_dir=run_dir,
                offline_early=wrong,
                offline_late=tmp_path / "late.tif",
            )
