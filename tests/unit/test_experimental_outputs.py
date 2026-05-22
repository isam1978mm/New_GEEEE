from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import Settings
from app.db.base import Base
from app.db.models import Artifact, ArtifactClass, Run, RunStatus
from app.services.storage import initialize_run_storage

PACKAGE_NAME = "app.pipeline.stages_experimental"


@pytest.mark.asyncio
async def test_write_experimental_outputs_stays_under_run_experimental_and_marks_filesystem_only(
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("ENABLE_EXPERIMENTAL", "1")
    outputs_module = _load_outputs_module()

    data_dir = tmp_path / "data"
    settings = Settings(data_dir=data_dir, database_path=data_dir / "gee_screening.db")
    run_id = "run-1"
    run_dir = initialize_run_storage(settings, run_id)

    engine = create_async_engine(settings.database_url, future=True)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as session:
        session.add(
            Run(
                id=run_id,
                name="fixture",
                status=RunStatus.DONE,
                latitude=43.6532,
                longitude=-79.3832,
            )
        )
        await session.commit()

    output_paths = await outputs_module.write_experimental_outputs(
        session_factory=session_factory,
        run_dir=run_dir,
        run_id=run_id,
        classifications=[
            {
                "object_id": 1,
                "cluster_id": 0,
                "row_min": 10,
                "row_max": 13,
                "col_min": 12,
                "col_max": 15,
                "class_id": "Class_A",
                "class_score": 0.91,
                "class_family": "family_01",
                "classifier_version": "experimental_v1",
            }
        ],
        summary={"run_id": run_id, "object_count": 1, "cluster_count": 1, "class_counts": {"Class_A": 1}},
    )

    assert output_paths.output_dir == run_dir / "experimental"
    assert output_paths.classifications_csv.is_file()
    assert output_paths.summary_json.is_file()
    assert output_paths.neutral_labels_json.is_file()
    assert output_paths.classifications_csv.relative_to(run_dir).as_posix().startswith("experimental/")
    assert output_paths.summary_json.relative_to(run_dir).as_posix().startswith("experimental/")
    assert output_paths.neutral_labels_json.relative_to(run_dir).as_posix().startswith("experimental/")

    summary_payload = json.loads(output_paths.summary_json.read_text(encoding="utf-8"))
    assert summary_payload["class_counts"] == {"Class_A": 1}
    labels_payload = json.loads(output_paths.neutral_labels_json.read_text(encoding="utf-8"))
    assert labels_payload["object_labels"][0]["class_id"] == "Class_A"
    assert labels_payload["cluster_labels"][0]["dominant_class_id"] == "Class_A"

    async with session_factory() as session:
        artifacts = list(
            await session.scalars(
                select(Artifact).where(Artifact.run_id == run_id).order_by(Artifact.name.asc())
            )
        )

    indexed = {artifact.name: artifact for artifact in artifacts if artifact.name.startswith("experimental_")}
    assert set(indexed) == {"experimental_classifications", "experimental_neutral_labels", "experimental_summary"}
    for artifact in indexed.values():
        assert artifact.artifact_class == ArtifactClass.FILESYSTEM_ONLY
        assert artifact.http_servable is False
        assert artifact.relative_path.startswith("experimental/")

    await engine.dispose()


def _load_outputs_module():
    _clear_experimental_modules()
    importlib.import_module(PACKAGE_NAME)
    return importlib.import_module(f"{PACKAGE_NAME}.outputs")


def _clear_experimental_modules() -> None:
    for name in list(sys.modules):
        if name == PACKAGE_NAME or name.startswith(f"{PACKAGE_NAME}."):
            sys.modules.pop(name, None)
