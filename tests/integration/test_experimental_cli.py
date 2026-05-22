from __future__ import annotations

import asyncio
import csv
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import Settings
from app.db.base import Base
from app.db.models import Artifact, ArtifactClass, Run, RunStatus
from app.pipeline.stages.dem import write_raster_sidecar
from app.pipeline.stages.grid import build_run_grid
from app.pipeline.stages.hypercube import HYPERCUBE_NPY_NAME, HYPERCUBE_TIF_NAME
from app.pipeline.stages.object_extract import CLUSTERS_SUMMARY_NAME, OBJECTS_INDEX_NAME
from app.pipeline.stages.pca_anomaly import PCA_ANOMALY_TIF_NAME
from app.services.storage import initialize_run_storage, write_grid_manifest


def test_experimental_cli_writes_deterministic_filesystem_only_outputs(tmp_path) -> None:
    data_dir = tmp_path / "data"
    db_path = data_dir / "gee_screening.db"
    run_id = "run-1"

    asyncio.run(_seed_completed_run(data_dir=data_dir, db_path=db_path, run_id=run_id))

    env = os.environ.copy()
    env["ENABLE_EXPERIMENTAL"] = "1"
    env["DATA_DIR"] = str(data_dir)
    env["DATABASE_PATH"] = str(db_path)

    result = subprocess.run(
        [sys.executable, "-m", "app.pipeline.stages_experimental.run", "--run-id", run_id],
        cwd=Path.cwd(),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr or result.stdout

    output_dir = data_dir / "runs" / run_id / "experimental"
    classifications_path = output_dir / "classifications.csv"
    summary_path = output_dir / "summary.json"
    neutral_labels_path = output_dir / "neutral_target_labels.json"

    assert classifications_path.is_file()
    assert summary_path.is_file()
    assert neutral_labels_path.is_file()

    rows = list(csv.DictReader(classifications_path.open("r", encoding="utf-8", newline="")))
    assert len(rows) == 2
    assert rows[0]["class_id"].startswith("Class_")
    assert rows[0]["classifier_version"] == "experimental_v1"

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["run_id"] == run_id
    assert summary["object_count"] == 2
    assert summary["cluster_count"] == 1
    neutral_labels = json.loads(neutral_labels_path.read_text(encoding="utf-8"))
    assert len(neutral_labels["object_labels"]) == 2
    assert neutral_labels["object_labels"][0]["class_id"].startswith("Class_")
    assert neutral_labels["cluster_labels"][0]["dominant_class_id"].startswith("Class_")

    artifacts = asyncio.run(_load_experimental_artifacts(data_dir=data_dir, db_path=db_path, run_id=run_id))
    assert set(artifacts) == {"experimental_classifications", "experimental_neutral_labels", "experimental_summary"}
    for artifact in artifacts.values():
        assert artifact["artifact_class"] == ArtifactClass.FILESYSTEM_ONLY.value
        assert artifact["http_servable"] is False
        assert artifact["relative_path"].startswith("experimental/")


async def _seed_completed_run(*, data_dir: Path, db_path: Path, run_id: str) -> None:
    settings = Settings(data_dir=data_dir, database_path=db_path)
    grid_spec = build_run_grid(43.6532, -79.3832)
    run_dir = initialize_run_storage(settings, run_id)
    write_grid_manifest(settings, run_id, grid_spec.manifest)

    hypercube = np.zeros((grid_spec.size, grid_spec.size, 3), dtype=np.float32)
    hypercube[:, :, 0] = 0.44
    hypercube[:, :, 1] = 0.71
    hypercube[:, :, 2] = 1.0
    np.save(run_dir / HYPERCUBE_NPY_NAME, hypercube)
    _write_multiband_tif(run_dir / HYPERCUBE_TIF_NAME, hypercube)
    write_raster_sidecar(
        run_dir / HYPERCUBE_TIF_NAME,
        grid_manifest=grid_spec.manifest,
        nodata=grid_spec.nodata,
        dtype="float32",
        shape=hypercube.shape[:2],
    )

    anomaly = np.zeros((grid_spec.size, grid_spec.size), dtype=np.float32)
    anomaly[32:36, 40:44] = 0.96
    anomaly[48:52, 56:60] = 0.83
    Image.fromarray(anomaly).save(run_dir / PCA_ANOMALY_TIF_NAME, format="TIFF")
    write_raster_sidecar(
        run_dir / PCA_ANOMALY_TIF_NAME,
        grid_manifest=grid_spec.manifest,
        nodata=grid_spec.nodata,
        dtype="float32",
        shape=anomaly.shape,
    )

    _write_csv(
        run_dir / OBJECTS_INDEX_NAME,
        ["object_id", "cluster_id", "row_min", "row_max", "col_min", "col_max", "row_center", "col_center", "area_px", "mean_anomaly", "max_anomaly"],
        [
            {
                "object_id": 1,
                "cluster_id": 0,
                "row_min": 32,
                "row_max": 35,
                "col_min": 40,
                "col_max": 43,
                "row_center": 33.5,
                "col_center": 41.5,
                "area_px": 16,
                "mean_anomaly": 0.96,
                "max_anomaly": 0.96,
            },
            {
                "object_id": 2,
                "cluster_id": 0,
                "row_min": 48,
                "row_max": 51,
                "col_min": 56,
                "col_max": 59,
                "row_center": 49.5,
                "col_center": 57.5,
                "area_px": 16,
                "mean_anomaly": 0.83,
                "max_anomaly": 0.83,
            },
        ],
    )
    _write_csv(
        run_dir / CLUSTERS_SUMMARY_NAME,
        ["cluster_id", "object_count", "total_area_px", "mean_object_area_px", "max_object_anomaly"],
        [{"cluster_id": 0, "object_count": 2, "total_area_px": 32, "mean_object_area_px": 16.0, "max_object_anomaly": 0.96}],
    )

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
        session.add_all(
            [
                Artifact(
                    run_id=run_id,
                    name="hypercube_tif",
                    relative_path=HYPERCUBE_TIF_NAME,
                    size_bytes=(run_dir / HYPERCUBE_TIF_NAME).stat().st_size,
                    sha256=None,
                    artifact_class=ArtifactClass.LOCAL_SENSITIVE,
                    http_servable=False,
                ),
                Artifact(
                    run_id=run_id,
                    name="hypercube_npy",
                    relative_path=HYPERCUBE_NPY_NAME,
                    size_bytes=(run_dir / HYPERCUBE_NPY_NAME).stat().st_size,
                    sha256=None,
                    artifact_class=ArtifactClass.LOCAL_SENSITIVE,
                    http_servable=False,
                ),
                Artifact(
                    run_id=run_id,
                    name="pca_anomaly_tif",
                    relative_path=PCA_ANOMALY_TIF_NAME,
                    size_bytes=(run_dir / PCA_ANOMALY_TIF_NAME).stat().st_size,
                    sha256=None,
                    artifact_class=ArtifactClass.LOCAL_SENSITIVE,
                    http_servable=False,
                ),
                Artifact(
                    run_id=run_id,
                    name="objects_index",
                    relative_path=OBJECTS_INDEX_NAME,
                    size_bytes=(run_dir / OBJECTS_INDEX_NAME).stat().st_size,
                    sha256=None,
                    artifact_class=ArtifactClass.REDACTED_PUBLIC,
                    http_servable=True,
                ),
                Artifact(
                    run_id=run_id,
                    name="clusters_summary",
                    relative_path=CLUSTERS_SUMMARY_NAME,
                    size_bytes=(run_dir / CLUSTERS_SUMMARY_NAME).stat().st_size,
                    sha256=None,
                    artifact_class=ArtifactClass.REDACTED_PUBLIC,
                    http_servable=True,
                ),
            ]
        )
        await session.commit()

    await engine.dispose()


async def _load_experimental_artifacts(
    *,
    data_dir: Path,
    db_path: Path,
    run_id: str,
) -> dict[str, dict[str, object]]:
    settings = Settings(data_dir=data_dir, database_path=db_path)
    engine = create_async_engine(settings.database_url, future=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        rows = list(
            await session.scalars(
                select(Artifact).where(Artifact.run_id == run_id, Artifact.name.like("experimental_%"))
            )
        )
    await engine.dispose()
    return {
        row.name: {
            "relative_path": row.relative_path,
            "artifact_class": row.artifact_class.value,
            "http_servable": row.http_servable,
        }
        for row in rows
    }


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _write_multiband_tif(path: Path, cube_hwc: np.ndarray) -> None:
    pages = [Image.fromarray(cube_hwc[:, :, band_index].astype(np.float32)) for band_index in range(cube_hwc.shape[-1])]
    first, *rest = pages
    first.save(path, format="TIFF", save_all=True, append_images=rest)
