from __future__ import annotations

import asyncio
import json
from pathlib import Path

import numpy as np
import pytest

from app.config import Settings
from app.db.models.enums import ArtifactClass
from app.pipeline._base import StageContext
from app.pipeline.stages.elevation_change import (
    CHANGE_TIF_NAME,
    STAGE_DIR_NAME,
    STATUS_MEASURED,
    STATUS_NO_MEASURABLE_CHANGE,
    SUMMARY_NAME,
    ZONES_GEOJSON_NAME,
    ElevationChangeStage,
)
from app.pipeline.stages.grid import DEFAULT_NODATA, grid_spec_from_manifest
from app.services.grid import GridManifest

SIZE = 640
SCALE_M = 10
TILE_SIZE = 320

COVERS = {
    "shallow": (slice(100, 200), slice(100, 200), 0.60),
    "middle": (slice(100, 200), slice(360, 460), 1.00),
    "deep": (slice(400, 500), slice(400, 500), 1.60),
}


def _grid_spec():
    manifest = GridManifest(
        epsg=32613,
        utm_zone=13,
        hemisphere="north",
        scale_m=SCALE_M,
        size_px=SIZE,
        crs_transform=[float(SCALE_M), 0.0, 500000.0, 0.0, -float(SCALE_M), 4000000.0],
        bounds_m={
            "xmin": 500000.0,
            "ymin": 4000000.0 - SIZE * SCALE_M,
            "xmax": 500000.0 + SIZE * SCALE_M,
            "ymax": 4000000.0,
        },
    )
    return grid_spec_from_manifest(manifest, nodata=DEFAULT_NODATA)


def _surfaces(*, noise_sigma_m: float = 0.05, datum_offset_m: float = 3.25, placed: bool = True):
    rng = np.random.default_rng(2026)
    rows, cols = np.indices((SIZE, SIZE), dtype=np.float64)
    base = 1500.0 + rows * 0.02 + cols * 0.01

    material = np.zeros((SIZE, SIZE), dtype=np.float64)
    if placed:
        for row_slice, col_slice, thickness in COVERS.values():
            material[row_slice, col_slice] = thickness

    early = base + rng.normal(0.0, noise_sigma_m, base.shape)
    late = base + material + datum_offset_m + rng.normal(0.0, noise_sigma_m, base.shape)
    return early.astype(np.float32), late.astype(np.float32)


def _fetcher_for(surface: np.ndarray):
    """Serve tiles out of a full-grid array, matching the DEM tiling contract."""

    def fetch_tile(*, grid_spec, tile_row, tile_col, xmin, ymin, xmax, ymax, size):
        del grid_spec, xmin, ymin, xmax, ymax
        row_start = tile_row * size
        col_start = tile_col * size
        return surface[row_start : row_start + size, col_start : col_start + size].astype(
            np.float32
        )

    return fetch_tile


def _run_stage(tmp_path: Path, *, placed: bool = True, **kwargs):
    early, late = _surfaces(placed=placed)
    stage = ElevationChangeStage(
        grid_spec=_grid_spec(),
        early_tile_fetcher=_fetcher_for(early),
        late_tile_fetcher=_fetcher_for(late),
        tile_size=TILE_SIZE,
        **kwargs,
    )
    run_dir = tmp_path / "run"
    run_dir.mkdir(parents=True, exist_ok=True)
    context = StageContext(run_id="test-run", settings=Settings(), run_dir=run_dir)
    result = asyncio.run(stage.run(context))
    summary = json.loads((run_dir / STAGE_DIR_NAME / SUMMARY_NAME).read_text(encoding="utf-8"))
    return result, summary, run_dir


class TestMeasuredRun:
    def test_reports_a_measured_status(self, tmp_path: Path) -> None:
        _, summary, _ = _run_stage(tmp_path)
        assert summary["status"] == STATUS_MEASURED

    def test_removes_the_datum_offset(self, tmp_path: Path) -> None:
        _, summary, _ = _run_stage(tmp_path)
        offset = summary["coregistration"]["stable_ground"]["offset_m"]
        assert offset == pytest.approx(3.25, abs=0.02)

    def test_writes_the_thickness_raster(self, tmp_path: Path) -> None:
        _, _, run_dir = _run_stage(tmp_path)
        raster = run_dir / STAGE_DIR_NAME / CHANGE_TIF_NAME
        assert raster.is_file()
        assert raster.with_name(f"{raster.name}.meta.json").is_file()

    def test_measures_each_placed_cover(self, tmp_path: Path) -> None:
        _, summary, _ = _run_stage(tmp_path)
        measured = sorted(zone["mean_change_m"] for zone in summary["zones"])
        for expected in (0.60, 1.00, 1.60):
            assert any(abs(value - expected) < 0.10 for value in measured), (
                f"no zone near {expected}: {measured}"
            )

    def test_writes_reviewed_zones_with_anchors_and_a_candidate(self, tmp_path: Path) -> None:
        _, summary, run_dir = _run_stage(tmp_path)
        assert summary["anchor_count"] >= 2
        assert summary["candidate_count"] >= 1

        payload = json.loads(
            (run_dir / STAGE_DIR_NAME / ZONES_GEOJSON_NAME).read_text(encoding="utf-8")
        )
        assert payload["type"] == "FeatureCollection"
        assert payload.get("template_only") is not True
        roles = [feature["properties"]["role"] for feature in payload["features"]]
        assert roles.count("anchor") >= 2
        assert roles.count("candidate") >= 1

    def test_zone_polygons_are_inside_the_grid_extent(self, tmp_path: Path) -> None:
        _, _, run_dir = _run_stage(tmp_path)
        payload = json.loads(
            (run_dir / STAGE_DIR_NAME / ZONES_GEOJSON_NAME).read_text(encoding="utf-8")
        )
        grid = _grid_spec()
        bounds = grid.manifest.bounds_m
        for feature in payload["features"]:
            for ring in feature["geometry"]["coordinates"]:
                for x, y in ring:
                    assert bounds["xmin"] <= x <= bounds["xmax"]
                    assert bounds["ymin"] <= y <= bounds["ymax"]

    def test_records_what_it_does_and_does_not_measure(self, tmp_path: Path) -> None:
        _, summary, _ = _run_stage(tmp_path)
        assert summary["measures"] == "placed_material_thickness"
        assert summary["does_not_measure"] == "depth_to_a_buried_object"
        assert summary["measurement_kind"] == "public_elevation_change_v1"

    def test_records_the_source_pair_it_used(self, tmp_path: Path) -> None:
        _, summary, _ = _run_stage(tmp_path)
        pair = summary["source_pair"]
        assert pair["early"]["asset_id"]
        assert pair["late"]["asset_id"]
        assert pair["minimum_detectable_thickness_m"] > 0


class TestPrivacy:
    def test_every_artifact_is_filesystem_only(self, tmp_path: Path) -> None:
        result, _, _ = _run_stage(tmp_path)
        assert result.artifacts
        for artifact in result.artifacts:
            assert artifact.artifact_class == ArtifactClass.FILESYSTEM_ONLY
            assert artifact.http_servable is False

    def test_stage_metadata_carries_no_coordinates(self, tmp_path: Path) -> None:
        result, _, _ = _run_stage(tmp_path)
        serialised = json.dumps(result.metadata)
        # The grid origin would be the giveaway if geometry leaked into metadata.
        assert "500000" not in serialised
        assert "4000000" not in serialised
        assert "coordinates" not in serialised


class TestAbstention:
    def test_undisturbed_ground_yields_no_measurable_change(self, tmp_path: Path) -> None:
        # The null control from the validation plan: flat unchanged terrain must
        # not produce invented thickness.
        _, summary, run_dir = _run_stage(tmp_path, placed=False)

        assert summary["status"] == STATUS_NO_MEASURABLE_CHANGE
        assert summary["zones"] == []
        assert "no_measurable_placed_material" in summary["warnings"]
        assert not (run_dir / STAGE_DIR_NAME / ZONES_GEOJSON_NAME).exists()

    def test_still_writes_a_summary_when_nothing_is_measurable(self, tmp_path: Path) -> None:
        result, _, run_dir = _run_stage(tmp_path, placed=False)
        assert (run_dir / STAGE_DIR_NAME / SUMMARY_NAME).is_file()
        assert any(
            artifact.name == "elevation_change_summary" for artifact in result.artifacts
        )

    def test_notes_when_there_are_too_few_zones_to_withhold(self, tmp_path: Path) -> None:
        # A large minimum separation collapses the zones to one, which is fewer
        # than a withheld validation zone requires.
        _, summary, _ = _run_stage(tmp_path, band_count=2, min_pixels=1_000_000)
        assert summary["status"] == STATUS_NO_MEASURABLE_CHANGE


class TestGlobalTierHonesty:
    def test_global_coverage_reports_a_coarse_detection_floor(self, tmp_path: Path) -> None:
        _, summary, _ = _run_stage(tmp_path, coverage="global", target_thickness_m=0.7)
        pair = summary["source_pair"]

        assert pair["minimum_detectable_thickness_m"] > 1.0
        assert "target_thickness_below_detection_floor" in summary["warnings"]
        assert "coarse_resolution_small_features_unresolvable" in summary["warnings"]


class TestSourceSelectionFailure:
    def test_unknown_coverage_is_reported_not_raised(self, tmp_path: Path) -> None:
        # A stage that raised here would fail the whole run for a configuration
        # mistake; recording it keeps the rest of the run usable.
        result, summary, _ = _run_stage(tmp_path, coverage="mars")

        assert summary["status"] == "not_available"
        assert any("source_selection_failed" in warning for warning in summary["warnings"])
        assert result.metadata["status"] == "not_available"


class TestEarthEngineIsolation:
    def test_the_package_imports_without_an_earth_engine_session(self) -> None:
        # Only ee_fetch may import ee, so the measurement code stays testable.
        repository_root = Path(__file__).resolve().parents[2]
        package = repository_root / "app" / "pipeline" / "elevation_change"
        importing_ee = [
            path.name
            for path in sorted(package.glob("*.py"))
            if "import ee" in path.read_text(encoding="utf-8")
        ]
        assert importing_ee == ["ee_fetch.py"]
