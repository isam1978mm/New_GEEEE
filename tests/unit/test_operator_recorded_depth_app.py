from __future__ import annotations

from pathlib import Path

from pyproj import Transformer

from app.services.operator_recorded_depth_app import (
    REVIEWED_PLOT_TO_ZONE,
    _geometry_inside_run_bounds,
    _load_or_rebuild_recorded_package,
    _measurement_payload,
)
from app.pipeline.depth.recorded import load_recorded_depth_package
from scripts.build_tyrone_recorded_depth_package import build_tyrone_recorded_depth_package


def test_reviewed_plot_mapping_is_exactly_tp5_tp6() -> None:
    assert REVIEWED_PLOT_TO_ZONE == {"TP5": "tyrone_tp5", "TP6": "tyrone_tp6"}


def test_geometry_must_be_fully_inside_run_bounds() -> None:
    geometry = {
        "type": "Polygon",
        "coordinates": [[[-108.42, 32.72], [-108.41, 32.72], [-108.41, 32.73], [-108.42, 32.73], [-108.42, 32.72]]],
    }
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:4326", always_xy=True)
    assert _geometry_inside_run_bounds(
        geometry,
        transformer=transformer,
        bounds={"xmin": -108.43, "ymin": 32.71, "xmax": -108.40, "ymax": 32.74},
    )
    assert not _geometry_inside_run_bounds(
        geometry,
        transformer=transformer,
        bounds={"xmin": -108.419, "ymin": 32.71, "xmax": -108.40, "ymax": 32.74},
    )


def test_record_payload_uses_recorded_fields_only(tmp_path: Path) -> None:
    package_dir = tmp_path / "recorded"
    build_tyrone_recorded_depth_package(package_dir)
    package = load_recorded_depth_package(package_dir)
    zone = package.zone("tyrone_tp5")
    assert zone is not None

    payload = _measurement_payload(plot_id="TP5", zone=zone)
    assert payload["depth_status"] == "recorded_measurement"
    assert payload["recorded_depth_mean_m"] == 0.68072
    assert payload["recorded_depth_ci95_low_m"] == 0.65532
    assert payload["recorded_depth_ci95_high_m"] == 0.70612
    assert payload["recorded_sample_count"] == 5
    assert "estimated_depth_best_m" not in payload
    assert "no_predictive_extrapolation" in payload["warnings"]


def test_stale_generated_package_is_rebuilt_and_reverified(tmp_path: Path) -> None:
    package_dir = tmp_path / "recorded"
    build_tyrone_recorded_depth_package(package_dir)

    manifest_path = package_dir / "depth_method_manifest.json"
    manifest_path.write_text(
        manifest_path.read_text(encoding="utf-8") + "\n",
        encoding="utf-8",
    )

    package = _load_or_rebuild_recorded_package(package_dir)
    zone = package.zone("tyrone_tp5")
    assert zone is not None
    assert zone.measurement.mean_m == 0.68072

    reverified = load_recorded_depth_package(package_dir)
    assert reverified.zone("tyrone_tp6") is not None


def test_operator_panel_is_recorded_lookup_not_calibration_ui() -> None:
    source = Path("frontend-v2/src/app/components/OperatorLocalDepthPanel.tsx").read_text(encoding="utf-8")
    assert "Recorded measured depth" in source
    assert "Load reviewed recorded measurements" in source
    assert "not predicted from this run" in source
    assert "GeoJSON" not in source
    assert "calibration_dataset_version" not in source
    assert "anchor" not in source.lower()


def test_recorded_api_is_separate_from_calibration_endpoint() -> None:
    source = Path("app/api/operator_local_depth.py").read_text(encoding="utf-8")
    assert '@router.post("/runs/{run_id}/operator/recorded-depth")' in source
    assert '@router.post("/runs/{run_id}/operator/local-depth")' in source
    assert "run_operator_recorded_depth_app" in source
