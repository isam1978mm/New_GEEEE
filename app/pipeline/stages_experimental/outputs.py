from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.models import Artifact, ArtifactClass

EXPERIMENTAL_DIRNAME = "experimental"
CLASSIFICATIONS_CSV_NAME = "classifications.csv"
SUMMARY_JSON_NAME = "summary.json"


@dataclass(frozen=True, slots=True)
class ExperimentalOutputPaths:
    output_dir: Path
    classifications_csv: Path
    summary_json: Path


async def write_experimental_outputs(
    *,
    session_factory: async_sessionmaker[AsyncSession],
    run_dir: Path,
    run_id: str,
    classifications: list[dict[str, object]],
    summary: dict[str, object],
) -> ExperimentalOutputPaths:
    output_dir = run_dir / EXPERIMENTAL_DIRNAME
    output_dir.mkdir(parents=True, exist_ok=True)

    classifications_csv = output_dir / CLASSIFICATIONS_CSV_NAME
    summary_json = output_dir / SUMMARY_JSON_NAME

    fieldnames = list(classifications[0].keys()) if classifications else ["object_id", "class_id", "class_score"]
    with classifications_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in classifications:
            writer.writerow(row)

    summary_json.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")

    async with session_factory() as session:
        await _upsert_artifact(
            session,
            run_id=run_id,
            name="experimental_classifications",
            relative_path=classifications_csv.relative_to(run_dir).as_posix(),
            size_bytes=classifications_csv.stat().st_size,
        )
        await _upsert_artifact(
            session,
            run_id=run_id,
            name="experimental_summary",
            relative_path=summary_json.relative_to(run_dir).as_posix(),
            size_bytes=summary_json.stat().st_size,
        )
        await session.commit()

    return ExperimentalOutputPaths(
        output_dir=output_dir,
        classifications_csv=classifications_csv,
        summary_json=summary_json,
    )


async def _upsert_artifact(
    session: AsyncSession,
    *,
    run_id: str,
    name: str,
    relative_path: str,
    size_bytes: int,
) -> None:
    artifact = await session.scalar(select(Artifact).where(Artifact.run_id == run_id, Artifact.name == name))
    if artifact is None:
        artifact = Artifact(
            run_id=run_id,
            name=name,
            relative_path=relative_path,
            size_bytes=size_bytes,
            sha256=None,
            artifact_class=ArtifactClass.FILESYSTEM_ONLY,
            http_servable=False,
        )
        session.add(artifact)
        return

    artifact.relative_path = relative_path
    artifact.size_bytes = size_bytes
    artifact.sha256 = None
    artifact.artifact_class = ArtifactClass.FILESYSTEM_ONLY
    artifact.http_servable = False

