from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.pipeline.parity.ai_beh_raster_verify_common import (
    ALLOWED_OUTPUT_STATUSES,
    ALLOWED_OVERALL_STATUSES,
    DEFAULT_TRANSFORM_ATOL,
    verify_ai_beh_raster_outputs,
)


AI_BEH_ALLOY_STATUE_VERIFICATION_SCHEMA_VERSION = (
    "ai_beh_alloy_statue_parity_verification_v1"
)
AI_BEH_ALLOY_STATUE_REPORT_RELATIVE_PATH = (
    "manifests/ai_beh_alloy_statue_parity_verification.json"
)
AI_BEH_ALLOY_STATUE_CLASSIFICATION = "notebook-parity semantic raster stage"
AI_BEH_ALLOY_STATUE_FAMILY = "AI_BEH semantic rasters"
AI_BEH_ALLOY_STATUE_OUTPUT_NAME = "AI_BEH_Alloys_Statues_REL_ND_DOM_lin_640.tif"


@dataclass(frozen=True)
class AIBehAlloyStatueVerificationResult:
    report_path: Path
    overall_status: str
    output: dict[str, Any]
    raster_value_comparison_available: bool


def verify_ai_beh_alloy_statue_parity(
    app_output_dir: str | Path,
    notebook_reference_dir: str | Path,
    run_dir: str | Path,
    run_id: str,
    *,
    atol: float = 1e-6,
    rtol: float = 1e-6,
    report_relative_path: str | Path = AI_BEH_ALLOY_STATUE_REPORT_RELATIVE_PATH,
) -> AIBehAlloyStatueVerificationResult:
    """Verify alloy/statue parity against a frozen notebook reference raster."""

    result = verify_ai_beh_raster_outputs(
        app_output_dir=app_output_dir,
        notebook_reference_dir=notebook_reference_dir,
        run_dir=run_dir,
        run_id=run_id,
        output_names=(AI_BEH_ALLOY_STATUE_OUTPUT_NAME,),
        schema_version=AI_BEH_ALLOY_STATUE_VERIFICATION_SCHEMA_VERSION,
        report_relative_path=report_relative_path,
        classification=AI_BEH_ALLOY_STATUE_CLASSIFICATION,
        family=AI_BEH_ALLOY_STATUE_FAMILY,
        missing_app_note="App alloy/statue output is missing.",
        missing_reference_note="Frozen notebook alloy/statue reference is missing.",
        atol=atol,
        rtol=rtol,
    )
    return AIBehAlloyStatueVerificationResult(
        report_path=result.report_path,
        overall_status=result.overall_status,
        output=result.outputs[0],
        raster_value_comparison_available=result.raster_value_comparison_available,
    )
