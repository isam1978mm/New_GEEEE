from __future__ import annotations

import csv
import json
from collections import deque
from pathlib import Path
from typing import Iterable

import numpy as np
from PIL import Image

from app.db.models.enums import ArtifactClass
from app.errors import GridDriftError, StageError
from app.pipeline._base import ParityCategory, Stage, StageContext, StageResult, build_stage_artifact
from app.pipeline.qa_paths import ensure_run_qa_dir
from app.pipeline.stages.dem import raster_sidecar_path
from app.pipeline.stages.grid import GridSpec
from app.pipeline.stages.hypercube import HYPERCUBE_NPY_NAME
from app.pipeline.stages.pca_anomaly import PCA_ANOMALY_TIF_NAME
from app.services.storage import read_manifest

OBJECTS_INDEX_NAME = "objects_index.csv"
CLUSTERS_SUMMARY_NAME = "clusters_summary.csv"
OBJECT_PATCHES_DIRNAME = "objects/object_patches"
OBJECT_MASK_NAME = "object_mask.npy"

MIN_OBJECT_PIXELS = 4
ANOMALY_PERCENTILE = 90.0
ANOMALY_FLOOR = 0.6
CLUSTER_EPS_PX = 6.0
CLUSTER_MIN_SAMPLES = 1


def _read_single_band_tif(path: Path) -> np.ndarray:
    with Image.open(path) as image:
        return np.array(image, dtype=np.float32)


def _validate_anomaly_sidecar(path: Path, grid_spec: GridSpec) -> None:
    sidecar_path = raster_sidecar_path(path)
    if not sidecar_path.is_file():
        raise StageError(f"Missing raster sidecar for object extraction input: {path.name}")
    sidecar = read_manifest(sidecar_path)
    if sidecar["crs"] != grid_spec.crs:
        raise GridDriftError(f"Object extraction CRS mismatch: {path.name}")
    if [float(value) for value in sidecar["transform"]] != [float(value) for value in grid_spec.manifest.crs_transform]:
        raise GridDriftError(f"Object extraction transform mismatch: {path.name}")
    if (int(sidecar["height"]), int(sidecar["width"])) != (grid_spec.size, grid_spec.size):
        raise GridDriftError(f"Object extraction size mismatch: {path.name}")
    if float(sidecar["nodata"]) != float(grid_spec.nodata):
        raise GridDriftError(f"Object extraction nodata mismatch: {path.name}")


def load_object_extract_inputs(run_dir: Path, grid_spec: GridSpec) -> tuple[np.ndarray, np.ndarray]:
    anomaly_path = run_dir / PCA_ANOMALY_TIF_NAME
    if not anomaly_path.is_file():
        raise StageError("PCA anomaly stage output is required before object extraction.")
    _validate_anomaly_sidecar(anomaly_path, grid_spec)

    hypercube_path = run_dir / HYPERCUBE_NPY_NAME
    if not hypercube_path.is_file():
        raise StageError("Hypercube stage output is required before object extraction.")

    anomaly = _read_single_band_tif(anomaly_path).astype(np.float32)
    hypercube = np.load(hypercube_path).astype(np.float32)
    if anomaly.shape != (grid_spec.size, grid_spec.size):
        raise GridDriftError(f"PCA anomaly shape {anomaly.shape} does not match GRID {(grid_spec.size, grid_spec.size)}.")
    if hypercube.shape[:2] != (grid_spec.size, grid_spec.size):
        raise GridDriftError(f"Hypercube shape {hypercube.shape} does not match GRID {(grid_spec.size, grid_spec.size)}.")
    return anomaly, hypercube


def build_candidate_mask(
    anomaly: np.ndarray,
    *,
    percentile: float = ANOMALY_PERCENTILE,
    floor: float = ANOMALY_FLOOR,
) -> tuple[np.ndarray, float]:
    finite = anomaly[np.isfinite(anomaly)]
    if finite.size == 0:
        raise StageError("Object extraction requires finite PCA anomaly values.")
    threshold = max(float(np.percentile(finite, percentile)), float(floor))
    mask = np.isfinite(anomaly) & (anomaly >= threshold)
    return mask.astype(np.uint8), threshold


def _neighbors(row: int, col: int, height: int, width: int) -> Iterable[tuple[int, int]]:
    for row_delta in (-1, 0, 1):
        for col_delta in (-1, 0, 1):
            if row_delta == 0 and col_delta == 0:
                continue
            next_row = row + row_delta
            next_col = col + col_delta
            if 0 <= next_row < height and 0 <= next_col < width:
                yield next_row, next_col


def connected_components(mask: np.ndarray, *, min_pixels: int = MIN_OBJECT_PIXELS) -> list[dict[str, object]]:
    height, width = mask.shape
    visited = np.zeros_like(mask, dtype=bool)
    components: list[dict[str, object]] = []

    for row in range(height):
        for col in range(width):
            if visited[row, col] or not mask[row, col]:
                continue

            queue: deque[tuple[int, int]] = deque([(row, col)])
            visited[row, col] = True
            pixels: list[tuple[int, int]] = []
            while queue:
                current_row, current_col = queue.popleft()
                pixels.append((current_row, current_col))
                for next_row, next_col in _neighbors(current_row, current_col, height, width):
                    if visited[next_row, next_col] or not mask[next_row, next_col]:
                        continue
                    visited[next_row, next_col] = True
                    queue.append((next_row, next_col))

            if len(pixels) < min_pixels:
                continue

            rows = np.array([item[0] for item in pixels], dtype=np.int32)
            cols = np.array([item[1] for item in pixels], dtype=np.int32)
            components.append(
                {
                    "pixel_rows": rows,
                    "pixel_cols": cols,
                    "row_min": int(rows.min()),
                    "row_max": int(rows.max()),
                    "col_min": int(cols.min()),
                    "col_max": int(cols.max()),
                    "area_px": int(len(pixels)),
                    "centroid_row": float(rows.mean()),
                    "centroid_col": float(cols.mean()),
                }
            )
    return components


def summarize_objects(
    anomaly: np.ndarray,
    components: list[dict[str, object]],
) -> list[dict[str, object]]:
    objects: list[dict[str, object]] = []
    for object_index, component in enumerate(components, start=1):
        rows = component["pixel_rows"]
        cols = component["pixel_cols"]
        assert isinstance(rows, np.ndarray)
        assert isinstance(cols, np.ndarray)
        scores = anomaly[rows, cols]
        objects.append(
            {
                "object_id": object_index,
                "row_min": int(component["row_min"]),
                "row_max": int(component["row_max"]),
                "col_min": int(component["col_min"]),
                "col_max": int(component["col_max"]),
                "row_center": round(float(component["centroid_row"]), 3),
                "col_center": round(float(component["centroid_col"]), 3),
                "area_px": int(component["area_px"]),
                "mean_anomaly": round(float(np.nanmean(scores)), 6),
                "max_anomaly": round(float(np.nanmax(scores)), 6),
            }
        )
    return objects


def dbscan_cluster_objects(
    objects: list[dict[str, object]],
    *,
    eps_px: float = CLUSTER_EPS_PX,
    min_samples: int = CLUSTER_MIN_SAMPLES,
) -> tuple[list[int], list[dict[str, object]]]:
    if not objects:
        return [], []

    points = np.array([[float(item["row_center"]), float(item["col_center"])] for item in objects], dtype=np.float32)
    labels = [-1] * len(objects)
    visited = [False] * len(objects)
    cluster_id = 0

    def region_query(index: int) -> list[int]:
        deltas = points - points[index]
        distances = np.sqrt(np.sum(deltas * deltas, axis=1))
        return [candidate for candidate, distance in enumerate(distances.tolist()) if distance <= eps_px]

    for index in range(len(objects)):
        if visited[index]:
            continue
        visited[index] = True
        neighbors = region_query(index)
        if len(neighbors) < min_samples:
            labels[index] = -1
            continue

        labels[index] = cluster_id
        seeds = deque(neighbors)
        while seeds:
            neighbor_index = seeds.popleft()
            if not visited[neighbor_index]:
                visited[neighbor_index] = True
                neighbor_neighbors = region_query(neighbor_index)
                if len(neighbor_neighbors) >= min_samples:
                    for neighbor_neighbor in neighbor_neighbors:
                        if neighbor_neighbor not in seeds:
                            seeds.append(neighbor_neighbor)
            if labels[neighbor_index] == -1:
                labels[neighbor_index] = cluster_id
            elif labels[neighbor_index] < 0:
                labels[neighbor_index] = cluster_id
        cluster_id += 1

    for index, label in enumerate(labels):
        objects[index]["cluster_id"] = label

    summaries: list[dict[str, object]] = []
    for label in sorted(set(labels)):
        member_indexes = [index for index, member_label in enumerate(labels) if member_label == label]
        members = [objects[index] for index in member_indexes]
        summaries.append(
            {
                "cluster_id": int(label),
                "object_count": len(members),
                "total_area_px": int(sum(int(member["area_px"]) for member in members)),
                "mean_object_area_px": round(float(np.mean([float(member["area_px"]) for member in members])), 3),
                "max_object_anomaly": round(float(max(float(member["max_anomaly"]) for member in members)), 6),
            }
        )
    return labels, summaries


def build_object_products(
    anomaly: np.ndarray,
    hypercube: np.ndarray,
) -> dict[str, object]:
    mask, threshold = build_candidate_mask(anomaly)
    components = connected_components(mask)
    objects = summarize_objects(anomaly, components)
    _labels, clusters = dbscan_cluster_objects(objects)
    return {
        "threshold": threshold,
        "mask": mask,
        "objects": objects,
        "clusters": clusters,
        "hypercube": hypercube,
    }


def _write_csv(path: Path, fieldnames: list[str], rows: Iterable[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_object_outputs(run_dir: Path, products: dict[str, object]) -> dict[str, Path | list[Path]]:
    objects = products["objects"]
    clusters = products["clusters"]
    mask = products["mask"]
    hypercube = products["hypercube"]
    assert isinstance(objects, list)
    assert isinstance(clusters, list)
    assert isinstance(mask, np.ndarray)
    assert isinstance(hypercube, np.ndarray)

    objects_path = run_dir / OBJECTS_INDEX_NAME
    clusters_path = run_dir / CLUSTERS_SUMMARY_NAME
    mask_path = run_dir / "objects" / OBJECT_MASK_NAME
    patches_dir = run_dir / OBJECT_PATCHES_DIRNAME
    patches_dir.mkdir(parents=True, exist_ok=True)
    mask_path.parent.mkdir(parents=True, exist_ok=True)

    object_fields = [
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
    ]
    cluster_fields = [
        "cluster_id",
        "object_count",
        "total_area_px",
        "mean_object_area_px",
        "max_object_anomaly",
    ]

    _write_csv(objects_path, object_fields, objects)
    _write_csv(clusters_path, cluster_fields, clusters)
    np.save(mask_path, mask.astype(np.uint8))

    patch_paths: list[Path] = []
    for row in objects:
        row_min = int(row["row_min"])
        row_max = int(row["row_max"])
        col_min = int(row["col_min"])
        col_max = int(row["col_max"])
        patch = hypercube[row_min : row_max + 1, col_min : col_max + 1, :]
        patch_path = patches_dir / f"object_{int(row['object_id']):03d}.npy"
        np.save(patch_path, patch.astype(np.float32))
        patch_paths.append(patch_path)

    return {
        "objects_csv": objects_path,
        "clusters_csv": clusters_path,
        "mask_npy": mask_path,
        "patches": patch_paths,
    }


class ObjectExtractStage(Stage):
    name = "object_extract"
    parity_category = ParityCategory.PARITY_REPRODUCES

    def __init__(self, *, grid_spec: GridSpec) -> None:
        self.grid_spec = grid_spec

    async def run(self, context: StageContext) -> StageResult:
        anomaly, hypercube = load_object_extract_inputs(context.run_dir, self.grid_spec)
        products = build_object_products(anomaly, hypercube)
        outputs = write_object_outputs(context.run_dir, products)
        patch_paths = outputs["patches"]
        assert isinstance(patch_paths, list)

        artifacts = [
            build_stage_artifact(
                name="objects_index",
                relative_path=Path(outputs["objects_csv"]).relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.REDACTED_PUBLIC,
                size_bytes=Path(outputs["objects_csv"]).stat().st_size,
            ),
            build_stage_artifact(
                name="clusters_summary",
                relative_path=Path(outputs["clusters_csv"]).relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.REDACTED_PUBLIC,
                size_bytes=Path(outputs["clusters_csv"]).stat().st_size,
            ),
            build_stage_artifact(
                name="object_mask",
                relative_path=Path(outputs["mask_npy"]).relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=Path(outputs["mask_npy"]).stat().st_size,
                http_servable=False,
            ),
        ]
        for patch_path in patch_paths:
            artifacts.append(
                build_stage_artifact(
                    name=f"object_patch_{patch_path.stem.split('_')[-1]}",
                    relative_path=patch_path.relative_to(context.run_dir).as_posix(),
                    artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                    size_bytes=patch_path.stat().st_size,
                    http_servable=False,
                )
            )

        objects = products["objects"]
        clusters = products["clusters"]
        threshold = products["threshold"]
        assert isinstance(objects, list)
        assert isinstance(clusters, list)
        assert isinstance(threshold, float)
        return StageResult(
            artifacts=artifacts,
            metadata={
                "object_count": len(objects),
                "cluster_count": len(clusters),
                "candidate_threshold": threshold,
            },
        )
