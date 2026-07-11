param(
    [switch]$RunTests
)

$ErrorActionPreference = "Stop"
Set-Location -Path (Resolve-Path "$PSScriptRoot\..")

@'
from pathlib import Path

p = Path("app/api/runs.py")
s = p.read_text(encoding="utf-8")

import_anchor = "from app.pipeline.stages.report_640 import (\n"
import_line = "from app.pipeline.stages.run_quality import RunQualityStage\n"
if import_line not in s:
    if import_anchor not in s:
        raise SystemExit("Could not find report_640 import anchor")
    s = s.replace(import_anchor, import_line + import_anchor, 1)

progress_anchor = '    ("alignment_qa", "Alignment QA"),\n'
progress_line = '    ("run_quality", "Run quality"),\n'
if progress_line not in s:
    if progress_anchor not in s:
        raise SystemExit("Could not find alignment QA progress anchor")
    s = s.replace(progress_anchor, progress_anchor + progress_line, 1)

stage_anchor = "                    AlignmentQaStage(grid_spec=grid_spec),\n"
stage_line = "                    RunQualityStage(),\n"
if stage_line not in s:
    if stage_anchor not in s:
        raise SystemExit("Could not find AlignmentQaStage stage anchor")
    s = s.replace(stage_anchor, stage_anchor + stage_line, 1)

p.write_text(s, encoding="utf-8")
print("PATCHED app/api/runs.py with RunQualityStage wiring")
'@ | python -

if ($RunTests) {
    pytest tests/unit/test_run_quality_summary.py tests/unit/test_zero_shift.py tests/unit/test_alignment_qa_real_geotiff_metadata.py
}
