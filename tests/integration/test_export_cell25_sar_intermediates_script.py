from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

from scripts.export_cell25_sar_intermediates import main


def test_export_cell25_sar_intermediates_script_writes_local_only_manifest(tmp_path: Path, monkeypatch) -> None:
    app_run_dir = tmp_path / "data" / "runs" / "run-123"
    output_dir = tmp_path / "reports" / "sar_intermediates"
    npy_dir = app_run_dir / "npy_radar_bands"
    npy_dir.mkdir(parents=True, exist_ok=True)
    vv = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32)
    np.save(npy_dir / "VV_dB.npy", vv)
    np.save(npy_dir / "VH_dB.npy", vv)
    np.save(npy_dir / "logRatio_dB.npy", vv - vv)
    np.save(npy_dir / "incidence.npy", vv + 30.0)

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "export_cell25_sar_intermediates.py",
            "--app-run-dir",
            str(app_run_dir),
            "--output-dir",
            str(output_dir),
        ],
    )

    assert main() == 0

    manifest_path = output_dir / "sar_intermediate_manifest.json"
    assert manifest_path.is_file()
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    serialized = json.dumps(payload, sort_keys=True)
    assert payload["artifact_class"] == "FILESYSTEM_ONLY"
    assert payload["local_only"] is True
    assert payload["stages"]["post_rtc"]["bands"]["VV_dB"] == "post_rtc/VV_dB.npy"
    assert "C:\\" not in serialized
    assert "/Users/" not in serialized
    assert "/home/" not in serialized
    assert "coordinates" not in serialized
