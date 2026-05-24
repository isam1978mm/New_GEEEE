from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

from scripts import export_cell25_sar_intermediates
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


def test_export_cell25_sar_intermediates_help_lists_modes(monkeypatch, capsys) -> None:
    monkeypatch.setattr(sys, "argv", ["export_cell25_sar_intermediates.py", "--help"])

    with pytest.raises(SystemExit) as exc:
        main()

    assert exc.value.code == 0
    help_text = capsys.readouterr().out
    assert "--mode {post-rtc-only,live-cell25-full}" in help_text
    assert "post-rtc-only" in help_text
    assert "live-cell25-full" in help_text


def test_export_cell25_sar_intermediates_live_mode_dispatches_explicitly(
    tmp_path: Path,
    monkeypatch,
) -> None:
    app_run_dir = tmp_path / "data" / "runs" / "run-123"
    output_dir = tmp_path / "reports" / "sar_intermediates"
    app_run_dir.mkdir(parents=True)
    called: dict[str, object] = {}

    def fake_export_app_full_intermediate_manifest(**kwargs):
        called.update(kwargs)
        output_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = output_dir / "sar_intermediate_manifest.json"
        manifest_path.write_text("{}", encoding="utf-8")
        return manifest_path

    monkeypatch.setattr(
        export_cell25_sar_intermediates,
        "export_app_full_intermediate_manifest",
        fake_export_app_full_intermediate_manifest,
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "export_cell25_sar_intermediates.py",
            "--app-run-dir",
            str(app_run_dir),
            "--output-dir",
            str(output_dir),
            "--mode",
            "live-cell25-full",
        ],
    )

    assert main() == 0
    assert called["app_run_dir"] == app_run_dir
    assert called["output_dir"] == output_dir
