from __future__ import annotations

import csv
import os
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.config import Settings
from app.db.models import Artifact, ArtifactClass, Run, RunStatus
from app.errors import GridDriftError, StageError
from app.pipeline.stages.dem import raster_sidecar_path
from app.pipeline.stages.grid import GridSpec, grid_spec_from_manifest
from app.pipeline.stages.hypercube import HYPERCUBE_NPY_NAME, HYPERCUBE_TIF_NAME
from app.pipeline.stages.object_extract import CLUSTERS_SUMMARY_NAME, OBJECTS_INDEX_NAME
from app.pipeline.stages.pca_anomaly import PCA_ANOMALY_TIF_NAME
from app.services.grid import GridManifest
from app.services.storage import get_run_dir, read_manifest, resolve_run_artifact_path

GRID_MANIFEST_NAME = "grid_manifest.json"
REQUIRED_ARTIFACT_CLASSES: dict[str, tuple[ArtifactClass, ...]] = {
    "hypercube_tif": (ArtifactClass.LOCAL_SENSITIVE,),
    "hypercube_npy": (ArtifactClass.LOCAL_SENSITIVE,),
    "pca_anomaly_tif": (ArtifactClass.LOCAL_SENSITIVE,),
    "objects_index": (ArtifactClass.REDACTED_PUBLIC,),
    "clusters_summary": (ArtifactClass.REDACTED_PUBLIC,),
}


@dataclass(frozen=True, slots=True)
class ExperimentalInputs:
    run_id: str
    run_dir: Path
    grid_spec: GridSpec
    hypercube_npy_path: Path
    pca_anomaly_tif_path: Path
    objects_index_path: Path
    clusters_summary_path: Path
    object_rows: list[dict[str, str]]
    cluster_rows: list[dict[str, str]]


async def validate_experimental_inputs(
    *,
    settings: Settings,
    session_factory: async_sessionmaker[AsyncSession],
    run_id: str,
) -> ExperimentalInputs:
    if os.getenv("ENABLE_EXPERIMENTAL") != "1":
        raise StageError("Experimental module not enabled.")

    async with session_factory() as session:
        run = await session.scalar(select(Run).where(Run.id == run_id))
        if run is None:
            raise StageError("Experimental run validation failed: run was not found.")
        if run.status != RunStatus.DONE:
            raise StageError("Experimental run validation failed: run is not done.")

        artifact_map = await _load_required_artifacts(session, run_id)

    run_dir = get_run_dir(settings, run_id)
    if not run_dir.is_dir():
        raise StageError("Experimental run validation failed: run directory is missing.")

    grid_manifest_path = run_dir / GRID_MANIFEST_NAME
    if not grid_manifest_path.is_file():
        raise StageError("Experimental run validation failed: grid manifest is missing.")

    grid_manifest = GridManifest.model_validate(read_manifest(grid_manifest_path))
    grid_spec = grid_spec_from_manifest(grid_manifest)

    hypercube_tif_path = resolve_run_artifact_path(settings, run_id, artifact_map["hypercube_tif"].relative_path)
    hypercube_npy_path = resolve_run_artifact_path(settings, run_id, artifact_map["hypercube_npy"].relative_path)
    pca_anomaly_tif_path = resolve_run_artifact_path(settings, run_id, artifact_map["pca_anomaly_tif"].relative_path)
    objects_index_path = resolve_run_artifact_path(settings, run_id, artifact_map["objects_index"].relative_path)
    clusters_summary_path = resolve_run_artifact_path(settings, run_id, artifact_map["clusters_summary"].relative_path)

    _require_file(hypercube_tif_path, "hypercube_tif")
    _require_file(hypercube_npy_path, "hypercube_npy")
    _require_file(pca_anomaly_tif_path, "pca_anomaly_tif")
    _require_file(objects_index_path, "objects_index")
    _require_file(clusters_summary_path, "clusters_summary")

    _validate_raster_grid(hypercube_tif_path, grid_spec)
    _validate_raster_grid(pca_anomaly_tif_path, grid_spec)
    _validate_hypercube_shape(hypercube_npy_path, grid_spec)
    _validate_anomaly_shape(pca_anomaly_tif_path, grid_spec)

    object_rows = _read_csv_rows(objects_index_path)
    cluster_rows = _read_csv_rows(clusters_summary_path)
    if not object_rows:
        raise StageError("Experimental run validation failed: objects index is empty.")
    if not cluster_rows:
        raise StageError("Experimental run validation failed: clusters summary is empty.")

    return ExperimentalInputs(
        run_id=run_id,
        run_dir=run_dir,
        grid_spec=grid_spec,
        hypercube_npy_path=hypercube_npy_path,
        pca_anomaly_tif_path=pca_anomaly_tif_path,
        objects_index_path=objects_index_path,
        clusters_summary_path=clusters_summary_path,
        object_rows=object_rows,
        cluster_rows=cluster_rows,
    )


async def _load_required_artifacts(session: AsyncSession, run_id: str) -> dict[str, Artifact]:
    rows = await session.scalars(select(Artifact).where(Artifact.run_id == run_id))
    artifact_map = {artifact.name: artifact for artifact in rows}
    validated: dict[str, Artifact] = {}

    for artifact_name, allowed_classes in REQUIRED_ARTIFACT_CLASSES.items():
        artifact = artifact_map.get(artifact_name)
        if artifact is None:
            raise StageError(f"Experimental run validation failed: required artifact missing: {artifact_name}.")
        if artifact.artifact_class not in allowed_classes:
            raise StageError(f"Experimental run validation failed: invalid artifact class: {artifact_name}.")
        validated[artifact_name] = artifact

    return validated


def _require_file(path: Path, artifact_name: str) -> None:
    if not path.is_file():
        raise StageError(f"Experimental run validation failed: required file missing: {artifact_name}.")


def _validate_raster_grid(raster_path: Path, grid_spec: GridSpec) -> None:
    sidecar_path = raster_sidecar_path(raster_path)
    if not sidecar_path.is_file():
        raise StageError(f"Experimental run validation failed: raster sidecar missing: {raster_path.name}.")
    sidecar = read_manifest(sidecar_path)
    if sidecar["crs"] != grid_spec.crs:
        raise GridDriftError(f"Experimental input CRS mismatch: {raster_path.name}")
    if [float(value) for value in sidecar["transform"]] != [float(value) for value in grid_spec.manifest.crs_transform]:
        raise GridDriftError(f"Experimental input transform mismatch: {raster_path.name}")
    if (int(sidecar["height"]), int(sidecar["width"])) != (grid_spec.size, grid_spec.size):
        raise GridDriftError(f"Experimental input size mismatch: {raster_path.name}")
    if float(sidecar["nodata"]) != float(grid_spec.nodata):
        raise GridDriftError(f"Experimental input nodata mismatch: {raster_path.name}")


def _validate_hypercube_shape(path: Path, grid_spec: GridSpec) -> None:
    cube = np.load(path, mmap_mode="r")
    try:
        if cube.ndim != 3 or cube.shape[:2] != (grid_spec.size, grid_spec.size):
            raise GridDriftError("Experimental input hypercube shape does not match the RUN grid.")
        if cube.shape[2] < 2:
            raise StageError("Experimental run validation failed: hypercube requires at least two bands.")
    finally:
        del cube


def _validate_anomaly_shape(path: Path, grid_spec: GridSpec) -> None:
    with Image.open(path) as image:
        anomaly = np.array(image, dtype=np.float32)
    if anomaly.shape != (grid_spec.size, grid_spec.size):
        raise GridDriftError("Experimental input anomaly raster does not match the RUN grid.")


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))

