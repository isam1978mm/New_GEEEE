from __future__ import annotations

import asyncio
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from pyproj import Transformer

from app.db.models.enums import ArtifactClass
from app.pipeline._base import StageContext
from app.pipeline.stages.grid import GridStage, grid_spec_from_notebook_radar_meta
from app.services.grid import build_grid_manifest


def test_grid_manifest_is_deterministic_for_same_input() -> None:
    first = build_grid_manifest(43.6532, -79.3832)
    second = build_grid_manifest(43.6532, -79.3832)
    assert first == second


def test_grid_manifest_changes_utm_zone_with_longitude() -> None:
    western = build_grid_manifest(43.6532, -79.3832)
    eastern = build_grid_manifest(43.6532, 31.2357)
    assert western.utm_zone != eastern.utm_zone
    assert western.epsg != eastern.epsg


def test_grid_manifest_transform_changes_with_roi_inside_same_utm_zone() -> None:
    first = build_grid_manifest(43.6532, -79.3832)
    second = build_grid_manifest(43.7000, -79.3000)

    assert first.utm_zone == second.utm_zone
    assert first.epsg == second.epsg
    assert first.crs_transform != second.crs_transform
    assert first.bounds_m != second.bounds_m


def test_grid_manifest_uses_hemisphere_and_fixed_extent() -> None:
    north = build_grid_manifest(43.6532, -79.3832)
    south = build_grid_manifest(-33.8688, 151.2093)
    assert north.hemisphere == "north"
    assert south.hemisphere == "south"
    assert north.scale_m == 10
    assert north.size_px == 640
    assert north.bounds_m["xmax"] - north.bounds_m["xmin"] == 6400.0
    assert north.bounds_m["ymax"] - north.bounds_m["ymin"] == 6400.0


def test_grid_manifest_is_centered_on_projected_roi_center() -> None:
    lat = 35.59499
    lon = 36.12694
    manifest = build_grid_manifest(lat, lon)
    transformer = Transformer.from_crs("EPSG:4326", f"EPSG:{manifest.epsg}", always_xy=True)
    center_x, center_y = transformer.transform(lon, lat)

    xmin = manifest.bounds_m["xmin"]
    xmax = manifest.bounds_m["xmax"]
    ymin = manifest.bounds_m["ymin"]
    ymax = manifest.bounds_m["ymax"]

    assert abs(((xmin + xmax) / 2.0) - center_x) < 0.01
    assert abs(((ymin + ymax) / 2.0) - center_y) < 0.01
    assert abs(manifest.crs_transform[2] - xmin) < 0.01
    assert abs(manifest.crs_transform[5] - ymax) < 0.01


def test_grid_stage_writes_grid_guard_summary_as_filesystem_only() -> None:
    with TemporaryDirectory() as temp_dir:
        run_dir = Path(temp_dir)
        context = StageContext(run_id="run-1", settings=_settings(run_dir), run_dir=run_dir)
        stage = GridStage(latitude=35.59499, longitude=36.12694)

        result = asyncio.run(stage.run(context))

        assert [artifact.name for artifact in result.artifacts] == ["grid_manifest", "grid_guard_summary"]
        artifact_classes = {artifact.name: artifact.artifact_class for artifact in result.artifacts}
        assert artifact_classes == {
            "grid_manifest": ArtifactClass.LOCAL_SENSITIVE,
            "grid_guard_summary": ArtifactClass.FILESYSTEM_ONLY,
        }
        guard_summary = json.loads((run_dir / "qa" / "grid_dem" / "grid_guard_summary.json").read_text(encoding="utf-8"))
        assert guard_summary["stage"] == "grid"
        assert guard_summary["grid_identity_recorded"] is True
        assert "bounds_m" not in guard_summary
        assert "crs_transform" not in guard_summary


def test_notebook_radar_meta_grid_override_preserves_exact_grid_values(tmp_path: Path) -> None:
    meta_path = tmp_path / "QA_RADAR_META_demo.json"
    transform = [10, 0, 236505.41247268865, 0, -10, 3946029.415191464]
    bounds = [236505.41247268865, 3939629.415191464, 242905.41247268865, 3946029.415191464]
    meta_path.write_text(
        json.dumps(
            {
                "CRS": "EPSG:32637",
                "SCALE": 10.0,
                "OUT_SIZE": 640,
                "NODATA": -9999.0,
                "ct": transform,
                "bounds_utm": bounds,
            }
        ),
        encoding="utf-8",
    )

    grid_spec = grid_spec_from_notebook_radar_meta(meta_path)

    assert grid_spec.crs == "EPSG:32637"
    assert grid_spec.size == 640
    assert grid_spec.nodata == -9999.0
    assert grid_spec.manifest.crs_transform == [float(value) for value in transform]
    assert grid_spec.manifest.bounds_m == {
        "xmin": bounds[0],
        "ymin": bounds[1],
        "xmax": bounds[2],
        "ymax": bounds[3],
    }


def test_grid_stage_override_does_not_recompute_from_lat_lon(tmp_path: Path) -> None:
    meta_path = tmp_path / "QA_RADAR_META_demo.json"
    transform = [10, 0, 236505.41247268865, 0, -10, 3946029.415191464]
    bounds = [236505.41247268865, 3939629.415191464, 242905.41247268865, 3946029.415191464]
    meta_path.write_text(
        json.dumps(
            {
                "CRS": "EPSG:32637",
                "SCALE": 10,
                "OUT_SIZE": 640,
                "NODATA": -9999.0,
                "crsTransform": transform,
                "bounds_utm": bounds,
            }
        ),
        encoding="utf-8",
    )
    override = grid_spec_from_notebook_radar_meta(meta_path)
    settings = _settings(tmp_path)
    context = StageContext(run_id="run-1", settings=settings, run_dir=tmp_path)
    stage = GridStage(latitude=43.6532, longitude=-79.3832, grid_spec_override=override)

    asyncio.run(stage.run(context))

    written = json.loads((settings.data_dir / "runs" / "run-1" / "grid_manifest.json").read_text(encoding="utf-8"))
    assert written["epsg"] == 32637
    assert written["crs_transform"] == [float(value) for value in transform]
    assert written["bounds_m"] == {
        "xmin": bounds[0],
        "ymin": bounds[1],
        "xmax": bounds[2],
        "ymax": bounds[3],
    }


def _settings(run_dir: Path):
    from app.config import Settings

    data_dir = run_dir / "data"
    return Settings(data_dir=data_dir, database_path=data_dir / "db.sqlite")
