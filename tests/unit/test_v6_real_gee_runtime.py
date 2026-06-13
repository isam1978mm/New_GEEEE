from __future__ import annotations

import json

import pytest

from app.services.v6_real_gee_runtime import (
    V6EarthEngineRuntime,
    V6GridConfig,
    V6RuntimeConfig,
    build_v6_grid,
    safe_grid_summary,
    v6_aoi_from_mapping,
    validate_v6_aoi_bounds,
)


class _FakeGeometry:
    def __init__(self) -> None:
        self.call_count = 0

    def Rectangle(self, bounds, *, proj=None, geodesic=False):  # noqa: N802
        self.call_count += 1
        return {"fake_rectangle": True, "member_count": len(bounds)}


class _FakeEarthEngine:
    def __init__(self) -> None:
        self.Geometry = _FakeGeometry()
        self.initialized_project = None
        self.authenticate_called = False

    def Initialize(self, *, project=None):  # noqa: N802
        self.initialized_project = project

    def Authenticate(self):  # noqa: N802
        self.authenticate_called = True


def test_v6_aoi_from_mapping_accepts_bbox_and_redacts_safe_summary() -> None:
    aoi = v6_aoi_from_mapping({"bbox": [0, 10, 2, 12]})

    assert aoi.width_degrees == 2
    assert aoi.height_degrees == 2
    summary = aoi.safe_summary()
    serialized = json.dumps(summary, sort_keys=True)
    assert summary["bounds_values_redacted"] is True
    assert "west" not in serialized
    assert "south" not in serialized
    assert "east" not in serialized
    assert "north" not in serialized


def test_validate_v6_aoi_bounds_rejects_invalid_bounds() -> None:
    with pytest.raises(ValueError, match="west must be less than east"):
        validate_v6_aoi_bounds(west=2, south=10, east=1, north=12)

    with pytest.raises(ValueError, match="positive integers"):
        V6GridConfig(rows=0, cols=2)


def test_build_v6_grid_is_deterministic_and_row_major() -> None:
    aoi = validate_v6_aoi_bounds(west=0, south=10, east=2, north=12)
    cells = build_v6_grid(aoi=aoi, config=V6GridConfig(rows=2, cols=2))

    assert [cell.cell_id for cell in cells] == [
        "V6_CELL_R001_C001",
        "V6_CELL_R001_C002",
        "V6_CELL_R002_C001",
        "V6_CELL_R002_C002",
    ]
    assert cells[0].row == 1
    assert cells[0].col == 1
    assert cells[-1].row == 2
    assert cells[-1].col == 2


def test_safe_grid_summary_does_not_include_bounds_values() -> None:
    aoi = validate_v6_aoi_bounds(west=0, south=10, east=2, north=12)
    cells = build_v6_grid(aoi=aoi, config=V6GridConfig(rows=2, cols=2))

    summary = safe_grid_summary(cells)
    serialized = json.dumps(summary, sort_keys=True)

    assert summary["cell_count"] == 4
    assert summary["bounds_values_redacted"] is True
    assert summary["first_cell_id"] == "V6_CELL_R001_C001"
    assert summary["last_cell_id"] == "V6_CELL_R002_C002"
    assert "west" not in serialized
    assert "south" not in serialized
    assert "east" not in serialized
    assert "north" not in serialized


def test_runtime_adapter_uses_injected_module_without_importing_real_service() -> None:
    fake_ee = _FakeEarthEngine()
    runtime = V6EarthEngineRuntime(
        V6RuntimeConfig(project_id="synthetic-project"),
        ee_module=fake_ee,
    )
    aoi = validate_v6_aoi_bounds(west=0, south=10, east=2, north=12)

    geometry = runtime.rectangle_geometry(aoi)

    assert runtime.initialized is True
    assert fake_ee.initialized_project == "synthetic-project"
    assert fake_ee.authenticate_called is False
    assert fake_ee.Geometry.call_count == 1
    assert geometry == {"fake_rectangle": True, "member_count": 4}


def test_runtime_adapter_keeps_interactive_auth_disabled_by_default() -> None:
    fake_ee = _FakeEarthEngine()
    runtime = V6EarthEngineRuntime(ee_module=fake_ee)

    runtime.initialize()

    assert fake_ee.authenticate_called is False
    assert fake_ee.initialized_project is None
