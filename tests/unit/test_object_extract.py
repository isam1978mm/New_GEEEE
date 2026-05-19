from __future__ import annotations

import asyncio
import csv
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import pytest
from PIL import Image

from app.db.models.enums import ArtifactClass
from app.errors import GridDriftError
from app.pipeline._base import StageContext
from app.pipeline.stages.dem import write_raster_sidecar
from app.pipeline.stages.grid import build_run_grid
from app.pipeline.stages.object_extract import ObjectExtractStage, build_object_products
from app.services.storage import read_manifest


def test_build_object_products_finds_objects_clusters_and_pixel_space_only_rows() -> None:
    anomaly = np.zeros((12, 12), dtype=np.float32)
    anomaly[1:4, 1:4] = 0.95
    anomaly[7:10, 7:11] = 0.99
    hypercube = np.dstack([anomaly, anomaly * 2.0]).astype(np.float32)

    products = build_object_products(anomaly, hypercube)

    objects = products["objects"]
    clusters = products["clusters"]
    assert len(objects) == 2
    assert len(clusters) == 2
    first = objects[0]
    assert set(first.keys()) == {
        "object_id",
        "row_min",
        "row_max",
        "col_min",
        "col_max",
        "row_center",
        "col_center",
        "area_px",
        "mean_anomaly",
        "max_anomaly",
        "cluster_id",
    }
    forbidden = {"lat", "lon", "latitude", "longitude", "x", "y", "geometry", "bbox"}
    assert forbidden.isdisjoint({key.lower() for key in first.keys()})


def test_object_extract_stage_writes_classified_outputs_and_patches() -> None:
    with TemporaryDirectory() as temp_dir:
        run_dir = Path(temp_dir)
        grid_spec = build_run_grid(35.59499, 36.12694)
        anomaly = np.zeros((grid_spec.size, grid_spec.size), dtype=np.float32)
        anomaly[10:18, 20:28] = 0.98
        anomaly[100:108, 140:149] = 0.99
        hypercube = np.dstack([anomaly, anomaly * 2.0, anomaly * 3.0]).astype(np.float32)
        _write_anomaly_inputs(run_dir, anomaly, hypercube, grid_spec)
        context = StageContext(run_id="run-1", settings=_settings(run_dir), run_dir=run_dir)

        result = asyncio.run(ObjectExtractStage(grid_spec=grid_spec).run(context))

        artifact_names = [artifact.name for artifact in result.artifacts]
        assert artifact_names[:3] == ["objects_index", "clusters_summary", "object_mask"]
        assert result.artifacts[0].artifact_class == ArtifactClass.REDACTED_PUBLIC
        assert result.artifacts[1].artifact_class == ArtifactClass.REDACTED_PUBLIC
        assert result.artifacts[2].artifact_class == ArtifactClass.LOCAL_SENSITIVE
        assert any(name.startswith("object_patch_") for name in artifact_names[3:])

        with (run_dir / "objects_index.csv").open("r", encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        assert len(rows) == 2
        assert set(rows[0].keys()) == {
            "object_id",
            "cluster_id",
            "row_min",
            "row_max",
            "col_min",
            "col_max",
            "row_center",
            "col_center",
            "area_px",
            "mean_anomaly",
            "max_anomaly",
        }

        patch_paths = sorted((run_dir / "object_patches").glob("*.npy"))
        assert len(patch_paths) == 2
        patch = np.load(patch_paths[0])
        assert patch.ndim == 3
        assert patch.shape[-1] == 3


def test_object_extract_stage_raises_for_grid_drift() -> None:
    with TemporaryDirectory() as temp_dir:
        run_dir = Path(temp_dir)
        grid_spec = build_run_grid(35.59499, 36.12694)
        anomaly = np.zeros((grid_spec.size, grid_spec.size), dtype=np.float32)
        hypercube = np.dstack([anomaly, anomaly]).astype(np.float32)
        _write_anomaly_inputs(run_dir, anomaly, hypercube, grid_spec, mutate_transform=True)
        context = StageContext(run_id="run-1", settings=_settings(run_dir), run_dir=run_dir)

        with pytest.raises(GridDriftError):
            asyncio.run(ObjectExtractStage(grid_spec=grid_spec).run(context))


def _write_anomaly_inputs(
    run_dir: Path,
    anomaly: np.ndarray,
    hypercube: np.ndarray,
    grid_spec,
    *,
    mutate_transform: bool = False,
) -> None:
    Image.fromarray(anomaly.astype(np.float32)).save(run_dir / "pca_anomaly.tif", format="TIFF")
    write_raster_sidecar(
        run_dir / "pca_anomaly.tif",
        grid_manifest=grid_spec.manifest,
        nodata=grid_spec.nodata,
        dtype="float32",
        shape=anomaly.shape,
    )
    if mutate_transform:
        sidecar_path = run_dir / "pca_anomaly.tif.meta.json"
        payload = read_manifest(sidecar_path)
        payload["transform"][2] = float(payload["transform"][2]) + 1.0
        sidecar_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    np.save(run_dir / "hypercube.npy", hypercube.astype(np.float32))


def _settings(run_dir: Path):
    from app.config import Settings

    data_dir = run_dir / "data"
    return Settings(data_dir=data_dir, database_path=data_dir / "db.sqlite")
