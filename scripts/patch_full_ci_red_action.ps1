param(
    [switch]$RunTests
)

$ErrorActionPreference = "Stop"

Write-Host "=== Patch full CI red action failures ==="

@'
from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    p = Path(path)
    s = p.read_text(encoding="utf-8")
    if old not in s:
        raise SystemExit(f"Could not find expected block in {path}")
    p.write_text(s.replace(old, new, 1), encoding="utf-8")
    print("PATCHED", path)

# 1) Startup stale cleanup: only RUNNING should be stale-failed on startup. QUEUED remains active.
replace_once(
    "app/services/run_state.py",
    '''ACTIVE_RUN_STATUSES = (RunStatus.QUEUED, RunStatus.RUNNING)


async def mark_stale_running_runs(session: AsyncSession) -> int:
    try:
        result = await session.execute(select(Run).where(Run.status.in_(ACTIVE_RUN_STATUSES)))
''',
    '''ACTIVE_RUN_STATUSES = (RunStatus.QUEUED, RunStatus.RUNNING)
STALE_ON_STARTUP_STATUSES = (RunStatus.RUNNING,)


async def mark_stale_running_runs(session: AsyncSession) -> int:
    try:
        result = await session.execute(select(Run).where(Run.status.in_(STALE_ON_STARTUP_STATUSES)))
''',
)

# 2) Restore public-safe run-name validation. Reject coordinate-like and path-like names without echoing them.
replace_once(
    "app/schemas/run.py",
    '''from datetime import datetime

from pydantic import BaseModel, Field, field_validator
''',
    '''from datetime import datetime
import re

from pydantic import BaseModel, Field, field_validator
''',
)
replace_once(
    "app/schemas/run.py",
    '''    @field_validator("name")
    @classmethod
    def validate_private_local_name(cls, value: str | None) -> str | None:
        return value
''',
    '''    @field_validator("name")
    @classmethod
    def validate_private_local_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        if not stripped:
            return None
        if re.search(r"\\b-?\\d{1,2}\\.\\d+\\s*,\\s*-?\\d{1,3}\\.\\d+\\b", stripped):
            raise ValueError("invalid run name")
        if re.search(r"(?i)([A-Z]:\\\\|/Users/|/home/|/tmp/|\\.\\.|[/\\\\])", stripped):
            raise ValueError("invalid run name")
        return stripped
''',
)

# 3) Operator output tree must use the explicit allowlist patterns, not every safe-looking path.
replace_once(
    "app/services/operator_outputs.py",
    '''def is_operator_visible_relative_path(relative_path: str) -> bool:
    normalized = relative_path.replace("\\\\", "/")
    return is_safe_operator_output_relative_path(normalized)
''',
    '''def is_operator_visible_relative_path(relative_path: str) -> bool:
    normalized = relative_path.replace("\\\\", "/")
    if not is_safe_operator_output_relative_path(normalized):
        return False
    return any(fnmatchcase(normalized, pattern) for pattern in OPERATOR_VISIBLE_PATTERNS)
''',
)

# 4) Alignment tests now need real georeferenced TIFF fixtures, because real TIFF metadata is authoritative.
replace_once(
    "tests/unit/test_alignment_qa.py",
    '''from app.pipeline.stages.dem import write_raster_sidecar
''',
    '''from app.pipeline.stages.dem import write_georeferenced_raster, write_raster_sidecar
''',
)
replace_once(
    "tests/unit/test_alignment_qa.py",
    '''    Image.fromarray(array.astype(np.float32)).save(path, format="TIFF")
    write_raster_sidecar(
''',
    '''    write_georeferenced_raster(path, array.astype(np.float32, copy=False), grid_spec)
    write_raster_sidecar(
''',
)
replace_once(
    "tests/notebook_parity/test_alignment_parity.py",
    '''from app.pipeline.stages.dem import write_raster_sidecar
''',
    '''from app.pipeline.stages.dem import write_georeferenced_raster, write_raster_sidecar
''',
)
replace_once(
    "tests/notebook_parity/test_alignment_parity.py",
    '''    Image.fromarray(array.astype(np.float32)).save(path, format="TIFF")
    write_raster_sidecar(
''',
    '''    write_georeferenced_raster(path, array.astype(np.float32, copy=False), grid_spec)
    write_raster_sidecar(
''',
)

# 5) Stale classifier wording expectation after promoting classifier to core.
replace_once(
    "tests/unit/test_experimental_gate.py",
    '''    assert stage.parity_reason == "Runs the previously isolated neutral classifier as a normal pipeline stage."
''',
    '''    assert stage.parity_reason == "Runs the core neutral classifier as a normal pipeline stage."
''',
)

# 6) Alignment schema now includes metadata_source because QA reads real GeoTIFF metadata.
replace_once(
    "tests/unit/test_notebook_output_metadata_contract.py",
    '''        assert set(alignment_summary) == {"pass", "checked_raster_count", "failing_artifacts", "max_center_offset_px", "threshold_px"}
''',
    '''        assert set(alignment_summary) == {"pass", "checked_raster_count", "failing_artifacts", "max_center_offset_px", "metadata_source", "threshold_px"}
''',
)
replace_once(
    "tests/unit/test_notebook_output_metadata_contract.py",
    '''            "passes_alignment",
        }
''',
    '''            "passes_alignment",
            "metadata_source",
        }
''',
)

# 7) Hypercube parity now preserves invalid values as NaN internally and persists nodata only for disk output.
replace_once(
    "tests/notebook_parity/test_hypercube_parity.py",
    '''    assert cube_clean[0, 1, 0] == 0.0
    assert cube_norm.shape == (2, 2, 2)
    assert cube_norm_plus_mask.shape == (2, 2, 3)
    assert np.all(cube_norm_plus_mask[:, :, -1] == mask_any.astype(np.float32))
    assert np.allclose(cube_raw, cube_norm_plus_mask)
''',
    '''    assert np.isnan(cube_clean[0, 1, 0])
    assert cube_norm.shape == (2, 2, 2)
    assert cube_norm_plus_mask.shape == (2, 2, 3)
    assert np.all(cube_norm_plus_mask[:, :, -1] == mask_all.astype(np.float32))
    expected_persisted = np.where(np.isfinite(cube_norm_plus_mask), cube_norm_plus_mask, -9999.0).astype(np.float32)
    assert np.allclose(cube_raw, expected_persisted)
''',
)

# 8) Thermal parity now samples LST, raw ST_B10, and L9 raw ST_B10 per four tiles.
replace_once(
    "tests/notebook_parity/test_thermal_parity.py",
    '''    assert len([name for name, _value in calls if name == "sampleRectangle"]) == 8
''',
    '''    assert len([name for name, _value in calls if name == "sampleRectangle"]) == 12
''',
)

# 9) Frontend copy changed; keep static test source-backed but avoid stale exact sentence.
replace_once(
    "tests/integration/test_frontend_static.py",
    '''    assert "Guarded exports appear only after a run produces public-safe deliverables." in bundle_text
''',
    '''    assert "exports may appear after completion" in bundle_text
''',
)

print("FULL_CI_PATCH_COMPLETE")
'@ | python -

if ($RunTests) {
    Write-Host "=== Run affected CI failure set ==="
    pytest `
        tests/unit/test_alignment_qa.py `
        tests/notebook_parity/test_alignment_parity.py `
        tests/notebook_parity/test_hypercube_parity.py `
        tests/notebook_parity/test_thermal_parity.py `
        tests/unit/test_experimental_gate.py `
        tests/unit/test_notebook_output_metadata_contract.py `
        tests/integration/test_artifact_serving.py `
        tests/integration/test_public_api_safety.py `
        tests/integration/test_run_roi_contract.py `
        tests/integration/test_runs_api.py `
        tests/integration/test_startup_stale_run_cleanup.py `
        tests/integration/test_frontend_static.py
}
