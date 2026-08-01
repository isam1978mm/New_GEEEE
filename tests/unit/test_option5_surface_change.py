from __future__ import annotations

import numpy as np

from app.config import Settings
from app.pipeline._base import ParityCategory, Stage, StageContext, StageResult
from app.pipeline.orchestrator import Orchestrator
from app.pipeline.stages.surface_change import compute_surface_change_review


class StubStage(Stage):
    parity_category = ParityCategory.PARITY_REPRODUCES

    def __init__(self, name: str) -> None:
        self.name = name

    async def run(self, context: StageContext) -> StageResult:
        del context
        return StageResult()


def test_surface_change_flags_only_large_relative_radar_differences() -> None:
    shape = (64, 64)
    before = np.zeros(shape, dtype=np.float32)
    after = np.zeros(shape, dtype=np.float32)
    after[20:30, 20:30] = 2.0
    incidence = np.full(shape, 38.0, dtype=np.float32)

    summary, indicator, delta = compute_surface_change_review(
        before_logratio_db=before,
        after_logratio_db=after,
        before_incidence=incidence,
        after_incidence=incidence,
        nodata=-9999.0,
        min_valid_pixels=100,
    )

    assert summary["status"] == "available"
    assert summary["change_review_pixel_count"] == 100
    assert summary["review_threshold_db"] >= 1.0
    assert float(indicator[25, 25]) >= 1.0
    assert float(indicator[0, 0]) < 1.0
    assert float(delta[25, 25]) == 2.0


def test_surface_change_abstains_when_incidence_compatible_support_is_too_small() -> None:
    shape = (32, 32)
    before = np.zeros(shape, dtype=np.float32)
    after = np.ones(shape, dtype=np.float32)
    before_incidence = np.full(shape, 35.0, dtype=np.float32)
    after_incidence = np.full(shape, 40.0, dtype=np.float32)

    summary, indicator, delta = compute_surface_change_review(
        before_logratio_db=before,
        after_logratio_db=after,
        before_incidence=before_incidence,
        after_incidence=after_incidence,
        nodata=-9999.0,
        min_valid_pixels=100,
    )

    assert summary["status"] == "not_available"
    assert summary["reason"] == "insufficient_compatible_pixels"
    assert np.all(indicator == -9999.0)
    assert np.all(delta == -9999.0)


def test_surface_change_stage_is_inserted_only_for_real_enabled_runs() -> None:
    stages = [StubStage("grid"), StubStage("sar_rtc"), StubStage("s2_indices")]

    disabled = Orchestrator(
        settings=Settings(ee_real_execution_enabled=False, option5_surface_change_enabled=True),
        session_factory=None,  # type: ignore[arg-type]
        stages=stages,
    )
    assert [stage.name for stage in disabled.stages] == ["grid", "sar_rtc", "s2_indices"]

    enabled = Orchestrator(
        settings=Settings(ee_real_execution_enabled=True, option5_surface_change_enabled=True),
        session_factory=None,  # type: ignore[arg-type]
        stages=stages,
    )
    assert [stage.name for stage in enabled.stages] == [
        "grid",
        "sar_rtc",
        "surface_change",
        "s2_indices",
    ]


def test_surface_change_stage_does_not_duplicate_existing_registration() -> None:
    stages = [StubStage("sar_rtc"), StubStage("surface_change"), StubStage("s2_indices")]
    orchestrator = Orchestrator(
        settings=Settings(ee_real_execution_enabled=True, option5_surface_change_enabled=True),
        session_factory=None,  # type: ignore[arg-type]
        stages=stages,
    )

    assert [stage.name for stage in orchestrator.stages].count("surface_change") == 1
