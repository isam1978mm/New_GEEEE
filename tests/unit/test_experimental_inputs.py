from __future__ import annotations

import csv
import importlib
import json
import sys
from pathlib import Path

import numpy as np
import pytest
from PIL import Image
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

from app.config import Settings
from app.db.base import Base
from app.db.models import Artifact, ArtifactClass, Run, RunStatus
from app.pipeline.stages.dem import write_raster_sidecar
from app.pipeline.stages.grid import build_run_grid
from app.pipeline.stages.hypercube import HYPERCUBE_NPY_NAME, HYPERCUBE_TIF_NAME
from app.pipeline.stages.object_extract import CLUSTERS_SUMMARY_NAME, OBJECTS_INDEX_NAME
from app.pipeline.stages.pca_anomaly import PCA_ANOMALY_TIF_NAME
from app.services.storage import initialize_run_storage, write_grid_manifest

PACKAGE_NAME = "app.pipeline.stages_experimental"


@pytest.mark.asyncio
async def test_validate_experimental_inputs_accepts_completed_grid_consistent_run(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ENABLE_EXPERIMENTAL", "1")
    inputs_module = _load_inputs_module()
    settings, session_factory, run_id, engine = await _build_completed_run_fixture(tmp_path)
    try:
        validated = await inputs_module.validate_experimental_inputs(
            settings=settings,
            session_factory=session_factory,
            run_id=run_id,
        )

        assert validated.run_id == run_id
        assert validated.hypercube_npy_path.name == HYPERCUBE_NPY_NAME
        assert validated.pca_anomaly_tif_path.name == PCA_ANOMALY_TIF_NAME
        assert len(validated.object_rows) == 2
        assert len(validated.cluster_rows) == 1
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_validate_experimental_inputs_rejects_non_done_run(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ENABLE_EXPERIMENTAL", "1")
    inputs_module = _load_inputs_module()
    settings, session_factory, run_id, engine = await _build_completed_run_fixture(tmp_path, status=RunStatus.RUNNING)
    try:
        with pytest.raises(Exception, match="run is not done"):
            await inputs_module.validate_experimental_inputs(
                settings=settings,
                session_factory=session_factory,
                run_id=run_id,
            )
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_validate_experimental_inputs_rejects_transform_drift_before_classifier_runs(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ENABLE_EXPERIMENTAL", "1")
    inputs_module = _load_inputs_module()
    settings, session_factory, run_id, engine = await _build_completed_run_fixture(tmp_path, drift_transform=True)
    try:
        with pytest.raises(Exception, match="transform mismatch"):
            await inputs_module.validate_experimental_inputs(
                settings=settings,
                session_factory=session_factory,
                run_id=run_id,
            )
    finally:
        await engine.dispose()


def _load_inputs_module():
    _clear_experimental_modules()
    importlib.import_module(PACKAGE_NAME)
    return importlib.import_module(f"{PACKAGE_NAME}.inputs")


async def _build_completed_run_fixture(
    tmp_path: Path,
    *,
    status: RunStatus = RunStatus.DONE,
    drift_transform: bool = False,
) -> tuple[Settings, async_sessionmaker, str, AsyncEngine]:
    data_dir = tmp_path / "data"
    settings = Settings(data_dir=data_dir, database_path=data_dir / "gee_screening.db")
    run_id = "run-1"
    grid_spec = build_run_grid(43.6532, -79.3832)
    run_dir = initialize_run_storage(settings, run_id)
    write_grid_manifest(settings, run_id, grid_spec.manifest)

    hypercube = np.zeros((grid_spec.size, grid_spec.size, 3), dtype=np.float32)
    hypercube[:, :, 0] = 0.35
    hypercube[:, :, 1] = 0.65
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
    anomaly[10:14, 12:16] = 0.92
    anomaly[20:24, 22:26] = 0.78
    Image.fromarray(anomaly).save(run_dir / PCA_ANOMALY_TIF_NAME, format="TIFF")
    manifest = grid_spec.manifest.model_copy(deep=True)
    if drift_transform:
        manifest.crs_transform[2] = float(manifest.crs_transform[2]) + float(manifest.scale_m)
    write_raster_sidecar(
        run_dir / PCA_ANOMALY_TIF_NAME,
        grid_manifest=manifest,
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
                "row_min": 10,
                "row_max": 13,
                "col_min": 12,
                "col_max": 15,
                "row_center": 11.5,
                "col_center": 13.5,
                "area_px": 16,
                "mean_anomaly": 0.92,
                "max_anomaly": 0.92,
            },
            {
                "object_id": 2,
                "cluster_id": 0,
                "row_min": 20,
                "row_max": 23,
                "col_min": 22,
                "col_max": 25,
                "row_center": 21.5,
                "col_center": 23.5,
                "area_px": 16,
                "mean_anomaly": 0.78,
                "max_anomaly": 0.78,
            },
        ],
    )
    _write_csv(
        run_dir / CLUSTERS_SUMMARY_NAME,
        ["cluster_id", "object_count", "total_area_px", "mean_object_area_px", "max_object_anomaly"],
        [{"cluster_id": 0, "object_count": 2, "total_area_px": 32, "mean_object_area_px": 16.0, "max_object_anomaly": 0.92}],
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
                status=status,
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

    return settings, session_factory, run_id, engine


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


def _clear_experimental_modules() -> None:
    for name in list(sys.modules):
        if name == PACKAGE_NAME or name.startswith(f"{PACKAGE_NAME}."):
            sys.modules.pop(name, None)
