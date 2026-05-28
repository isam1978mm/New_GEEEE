from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def _sanitized_subprocess_env() -> dict[str, str]:
    env = dict(os.environ)
    env.pop("APP_NOTEBOOK_OUTPUT_RUN_DIR", None)
    env.pop("NOTEBOOK_REFERENCE_BUNDLE_DIR", None)
    return env


def test_report_phase5_numeric_output_parity_writes_json_only_when_requested(tmp_path: Path) -> None:
    app_run_dir = tmp_path / "runs" / "run-123"
    reference_root = tmp_path / "reference_bundle"
    app_run_dir.mkdir(parents=True, exist_ok=True)
    reference_root.mkdir(parents=True, exist_ok=True)

    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                f"APP_NOTEBOOK_OUTPUT_RUN_DIR={app_run_dir}",
                f"NOTEBOOK_REFERENCE_BUNDLE_DIR={reference_root}",
            ]
        ),
        encoding="utf-8",
    )

    output_path = tmp_path / "reports" / "phase5_summary.json"
    script_path = Path("scripts/report_phase5_numeric_output_parity.py").resolve()

    result = subprocess.run(
        [sys.executable, str(script_path), "--output", str(output_path)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=True,
        env=_sanitized_subprocess_env(),
    )

    stdout_payload = json.loads(result.stdout)
    written_payload = json.loads(output_path.read_text(encoding="utf-8"))

    assert stdout_payload == written_payload
    assert stdout_payload["summary"]["overall_status"] == "FAIL"
    assert stdout_payload["summary"]["phase5d_alias_integrity_status"] == "CONFIG_REQUIRED"
    assert stdout_payload["summary"]["phase5e_reference_parity_status"] == "CONFIG_REQUIRED"
    assert stdout_payload["summary"]["not_implemented_inventory_status"] == "FAIL"
    assert stdout_payload["summary"]["final_reference_proof_complete"] is False


def test_report_phase5_numeric_output_parity_uses_config_required_when_env_missing(tmp_path: Path) -> None:
    script_path = Path("scripts/report_phase5_numeric_output_parity.py").resolve()

    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=True,
        env=_sanitized_subprocess_env(),
    )

    payload = json.loads(result.stdout)
    assert payload["summary"]["overall_status"] == "CONFIG_REQUIRED"
    assert payload["summary"]["final_reference_proof_complete"] is False
