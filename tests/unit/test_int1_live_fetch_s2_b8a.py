from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
import int1_live_fetch_s2_b8a as live_fetch


def _write_run(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "grid_manifest.json").write_text(
        json.dumps(
            {
                "epsg": 32637,
                "scale_m": 10.0,
                "size_px": 640,
                "crs_transform": [10.0, 0.0, 500000.0, 0.0, -10.0, 4100000.0],
                "bounds_m": {
                    "xmin": 500000.0,
                    "ymin": 4093600.0,
                    "xmax": 506400.0,
                    "ymax": 4100000.0,
                },
                "nodata": -9999.0,
            }
        ),
        encoding="utf-8",
    )
    (root / "stage_s2_indices.manifest.json").write_text(
        json.dumps({"metadata": {"source_bands": ["B2", "B3", "B4", "B8", "B11", "B12", "B1"]}}),
        encoding="utf-8",
    )


def test_dry_run_reports_contract_without_calling_earth_engine(tmp_path: Path) -> None:
    _write_run(tmp_path)

    result = live_fetch.fetch_live_b8a(app_run_dir=tmp_path)

    assert result["ok"] is True
    assert result["status"] == "dry_run_ready"
    assert result["source_collection"] == "COPERNICUS/S2_SR_HARMONIZED"
    assert result["band_name"] == "B8A"
    assert result["grid_size_px"] == 640
    assert result["earth_engine_called"] is False
    assert result["output_npy_written"] is False


def test_cli_dry_run(tmp_path: Path) -> None:
    _write_run(tmp_path)

    completed = subprocess.run(
        [
            sys.executable,
            str(Path(__file__).parent.parent.parent / "scripts" / "int1_live_fetch_s2_b8a.py"),
            "--app-run-dir",
            str(tmp_path),
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert completed.returncode == 0
    payload = json.loads(completed.stdout)
    assert payload["status"] == "dry_run_ready"
    assert payload["earth_engine_called"] is False


def test_existing_outputs_are_reported_in_dry_run(tmp_path: Path) -> None:
    _write_run(tmp_path)
    (tmp_path / "S2_B8A_640.npy").write_bytes(b"placeholder")

    result = live_fetch.fetch_live_b8a(app_run_dir=tmp_path)

    assert result["existing_outputs"] == ["S2_B8A_640.npy"]
