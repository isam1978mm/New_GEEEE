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
from app.pipeline.stages.dem import raster_sidecar_path
from app.pipeline.stages.grid import GridSpec
from app.pipeline.stages.hypercube import HYPERCUBE_NPY_NAME
from app.pipeline.stages.pca_anomaly import PCA_ANOMALY_TIF_NAME, PCA_RAW_SCORE_NPY_NAME
from app.services.storage import read_manifest

OBJECTS_INDEX_NAME = "objects_index.csv"
CLUSTERS_SUMMARY_NAME = "clusters_summary.csv"
OBJECT_PATCHES_DIRNAME = "objects/object_patches"
OBJECT_MASK_NAME = "object_mask.npy"
TARGET_OUTPUT_DIRNAME = "targets"
TARGET_CANDIDATES_CSV_NAME = "target_candidates.csv"
TARGET_SUMMARY_JSON_NAME = "target_summary.json"
TARGET_SUMMARY_TXT_NAME = "target_summary.txt"
DETECTED_FEATURES_GEOJSON_NAME = "detected_features_pixel.geojson"

MIN_OBJECT_PIXELS = 4
ANOMALY_PERCENTILE = 90.0
ANOMALY_FLOOR = 0.6
CLUSTER_EPS_PX = 6.0
CLUSTER_MIN_SAMPLES = 1
VALID_MASK_POLICY = "hypercube_last_binary_channel_when_available_else_all_finite"
ANOMALY_SCORE_SOURCE_RAW = "pca_raw_score_npy"
ANOMALY_SCORE_SOURCE_DISPLAY = "display_stretched_pca_anomaly_tif"
CANDIDATE_THRESHOLD_POLICY_RAW = "raw_score_robust_mad_fallback_midrange"
CANDIDATE_THRESHOLD_POLICY_DISPLAY = "display_percentile_90_floor_0_6"


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


def load_object_extract_inputs(run_dir: Path, grid_spec: GridSpec) -> tuple[np.ndarray, np.ndarray, str]:
    anomaly_path = run_dir / PCA_ANOMALY_TIF_NAME
    if not anomaly_path.is_file():
        raise StageError("PCA anomaly stage output is required before object extraction.")
    _validate_anomaly_sidecar(anomaly_path, grid_spec)

    hypercube_path = run_dir / HYPERCUBE_NPY_NAME
    if not hypercube_path.is_file():
        raise StageError("Hypercube stage output is required before object extraction.")

    raw_score_path = run_dir / PCA_RAW_SCORE_NPY_NAME
    if raw_score_path.is_file():
        anomaly = np.load(raw_score_path).astype(np.float32)
        score_source = ANOMALY_SCORE_SOURCE_RAW
    else:
        anomaly = _read_single_band_tif(anomaly_path).astype(np.float32)
        score_source = ANOMALY_SCORE_SOURCE_DISPLAY

    hypercube = np.load(hypercube_path).astype(np.float32)
    if anomaly.shape != (grid_spec.size, grid_spec.size):
        raise GridDriftError(f"PCA anomaly score shape {anomaly.shape} does not match GRID {(grid_spec.size, grid_spec.size)}.")
    if hypercube.shape[:2] != (grid_spec.size, grid_spec.size):
        raise GridDriftError(f"Hypercube shape {hypercube.shape} does not match GRID {(grid_spec.size, grid_spec.size)}.")
    return anomaly, hypercube, score_source


def build_candidate_mask(
    anomaly: np.ndarray,
    *,
    valid_mask: np.ndarray | None = None,
    nodata: float | None = None,
    percentile: float = ANOMALY_PERCENTILE,
    floor: float | None = ANOMALY_FLOOR,
    threshold_policy: str = CANDIDATE_THRESHOLD_POLICY_DISPLAY,
) -> tuple[np.ndarray, float]:
    finite_mask = np.isfinite(anomaly)
    if nodata is not None:
        finite_mask &= anomaly != np.float32(nodata)
    if valid_mask is not None:
        if valid_mask.shape != anomaly.shape:
            raise StageError(f"Object extraction valid_mask shape {valid_mask.shape} does not match anomaly shape {anomaly.shape}.")
        finite_mask &= valid_mask.astype(bool)
    finite = anomaly[finite_mask]
    if finite.size == 0:
        raise StageError("Object extraction requires valid finite PCA anomaly values.")
    if threshold_policy == CANDIDATE_THRESHOLD_POLICY_RAW:
        threshold = _raw_score_threshold(finite)
    elif threshold_policy == CANDIDATE_THRESHOLD_POLICY_DISPLAY:
        threshold = float(np.percentile(finite, percentile))
        if floor is not None:
            threshold = max(threshold, float(floor))
    else:
        raise StageError(f"Unknown object extraction threshold policy: {threshold_policy}")
    mask = finite_mask & (anomaly >= threshold)
    return mask.astype(np.uint8), threshold


def _raw_score_threshold(values: np.ndarray) -> float:
    finite = values[np.isfinite(values)].astype(np.float64)
    if finite.size == 0:
        raise StageError("Raw PCA score threshold requires finite values.")
    median = float(np.median(finite))
    mad = float(np.median(np.abs(finite - median)))
    if np.isfinite(mad) and mad > 0.0:
        robust_sigma = 1.4826 * mad
        return max(float(np.percentile(finite, 99.0)), median + 6.0 * robust_sigma)
    max_value = float(np.max(finite))
    if np.isfinite(max_value) and max_value > median:
        return median + 0.5 * (max_value - median)
    return max_value + 1e-6


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
    *,
    nodata: float | None = None,
    score_source: str = ANOMALY_SCORE_SOURCE_DISPLAY,
) -> dict[str, object]:
    valid_mask = _valid_mask_from_hypercube(hypercube)
    threshold_policy = (
        CANDIDATE_THRESHOLD_POLICY_RAW
        if score_source == ANOMALY_SCORE_SOURCE_RAW
        else CANDIDATE_THRESHOLD_POLICY_DISPLAY
    )
    threshold_floor = None if threshold_policy == CANDIDATE_THRESHOLD_POLICY_RAW else ANOMALY_FLOOR
    mask, threshold = build_candidate_mask(
        anomaly,
        valid_mask=valid_mask,
        nodata=nodata,
        floor=threshold_floor,
        threshold_policy=threshold_policy,
    )
    components = connected_components(mask)
    objects = summarize_objects(anomaly, components)
    _labels, clusters = dbscan_cluster_objects(objects)
    return {
        "threshold": threshold,
        "mask": mask,
        "objects": objects,
        "clusters": clusters,
        "hypercube": hypercube,
        "valid_pixel_count": int(valid_mask.sum()),
        "valid_mask_policy": VALID_MASK_POLICY,
        "anomaly_score_source": score_source,
        "candidate_threshold_policy": threshold_policy,
    }


def _valid_mask_from_hypercube(hypercube: np.ndarray) -> np.ndarray:
    if hypercube.ndim != 3 or hypercube.shape[-1] == 0:
        raise StageError(f"Hypercube must be HWC 3D for object extraction, got shape {hypercube.shape}.")
    if hypercube.shape[-1] > 1 and _looks_like_valid_mask(hypercube[:, :, -1]):
        feature_cube = hypercube[:, :, :-1]
        return ((hypercube[:, :, -1] > 0.5) & np.isfinite(feature_cube).all(axis=-1)).astype(bool)
    return np.isfinite(hypercube).all(axis=-1).astype(bool)


def _looks_like_valid_mask(channel: np.ndarray) -> bool:
    finite = channel[np.isfinite(channel)]
    if finite.size == 0:
        return False
    is_binary = np.isclose(finite, 0.0, atol=1e-6) | np.isclose(finite, 1.0, atol=1e-6)
    return bool(is_binary.all())


def _write_csv(path: Path, fieldnames: list[str], rows: Iterable[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _build_target_summary(
    *,
    objects: list[dict[str, object]],
    clusters: list[dict[str, object]],
    threshold: float,
    score_source: str,
    threshold_policy: str,
) -> dict[str, object]:
    return {
        "schema": "target_outputs_v1",
        "coordinate_space": "pixel_grid",
        "object_count": len(objects),
        "cluster_count": len(clusters),
        "candidate_threshold": float(threshold),
        "candidate_score_source": score_source,
        "candidate_threshold_policy": threshold_policy,
        "max_object_anomaly": max((float(row["max_anomaly"]) for row in objects), default=None),
        "outputs": {
            "csv": f"{TARGET_OUTPUT_DIRNAME}/{TARGET_CANDIDATES_CSV_NAME}",
            "txt": f"{TARGET_OUTPUT_DIRNAME}/{TARGET_SUMMARY_TXT_NAME}",
            "json": f"{TARGET_OUTPUT_DIRNAME}/{TARGET_SUMMARY_JSON_NAME}",
            "geojson": f"{TARGET_OUTPUT_DIRNAME}/{DETECTED_FEATURES_GEOJSON_NAME}",
        },
        "privacy": {
            "artifact_class": "FILESYSTEM_ONLY",
            "http_servable": False,
            "geographic_coordinates_included": False,
        },
    }


def _build_target_summary_text(summary: dict[str, object]) -> str:
    return "\n".join(
        [
            "Target output summary",
            f"Coordinate space: {summary['coordinate_space']}",
            f"Object count: {summary['object_count']}",
            f"Cluster count: {summary['cluster_count']}",
            f"Candidate threshold: {summary['candidate_threshold']}",
            f"Candidate score source: {summary['candidate_score_source']}",
            f"Candidate threshold policy: {summary['candidate_threshold_policy']}",
            "Geographic coordinates included: no",
            "Visibility: local filesystem only",
            "",
        ]
    )


def _pixel_bbox_polygon(row: dict[str, object]) -> list[list[list[float]]]:
    row_min = float(row["row_min"])
    row_max = float(row["row_max"]) + 1.0
    col_min = float(row["col_min"])
    col_max = float(row["col_max"]) + 1.0
    return [
        [
            [col_min, row_min],
            [col_max, row_min],
            [col_max, row_max],
            [col_min, row_max],
            [col_min, row_min],
        ]
    ]


def _build_detected_features_geojson(objects: list[dict[str, object]]) -> dict[str, object]:
    return {
        "type": "FeatureCollection",
        "coordinate_space": "pixel_grid",
        "geographic_coordinates_included": False,
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": _pixel_bbox_polygon(row),
                },
                "properties": {
                    "object_id": int(row["object_id"]),
                    "cluster_id": int(row["cluster_id"]),
                    "area_px": int(row["area_px"]),
                    "row_center": float(row["row_center"]),
                    "col_center": float(row["col_center"]),
                    "mean_anomaly": float(row["mean_anomaly"]),
                    "max_anomaly": float(row["max_anomaly"]),
                },
            }
            for row in objects
        ],
    }


def write_object_outputs(run_dir: Path, products: dict[str, object]) -> dict[str, Path | list[Path]]:
    objects = products["objects"]
    clusters = products["clusters"]
    mask = products["mask"]
    hypercube = products["hypercube"]
    threshold = products["threshold"]
    score_source = str(products.get("anomaly_score_source", ANOMALY_SCORE_SOURCE_DISPLAY))
    threshold_policy = str(products.get("candidate_threshold_policy", CANDIDATE_THRESHOLD_POLICY_DISPLAY))
    assert isinstance(objects, list)
    assert isinstance(clusters, list)
    assert isinstance(mask, np.ndarray)
    assert isinstance(hypercube, np.ndarray)
    assert isinstance(threshold, float)

    objects_path = run_dir / OBJECTS_INDEX_NAME
    clusters_path = run_dir / CLUSTERS_SUMMARY_NAME
    mask_path = run_dir / "objects" / OBJECT_MASK_NAME
    patches_dir = run_dir / OBJECT_PATCHES_DIRNAME
    targets_dir = run_dir / TARGET_OUTPUT_DIRNAME
    target_candidates_path = targets_dir / TARGET_CANDIDATES_CSV_NAME
    target_summary_json_path = targets_dir / TARGET_SUMMARY_JSON_NAME
    target_summary_txt_path = targets_dir / TARGET_SUMMARY_TXT_NAME
    detected_features_geojson_path = targets_dir / DETECTED_FEATURES_GEOJSON_NAME
    patches_dir.mkdir(parents=True, exist_ok=True)
    mask_path.parent.mkdir(parents=True, exist_ok=True)
    targets_dir.mkdir(parents=True, exist_ok=True)

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
    _write_csv(target_candidates_path, object_fields, objects)
    _write_csv(clusters_path, cluster_fields, clusters)
    np.save(mask_path, mask.astype(np.uint8))
    summary = _build_target_summary(
        objects=objects,
        clusters=clusters,
        threshold=threshold,
        score_source=score_source,
        threshold_policy=threshold_policy,
    )
    target_summary_json_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    target_summary_txt_path.write_text(_build_target_summary_text(summary), encoding="utf-8")
    detected_features_geojson_path.write_text(
        json.dumps(_build_detected_features_geojson(objects), indent=2, sort_keys=True),
        encoding="utf-8",
    )

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
        "target_candidates_csv": target_candidates_path,
        "target_summary_json": target_summary_json_path,
        "target_summary_txt": target_summary_txt_path,
        "detected_features_geojson": detected_features_geojson_path,
        "patches": patch_paths,
    }


class ObjectExtractStage(Stage):
    name = "object_extract"
    parity_category = ParityCategory.PARITY_REPRODUCES

    def __init__(self, *, grid_spec: GridSpec) -> None:
        self.grid_spec = grid_spec

    async def run(self, context: StageContext) -> StageResult:
        anomaly, hypercube, score_source = load_object_extract_inputs(context.run_dir, self.grid_spec)
        products = build_object_products(
            anomaly,
            hypercube,
            nodata=self.grid_spec.nodata,
            score_source=score_source,
        )
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
            build_stage_artifact(
                name="target_candidates_csv",
                relative_path=Path(outputs["target_candidates_csv"]).relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=Path(outputs["target_candidates_csv"]).stat().st_size,
                http_servable=False,
            ),
            build_stage_artifact(
                name="target_summary_json",
                relative_path=Path(outputs["target_summary_json"]).relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=Path(outputs["target_summary_json"]).stat().st_size,
                http_servable=False,
            ),
            build_stage_artifact(
                name="target_summary_txt",
                relative_path=Path(outputs["target_summary_txt"]).relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=Path(outputs["target_summary_txt"]).stat().st_size,
                http_servable=False,
            ),
            build_stage_artifact(
                name="detected_features_geojson",
                relative_path=Path(outputs["detected_features_geojson"]).relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=Path(outputs["detected_features_geojson"]).stat().st_size,
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
                "anomaly_score_source": str(products["anomaly_score_source"]),
                "candidate_threshold_policy": str(products["candidate_threshold_policy"]),
                "valid_pixel_count": int(products["valid_pixel_count"]),
                "valid_mask_policy": str(products["valid_mask_policy"]),
            },
        )
