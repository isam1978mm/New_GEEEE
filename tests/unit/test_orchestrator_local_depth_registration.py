from __future__ import annotations

from app.api.runs import SAFE_STAGE_PROGRESS
from app.config import Settings
from app.pipeline._base import ParityCategory, Stage, StageContext, StageResult
from app.pipeline.orchestrator import Orchestrator
from app.pipeline.stages.depth_estimation import DepthEstimationStage


class _NamedStage(Stage):
    parity_category = ParityCategory.PARITY_REPRODUCES

    def __init__(self, name: str) -> None:
        self.name = name

    async def run(self, context: StageContext) -> StageResult:
        del context
        return StageResult()


def _orchestrator(*, mode: str, stages: list[Stage]) -> Orchestrator:
    settings = Settings(local_depth_mode=mode)
    return Orchestrator(
        settings=settings,
        session_factory=None,  # Not used by registration tests.
        stages=stages,
    )


def test_off_mode_preserves_stage_list_exactly() -> None:
    stages = [_NamedStage("before"), _NamedStage("run_quality"), _NamedStage("after")]

    orchestrator = _orchestrator(mode="off", stages=stages)

    assert orchestrator.stages == stages
    assert [stage.name for stage in orchestrator.stages] == ["before", "run_quality", "after"]


def test_local_calibrated_mode_inserts_depth_after_run_quality() -> None:
    orchestrator = _orchestrator(
        mode="local_calibrated",
        stages=[_NamedStage("before"), _NamedStage("run_quality"), _NamedStage("after")],
    )

    assert [stage.name for stage in orchestrator.stages] == [
        "before",
        "run_quality",
        "depth_estimation",
        "after",
    ]
    assert isinstance(orchestrator.stages[2], DepthEstimationStage)


def test_unknown_mode_does_not_change_stage_list() -> None:
    stages = [_NamedStage("run_quality")]

    orchestrator = _orchestrator(mode="unexpected", stages=stages)

    assert orchestrator.stages == stages


def test_pipeline_without_run_quality_does_not_receive_depth_stage() -> None:
    stages = [_NamedStage("before"), _NamedStage("after")]

    orchestrator = _orchestrator(mode="local_calibrated", stages=stages)

    assert orchestrator.stages == stages


def test_explicit_depth_stage_is_not_duplicated() -> None:
    orchestrator = _orchestrator(
        mode="local_calibrated",
        stages=[_NamedStage("run_quality"), DepthEstimationStage()],
    )

    assert [stage.name for stage in orchestrator.stages].count("depth_estimation") == 1


def test_depth_stage_is_not_added_to_public_progress_list() -> None:
    assert "depth_estimation" not in {name for name, _label in SAFE_STAGE_PROGRESS}
