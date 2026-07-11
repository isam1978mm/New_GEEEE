param(
    [switch]$RunTests
)

$ErrorActionPreference = "Stop"

Write-Host "=== Patch S2 mask support GeoTIFF georef ==="

$python = @'
from pathlib import Path

path = Path("app/pipeline/stages/feature_stacks.py")
s = path.read_text(encoding="utf-8")

old = '    Image.fromarray(s2_mask.astype(np.float32)).save(s2_mask_path, format="TIFF")\n'
new = '    write_georeferenced_raster(s2_mask_path, s2_mask.astype(np.float32, copy=False), grid_spec)\n'

if old not in s:
    raise SystemExit("Could not find PIL save for s2_mask_support_valid.tif")

s = s.replace(old, new, 1)
path.write_text(s, encoding="utf-8")
print("PATCHED app/pipeline/stages/feature_stacks.py")
'@

$python | python -

if ($RunTests) {
    Write-Host "=== Run strict integration and inventory tests ==="
    pytest tests/integration/test_full_run.py tests/integration/test_full_job_artifact_access.py tests/unit/test_full_job_artifact_inventory.py tests/unit/test_run_quality_summary.py tests/unit/test_classifier_stage.py
}
