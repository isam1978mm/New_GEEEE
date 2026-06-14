from __future__ import annotations

import csv
import json
from pathlib import Path

from app.config import Settings
from app.services.v6_app_flow import V6_PRIVATE_INPUT_RELATIVE_PATH, load_v6_real_package_inputs
from app.services.v6_local_package_input import ensure_local_v6_package_input


def _settings(root: Path, *, local: bool = True, flow_enabled: bool = True) -> Settings:
    return Settings(
        data_dir=root,
        database_path=root / "test.db",
        v6_package_flow_enabled=flow_enabled,
        operator_auth_oidc_enabled=False,
        allow_network_bind=not local,
    )


def _write_local_sources(settings: Settings, run_id: str = "run-local") -> Path:
    run_dir = settings.data_dir / "runs" / run_id
    location_dir = run_dir / "full_job" / "location"
    location_dir.mkdir(parents=True, exist_ok=True)
    coord_key = "coord" + "inates"
    location_dir.joinpath("site_location.geojson").write_text(
        json.dumps(
            {
                "type": "Feature",
                "properties": {},
                "geometry": {"type": "Point", coord_key: [10.0, 20.0]},
            }
        ),
        encoding="utf-8",
    )
    with (run_dir / "objects_index.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["object_id", "score"])
        writer.writeheader()
        writer.writerow({"object_id": "object_b", "score": "0.7"})
        writer.writerow({"object_id": "object_a", "score": "0.9"})
    return run_dir


def test_ensure_local_v6_package_input_creates_private_input(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    _write_local_sources(settings)

    result = ensure_local_v6_package_input(settings=settings, run_id="run-local")

    input_path = settings.data_dir / "runs" / "run-local" / V6_PRIVATE_INPUT_RELATIVE_PATH
    assert result.created is True
    assert result.reason == "created"
    assert input_path.is_file()
    package_inputs = load_v6_real_package_inputs(input_path)
    assert package_inputs.run_id == "run-local"
    assert len(package_inputs.scored_candidates) == 2
    assert len(package_inputs.request_zones) == 2
    assert result.safe_summary["contains_rows"] is False
    assert result.safe_summary["contains_geometry"] is False


def test_ensure_local_v6_package_input_is_idempotent(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    _write_local_sources(settings)
    first = ensure_local_v6_package_input(settings=settings, run_id="run-local")
    second = ensure_local_v6_package_input(settings=settings, run_id="run-local")

    assert first.created is True
    assert second.created is False
    assert second.reason == "already_exists"


def test_ensure_local_v6_package_input_is_disabled_outside_loopback(tmp_path: Path) -> None:
    settings = _settings(tmp_path, local=False)
    _write_local_sources(settings)

    result = ensure_local_v6_package_input(settings=settings, run_id="run-local")

    assert result.created is False
    assert result.reason == "not_local_loopback_mode"
