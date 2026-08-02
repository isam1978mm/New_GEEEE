from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any

from sqlalchemy.ext.asyncio import async_sessionmaker

from app.config import Settings, get_settings
from app.db.session import create_engine, create_session_factory
from app.pipeline._base import Stage
from app.pipeline.orchestrator import Orchestrator
from app.pipeline.stages.surface_change import SUMMARY_FILENAME, SurfaceChangeStage
from app.services.storage import get_run_dir


async def run_surface_change_for_existing_run(
    *,
    run_id: str,
    settings: Settings,
    force: bool = False,
    stage: Stage | None = None,
    session_factory: async_sessionmaker | None = None,
) -> dict[str, Any]:
    """Run only the Option 5 surface-change stage for a completed app run.

    The existing run status is preserved. The stage result is registered in the
    artifact database so the normal app results panel can read the public summary.
    """

    using_real_stage = stage is None
    stage = stage or SurfaceChangeStage()

    if using_real_stage and not settings.ee_real_execution_enabled:
        raise RuntimeError("EE_REAL_EXECUTION_ENABLED must be true for surface-change backfill.")
    if using_real_stage and not settings.option5_surface_change_enabled:
        raise RuntimeError("OPTION5_SURFACE_CHANGE_ENABLED must be true for surface-change backfill.")

    engine = None
    if session_factory is None:
        engine = create_engine(settings)
        session_factory = create_session_factory(settings, engine)

    try:
        orchestrator = Orchestrator(
            settings=settings,
            session_factory=session_factory,
            stages=[],
        )
        record = await orchestrator.run_stage_for_existing_run(
            run_id,
            stage,
            force=force,
        )

        summary_path = get_run_dir(settings, run_id) / SUMMARY_FILENAME
        summary_payload: dict[str, Any] = {}
        if summary_path.is_file():
            raw_payload = json.loads(summary_path.read_text(encoding="utf-8"))
            if isinstance(raw_payload, dict):
                summary_payload = raw_payload

        return {
            "run_id": run_id,
            "stage": record.stage_name,
            "stage_status": record.status,
            "artifact_count": record.artifact_count,
            "surface_change_status": summary_payload.get("status", "not_available"),
            "reason": summary_payload.get("reason"),
            "summary_artifact": "option5_surface_change_summary",
            "summary_filename": SUMMARY_FILENAME,
            "run_status_preserved": True,
            "warnings": summary_payload.get(
                "warnings",
                [
                    "radar_backscatter_change_only",
                    "not_depth",
                    "not_settlement",
                    "not_displacement",
                ],
            ),
        }
    finally:
        if engine is not None:
            await engine.dispose()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run the guarded Option 5 dual-window radar surface-change stage "
            "for an existing completed app run."
        ),
    )
    parser.add_argument("--run-id", required=True)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Rerun the stage when a surface-change stage manifest already exists.",
    )
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    settings = get_settings()
    try:
        result = asyncio.run(
            run_surface_change_for_existing_run(
                run_id=args.run_id,
                settings=settings,
                force=args.force,
            )
        )
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        print(
            json.dumps(
                {
                    "status": "failed",
                    "reason": str(exc),
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 1
    except Exception:
        print(
            json.dumps(
                {
                    "status": "failed",
                    "reason": "surface_change_backfill_failed",
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 1

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
