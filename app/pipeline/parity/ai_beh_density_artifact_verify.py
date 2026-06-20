from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.pipeline.parity.ai_beh_raster_verify_common import verify_ai_beh_raster_outputs


AI_BEH_DENSITY_ARTIFACT_VERIFICATION_SCHEMA_VERSION = (
    "ai_beh_density_artifact_parity_verification_v1"
)
AI_BEH_DENSITY_ARTIFACT_REPORT_RELATIVE_PATH = (
    "manifests/ai_beh_density_artifact_parity_verification.json"
)
AI_BEH_DENSITY_ARTIFACT_CLASSIFICATION = "notebook-parity semantic raster stage"
AI_BEH_DENSITY_ARTIFACT_FAMILY = "AI_BEH semantic rasters"
AI_BEH_DENSITY_ARTIFACT_OUTPUT_NAMES = (
    "AI_BEH_Gold_Pure_Density_19_3_DOM_lin_640.tif",
    "AI_BEH_Artifacts_Jars_Chests_DOM_lin_640.tif",
)


@dataclass(frozen=True)
class AIBehDensityArtifactVerificationResult:
    report_path: Path
    overall_status: str
    outputs: tuple[dict[str, Any], ...]
    raster_value_comparison_available: bool


def verify_ai_beh_density_artifact_parity(
    app_output_dir: str | Path,
    notebook_reference_dir: str | Path,
    run_dir: str | Path,
    run_id: str,
    *,
    atol: float = 1e-6,
    rtol: float = 1e-6,
    report_relative_path: str | Path = AI_BEH_DENSITY_ARTIFACT_REPORT_RELATIVE_PATH,
) -> AIBehDensityArtifactVerificationResult:
    """Verify AI_BEH density/artifact parity against frozen notebook reference rasters."""

    result = verify_ai_beh_raster_outputs(
        app_output_dir=app_output_dir,
        notebook_reference_dir=notebook_reference_dir,
        run_dir=run_dir,
        run_id=run_id,
        output_names=AI_BEH_DENSITY_ARTIFACT_OUTPUT_NAMES,
        schema_version=AI_BEH_DENSITY_ARTIFACT_VERIFICATION_SCHEMA_VERSION,
        report_relative_path=report_relative_path,
        classification=AI_BEH_DENSITY_ARTIFACT_CLASSIFICATION,
        family=AI_BEH_DENSITY_ARTIFACT_FAMILY,
        missing_app_note="App AI_BEH density/artifact output is missing.",
        missing_reference_note="Frozen notebook AI_BEH density/artifact reference is missing.",
        atol=atol,
        rtol=rtol,
    )
    return AIBehDensityArtifactVerificationResult(
        report_path=result.report_path,
        overall_status=result.overall_status,
        outputs=result.outputs,
        raster_value_comparison_available=result.raster_value_comparison_available,
    )
