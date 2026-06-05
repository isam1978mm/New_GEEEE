from __future__ import annotations

import inspect
from datetime import date, timedelta

import pytest

from app.config import Settings
from app.services.earth_engine_control import (
    EarthEnginePlanRequest,
    build_earth_engine_plan,
    import_earth_engine,
)
from app.services.redaction import verify_redacted


FORBIDDEN_ARTIFACT_SUFFIXES = {
    ".tif",
    ".tiff",
    ".npy",
    ".geojson",
    ".kmz",
    ".kml",
    ".html",
    ".png",
    ".jpg",
    ".jpeg",
    ".csv",
}


def test_valid_request_returns_dry_run_plan_metadata() -> None:
    request = EarthEnginePlanRequest(
        latitude=35.59499,
        longitude=36.12694,
        acquisition_start=date(2026, 1, 1),
        acquisition_end=date(2026, 1, 31),
        cloud_percent_max=20,
        sar_orbit="any",
        sar_polarization="VV",
    )

    plan = build_earth_engine_plan(request, settings=_settings_without_auth()).model_dump()

    assert plan["dry_run"] is True
    assert plan["execution_status"] == "auth_not_configured"
    assert plan["auth_readiness"]["status"] == "auth_not_configured"
    assert plan["selected_point_preview"]["north_south_degrees"] == pytest.approx(35.59499)
    assert plan["selected_point_preview"]["east_west_degrees"] == pytest.approx(36.12694)
    assert plan["roi_window_preview"]["width_meters"] == pytest.approx(6400.0)
    assert plan["grid_preview"]["width_cells"] == 640
    assert plan["planned_provider_families"] == [
        "Sentinel-2 optical planning",
        "Sentinel-1 SAR planning",
        "Landsat thermal planning",
        "DEM planning",
    ]
    assert plan["warnings"]
    verify_redacted(plan)


@pytest.mark.parametrize(
    ("latitude", "longitude"),
    [
        (91.0, 36.0),
        (-91.0, 36.0),
        (35.0, 181.0),
        (35.0, -181.0),
    ],
)
def test_invalid_coordinate_ranges_are_rejected(latitude: float, longitude: float) -> None:
    with pytest.raises(ValueError):
        EarthEnginePlanRequest(
            latitude=latitude,
            longitude=longitude,
            acquisition_start=date(2026, 1, 1),
            acquisition_end=date(2026, 1, 31),
        )


def test_invalid_date_range_is_rejected() -> None:
    with pytest.raises(ValueError):
        EarthEnginePlanRequest(
            latitude=35.0,
            longitude=36.0,
            acquisition_start=date(2026, 2, 1),
            acquisition_end=date(2026, 1, 1),
        )


def test_overly_large_date_window_is_rejected() -> None:
    with pytest.raises(ValueError):
        EarthEnginePlanRequest(
            latitude=35.0,
            longitude=36.0,
            acquisition_start=date(2025, 1, 1),
            acquisition_end=date(2026, 2, 1),
        )


def test_cloud_threshold_range_is_rejected() -> None:
    with pytest.raises(ValueError):
        EarthEnginePlanRequest(
            latitude=35.0,
            longitude=36.0,
            acquisition_start=date(2026, 1, 1),
            acquisition_end=date(2026, 1, 31),
            cloud_percent_max=101,
        )


def test_backend_auth_ready_without_secret_leak(tmp_path) -> None:
    key_file = tmp_path / "service-account.json"
    key_file.write_text("{}", encoding="utf-8")
    settings = Settings(
        ee_service_account_email="svc@example.com",
        ee_service_account_key_path=key_file,
        ee_real_execution_enabled=True,
    )
    request = EarthEnginePlanRequest(
        latitude=35.0,
        longitude=36.0,
        acquisition_start=date(2026, 1, 1),
        acquisition_end=date(2026, 1, 31),
        dry_run=False,
    )

    plan = build_earth_engine_plan(request, settings=settings).model_dump()
    serialized = str(plan)

    assert plan["execution_status"] == "ready_for_real_execution"
    assert plan["auth_readiness"]["status"] == "ready_for_real_execution"
    assert "svc@example.com" not in serialized
    assert str(key_file) not in serialized
    verify_redacted(plan)


def test_real_execution_request_stays_disabled_without_flag(tmp_path) -> None:
    key_file = tmp_path / "service-account.json"
    key_file.write_text("{}", encoding="utf-8")
    settings = Settings(
        ee_service_account_email="svc@example.com",
        ee_service_account_key_path=key_file,
        ee_real_execution_enabled=False,
    )
    request = EarthEnginePlanRequest(
        latitude=35.0,
        longitude=36.0,
        acquisition_start=date(2026, 1, 1),
        acquisition_end=date(2026, 1, 31),
        dry_run=False,
    )

    plan = build_earth_engine_plan(request, settings=settings)

    assert plan.execution_status == "real_execution_disabled"
    assert plan.auth_readiness.status == "ready_for_real_execution"


def test_dry_run_does_not_import_earth_engine_or_create_artifacts(tmp_path, monkeypatch) -> None:
    imported = False

    def fake_import():
        nonlocal imported
        imported = True
        raise AssertionError("dry-run planning must not import Earth Engine")

    monkeypatch.setattr("app.services.earth_engine_control.import_earth_engine", fake_import)
    request = EarthEnginePlanRequest(
        latitude=35.0,
        longitude=36.0,
        acquisition_start=date(2026, 1, 1),
        acquisition_end=date(2026, 1, 31),
    )

    build_earth_engine_plan(request, settings=_settings_without_auth())

    assert imported is False
    created_artifacts = [
        path
        for path in tmp_path.rglob("*")
        if path.suffix.casefold() in FORBIDDEN_ARTIFACT_SUFFIXES
    ]
    assert created_artifacts == []


def test_earth_engine_import_is_lazy() -> None:
    import app.services.earth_engine_control as earth_engine_control

    source = inspect.getsource(earth_engine_control)
    assert "import ee" not in source
    assert "ee.Authenticate" not in source
    assert callable(import_earth_engine)


def test_no_colab_or_drive_behavior_is_introduced() -> None:
    import app.services.earth_engine_control as earth_engine_control

    source = inspect.getsource(earth_engine_control).casefold()
    assert "drive.mount" not in source
    assert "/content/drive" not in source
    assert "google.colab" not in source
    assert "colab" not in source


def _settings_without_auth() -> Settings:
    return Settings(
        ee_service_account_email=None,
        ee_service_account_key_path=None,
        ee_real_execution_enabled=False,
    )
