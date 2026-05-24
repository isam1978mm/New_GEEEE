from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.runs import run_core_pipeline_for_run
from app.config import Settings
from app.db.base import Base
from app.db.models import Run, RunStatus
from app.pipeline.manifest import save_grid_manifest
from app.pipeline.stages.grid import grid_spec_from_notebook_radar_meta
from app.services.storage import initialize_run_storage


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run a local-only app validation pipeline using the exact GRID from notebook QA_RADAR_META*.json. "
            "This command does not add any public API field and does not print GRID coordinates or transforms."
        )
    )
    parser.add_argument("--notebook-radar-meta", type=Path, required=True, help="Local QA_RADAR_META*.json file.")
    parser.add_argument("--lat", type=float, required=True, help="Internal run latitude; not used to build GRID.")
    parser.add_argument("--lon", type=float, required=True, help="Internal run longitude; not used to build GRID.")
    parser.add_argument("--name", type=str, default="notebook-grid-validation", help="Internal run name.")
    parser.add_argument("--run-id", type=str, default=None, help="Optional run id. Defaults to generated UUID.")
    parser.add_argument("--data-dir", type=Path, default=Path("./data"), help="App data directory.")
    parser.add_argument(
        "--database-path",
        type=Path,
        default=None,
        help="SQLite database path. Defaults to <data-dir>/gee_screening.db.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    database_path = args.database_path or (args.data_dir / "gee_screening.db")
    settings = Settings(data_dir=args.data_dir, database_path=database_path)
    grid_spec = grid_spec_from_notebook_radar_meta(args.notebook_radar_meta)
    run_id = asyncio.run(
        _create_validation_run(
            settings=settings,
            run_id=args.run_id,
            name=args.name,
            lat=args.lat,
            lon=args.lon,
            grid_spec=grid_spec,
        )
    )
    asyncio.run(run_core_pipeline_for_run(run_id=run_id, settings=settings, grid_spec_override=grid_spec))
    print(f"Validation run completed: {run_id}")
    print("GRID override source: notebook QA_RADAR_META")
    return 0


async def _create_validation_run(
    *,
    settings: Settings,
    run_id: str | None,
    name: str,
    lat: float,
    lon: float,
    grid_spec,
) -> str:
    engine = create_async_engine(settings.database_url, future=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        async with session_factory() as session:
            run_kwargs = {
                "name": name,
                "status": RunStatus.QUEUED,
                "latitude": lat,
                "longitude": lon,
            }
            if run_id is not None:
                run_kwargs["id"] = run_id
            run = Run(**run_kwargs)
            session.add(run)
            await session.flush()
            initialize_run_storage(settings, run.id)
            save_grid_manifest(settings, run.id, grid_spec.manifest)
            await session.commit()
            return str(run.id)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
