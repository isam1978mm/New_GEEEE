param(
    [switch]$RunTests
)

$ErrorActionPreference = "Stop"

Write-Host "=== Patch run quality inventory tests ==="

$python = @'
from pathlib import Path

path = Path("tests/unit/test_full_job_artifact_inventory.py")
s = path.read_text(encoding="utf-8")

replacements = [
    (
        "from app.pipeline.stages.report_640 import Report640Stage\nfrom app.pipeline.stages.s2_indices import INDEX_NAMES, S2IndicesStage, deterministic_s2_cube_fetcher\n",
        "from app.pipeline.stages.report_640 import Report640Stage\nfrom app.pipeline.stages.run_quality import RunQualityStage\nfrom app.pipeline.stages.s2_indices import INDEX_NAMES, S2IndicesStage, deterministic_s2_cube_fetcher\n",
    ),
    (
        "        classifier_result = asyncio.run(ClassifierStage().run(context))\n        alignment_result = asyncio.run(AlignmentQaStage(grid_spec=grid_spec).run(context))\n",
        "        classifier_result = asyncio.run(ClassifierStage().run(context))\n        alignment_result = asyncio.run(AlignmentQaStage(grid_spec=grid_spec).run(context))\n        run_quality_result = asyncio.run(RunQualityStage().run(context))\n",
    ),
    (
        "        assert _artifact_classes(classifier_result) == {\n            \"experimental_classifications\": ArtifactClass.REDACTED_PUBLIC,\n            \"experimental_summary\": ArtifactClass.REDACTED_PUBLIC,\n            \"experimental_neutral_labels\": ArtifactClass.REDACTED_PUBLIC,\n        }\n        assert _artifact_classes(alignment_result) == {\n",
        "        assert _artifact_classes(classifier_result) == {\n            \"classifier_classifications\": ArtifactClass.REDACTED_PUBLIC,\n            \"classifier_summary\": ArtifactClass.REDACTED_PUBLIC,\n            \"classifier_neutral_labels\": ArtifactClass.REDACTED_PUBLIC,\n            \"experimental_classifications\": ArtifactClass.REDACTED_PUBLIC,\n            \"experimental_summary\": ArtifactClass.REDACTED_PUBLIC,\n            \"experimental_neutral_labels\": ArtifactClass.REDACTED_PUBLIC,\n        }\n        assert _artifact_classes(alignment_result) == {\n",
    ),
    (
        "            \"alignment_summary_redacted\": ArtifactClass.LOCAL_SENSITIVE,\n        }\n\n\ndef test_full_job_run_dir_matches_notebook_compatible_inventory_contract() -> None:\n",
        "            \"alignment_summary_redacted\": ArtifactClass.LOCAL_SENSITIVE,\n        }\n        assert _artifact_classes(run_quality_result) == {\n            \"run_quality_summary\": ArtifactClass.REDACTED_PUBLIC,\n        }\n\n\ndef test_full_job_run_dir_matches_notebook_compatible_inventory_contract() -> None:\n",
    ),
    (
        "        asyncio.run(ClassifierStage().run(context))\n        asyncio.run(AlignmentQaStage(grid_spec=grid_spec).run(context))\n",
        "        asyncio.run(ClassifierStage().run(context))\n        asyncio.run(AlignmentQaStage(grid_spec=grid_spec).run(context))\n        asyncio.run(RunQualityStage().run(context))\n",
    ),
    (
        "            \"objects\",\n            \"experimental\",\n        }\n",
        "            \"objects\",\n            \"classifier\",\n            \"experimental\",\n        }\n",
    ),
    (
        "            \"objects/object_mask.npy\",\n            \"experimental/classifications.csv\",\n            \"experimental/summary.json\",\n            \"experimental/neutral_target_labels.json\",\n        }\n",
        "            \"objects/object_mask.npy\",\n            \"classifier/classifications.csv\",\n            \"classifier/summary.json\",\n            \"classifier/neutral_target_labels.json\",\n            \"experimental/classifications.csv\",\n            \"experimental/summary.json\",\n            \"experimental/neutral_target_labels.json\",\n            \"QA/run_quality/run_quality_summary.json\",\n        }\n",
    ),
]

for old, new in replacements:
    if old not in s:
        raise SystemExit(f"Could not find expected block:\n{old}")
    s = s.replace(old, new, 1)

path.write_text(s, encoding="utf-8")
print("PATCHED tests/unit/test_full_job_artifact_inventory.py")
'@

$python | python -

if ($RunTests) {
    Write-Host "=== Run strict integration and inventory tests ==="
    pytest tests/integration/test_full_run.py tests/integration/test_full_job_artifact_access.py tests/unit/test_full_job_artifact_inventory.py tests/unit/test_run_quality_summary.py tests/unit/test_classifier_stage.py
}
