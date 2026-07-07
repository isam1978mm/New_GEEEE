from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image

from app.db.models.enums import ArtifactClass
from app.errors import StageError
from app.pipeline._base import ParityCategory, Stage, StageContext, StageResult, build_stage_artifact
from app.pipeline.stages.hypercube import HYPERCUBE_NPY_NAME
from app.pipeline.stages.object_extract import CLUSTERS_SUMMARY_NAME, OBJECTS_INDEX_NAME
from app.pipeline.stages.pca_anomaly import PCA_ANOMALY_TIF_NAME
from app.pipeline.stages_experimental.classifier import NeutralFeatureVector, classify_feature_vector
from app.pipeline.stages_experimental.outputs import CLASSIFICATIONS_CSV_NAME, NEUTRAL_LABELS_JSON_NAME, SUMMARY_JSON_NAME

CLASSIFIER_OUTPUT_DIRNAME = "experimental"


class ClassifierStage(Stage):
    name = "classifier"
    parity_category = ParityCategory.PARITY_REPLACES
    parity_reason = "Runs the previously isolated neutral classifier as a normal pipeline stage."

    async def run(self, context: StageContext) -> StageResult:
        classifications, summary = build_classifier_results(context.run_dir)
        outputs = write_classifier_outputs(context.run_dir, classifications, summary)
        return StageResult(
            artifacts=[
                build_stage_artifact(
                    name="experimental_classifications",
                    relative_path=outputs["classifications"].relative_to(context.run_dir).as_posix(),
                    artifact_class=ArtifactClass.REDACTED_PUBLIC,
                    size_bytes=outputs["classifications"].stat().st_size,
                ),
                build_stage_artifact(
                    name="experimental_summary",
                    relative_path=outputs["summary"].relative_to(context.run_dir).as_posix(),
                    artifact_class=ArtifactClass.REDACTED_PUBLIC,
                    size_bytes=outputs["summary"].stat().st_size,
                ),
                build_stage_artifact(
                    name="experimental_neutral_labels",
                    relative_path=outputs["neutral_labels"].relative_to(context.run_dir).as_posix(),
                    artifact_class=ArtifactClass.REDACTED_PUBLIC,
                    size_bytes=outputs["neutral_labels"].stat().st_size,
                ),
            ],
            metadata={
                "object_count": summary["object_count"],
                "cluster_count": summary["cluster_count"],
                "classifier_version": summary["classifier_version"],
                "classifier_feature_policy": summary.get("classifier_feature_policy"),
            },
        )


def build_classifier_results(run_dir: Path) -> tuple[list[dict[str, object]], dict[str, object]]:
    hypercube_path = run_dir / HYPERCUBE_NPY_NAME
    anomaly_path = run_dir / PCA_ANOMALY_TIF_NAME
    objects_path = run_dir / OBJECTS_INDEX_NAME
    clusters_path = run_dir / CLUSTERS_SUMMARY_NAME
    for path in (hypercube_path, anomaly_path, objects_path, clusters_path):
        if not path.is_file():
            raise StageError(f"Classifier input is missing: {path.name}")

    hypercube = np.load(hypercube_path).astype(np.float32)
    with Image.open(anomaly_path) as image:
        anomaly = np.array(image, dtype=np.float32)
    object_rows = _read_csv_rows(objects_path)
    cluster_rows = _read_csv_rows(clusters_path)
    scene_feature_values = _valid_feature_values(hypercube)
    scene_anomaly_values = anomaly[np.isfinite(anomaly)]

    classifications: list[dict[str, object]] = []
    for row in object_rows:
        row_min = int(row["row_min"])
        row_max = int(row["row_max"])
        col_min = int(row["col_min"])
        col_max = int(row["col_max"])
        patch = hypercube[row_min : row_max + 1, col_min : col_max + 1, :]
        anomaly_patch = anomaly[row_min : row_max + 1, col_min : col_max + 1]
        diagnostics = _object_feature_diagnostics(
            patch,
            anomaly_patch,
            row=row,
            scene_feature_values=scene_feature_values,
            scene_anomaly_values=scene_anomaly_values,
        )
        feature_vector = NeutralFeatureVector(
            signal_mean=float(diagnostics["signal_mean"]),
            signal_peak=float(diagnostics["signal_peak"]),
            signal_spread=float(diagnostics["signal_spread"]),
        )
        classification = classify_feature_vector(feature_vector)
        classifications.append(
            {
                "object_id": int(row["object_id"]),
                "cluster_id": int(row["cluster_id"]),
                "row_min": row_min,
                "row_max": row_max,
                "col_min": col_min,
                "col_max": col_max,
                "class_id": classification.class_id.value,
                "class_score": round(float(classification.class_score), 6),
                "class_family": classification.class_family,
                "classifier_version": classification.classifier_version,
                **diagnostics,
            }
        )

    counts = Counter(row["class_id"] for row in classifications)
    summary = {
        "object_count": len(classifications),
        "cluster_count": len(cluster_rows),
        "class_counts": dict(sorted(counts.items())),
        "classifier_version": classifications[0]["classifier_version"] if classifications else "experimental_v1",
        "classifier_feature_policy": "private_local_robust_object_evidence_v1",
    }
    return classifications, summary


def write_classifier_outputs(run_dir: Path, classifications: list[dict[str, object]], summary: dict[str, object]) -> dict[str, Path]:
    output_dir = run_dir / CLASSIFIER_OUTPUT_DIRNAME
    output_dir.mkdir(parents=True, exist_ok=True)
    classifications_path = output_dir / CLASSIFICATIONS_CSV_NAME
    summary_path = output_dir / SUMMARY_JSON_NAME
    neutral_labels_path = output_dir / NEUTRAL_LABELS_JSON_NAME

    fieldnames = list(classifications[0].keys()) if classifications else ["object_id", "class_id", "class_score"]
    with classifications_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in classifications:
            writer.writerow(row)

    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    neutral_labels_path.write_text(json.dumps(_build_neutral_labels(classifications, summary), indent=2, sort_keys=True), encoding="utf-8")
    return {"classifications": classifications_path, "summary": summary_path, "neutral_labels": neutral_labels_path}


def _build_neutral_labels(classifications: list[dict[str, object]], summary: dict[str, object]) -> dict[str, object]:
    object_labels = [
        {
            "object_id": int(row["object_id"]),
            "cluster_id": int(row["cluster_id"]),
            "class_id": row["class_id"],
            "class_family": row["class_family"],
            "class_score": row["class_score"],
        }
        for row in classifications
    ]
    labels_by_cluster: dict[int, list[str]] = {}
    for row in classifications:
        cluster_id = int(row["cluster_id"])
        labels_by_cluster.setdefault(cluster_id, []).append(str(row["class_id"]))
    cluster_labels = [
        {
            "cluster_id": cluster_id,
            "dominant_class_id": _dominant_class_id(class_ids),
            "class_ids": sorted(class_ids),
        }
        for cluster_id, class_ids in sorted(labels_by_cluster.items())
    ]
    return {
        "classifier_version": summary.get("classifier_version", "experimental_v1"),
        "object_count": int(summary.get("object_count", len(object_labels))),
        "cluster_count": int(summary.get("cluster_count", len(cluster_labels))),
        "object_labels": object_labels,
        "cluster_labels": cluster_labels,
    }


def _object_feature_diagnostics(
    patch: np.ndarray,
    anomaly_patch: np.ndarray,
    *,
    row: dict[str, str],
    scene_feature_values: np.ndarray,
    scene_anomaly_values: np.ndarray,
) -> dict[str, object]:
    feature_patch, valid_mask = _valid_feature_patch_and_mask(patch)
    valid_values = feature_patch[valid_mask]
    valid_values = valid_values[np.isfinite(valid_values)].astype(np.float32, copy=False)
    anomaly_values = anomaly_patch[valid_mask] if anomaly_patch.shape == valid_mask.shape else anomaly_patch[np.isfinite(anomaly_patch)]
    anomaly_values = anomaly_values[np.isfinite(anomaly_values)].astype(np.float32, copy=False)

    bbox_area_px = int(max(patch.shape[0] * patch.shape[1], 1))
    object_area_px = int(_row_float(row, "area_px", float(bbox_area_px)))
    valid_pixel_count = int(valid_mask.sum())
    valid_pixel_fraction = valid_pixel_count / float(bbox_area_px)
    compactness = max(0.0, min(1.0, object_area_px / float(bbox_area_px)))

    signal_mean_raw = float(valid_values.mean()) if valid_values.size else 0.0
    signal_spread_raw = float(valid_values.std()) if valid_values.size else 0.0
    anomaly_mean = float(anomaly_values.mean()) if anomaly_values.size else 0.0
    anomaly_peak = float(anomaly_values.max()) if anomaly_values.size else 0.0
    signal_mean_z = _robust_z(signal_mean_raw, scene_feature_values)
    anomaly_peak_z = _robust_z(anomaly_peak, scene_anomaly_values)

    signal_mean = _unit_evidence_from_z(signal_mean_z) * valid_pixel_fraction
    signal_peak = _unit_evidence_from_z(anomaly_peak_z) * valid_pixel_fraction
    signal_spread = compactness * valid_pixel_fraction

    return {
        "signal_mean": round(float(signal_mean), 6),
        "signal_peak": round(float(signal_peak), 6),
        "signal_spread": round(float(signal_spread), 6),
        "signal_mean_raw": round(float(signal_mean_raw), 6),
        "signal_mean_z": round(float(signal_mean_z), 6),
        "signal_spread_raw": round(float(signal_spread_raw), 6),
        "anomaly_mean": round(float(anomaly_mean), 6),
        "anomaly_peak": round(float(anomaly_peak), 6),
        "anomaly_peak_z": round(float(anomaly_peak_z), 6),
        "object_area_px": int(object_area_px),
        "bbox_area_px": int(bbox_area_px),
        "compactness": round(float(compactness), 6),
        "valid_pixel_count": int(valid_pixel_count),
        "valid_pixel_fraction": round(float(valid_pixel_fraction), 6),
        "feature_policy": "private_local_robust_object_evidence_v1",
    }


def _valid_feature_values(patch: np.ndarray) -> np.ndarray:
    feature_patch, valid_mask = _valid_feature_patch_and_mask(patch)
    values = feature_patch[valid_mask]
    values = values[np.isfinite(values)]
    return values.astype(np.float32, copy=False)


def _valid_feature_patch_and_mask(patch: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    if patch.ndim != 3 or patch.shape[-1] == 0:
        return np.empty((*patch.shape[:2], 0), dtype=np.float32), np.zeros(patch.shape[:2], dtype=bool)
    if patch.shape[-1] == 1:
        feature_patch = patch.astype(np.float32, copy=False)
        valid_mask = np.isfinite(feature_patch).all(axis=-1)
    else:
        feature_patch = patch[:, :, :-1].astype(np.float32, copy=False)
        valid_mask = (patch[:, :, -1] > 0.5) & np.isfinite(feature_patch).all(axis=-1)
    return feature_patch, valid_mask.astype(bool)


def _row_float(row: dict[str, str], key: str, default: float) -> float:
    try:
        return float(row.get(key, default))
    except (TypeError, ValueError):
        return float(default)


def _robust_z(value: float, background: np.ndarray) -> float:
    if not np.isfinite(value):
        return 0.0
    finite = background[np.isfinite(background)].astype(np.float64, copy=False)
    if finite.size < 2:
        return 0.0
    median = float(np.median(finite))
    mad = float(np.median(np.abs(finite - median)))
    scale = 1.4826 * mad if np.isfinite(mad) and mad > 1e-9 else float(np.std(finite))
    if not np.isfinite(scale) or scale <= 1e-9:
        return 0.0
    return round(float((value - median) / scale), 6)


def _unit_evidence_from_z(value: float) -> float:
    if not np.isfinite(value):
        return 0.0
    return max(0.0, min(1.0, 0.5 + float(value) / 6.0))


def _dominant_class_id(class_ids: list[str]) -> str:
    if not class_ids:
        return ""
    counts = Counter(class_ids)
    max_count = max(counts.values())
    return sorted(class_id for class_id, count in counts.items() if count == max_count)[0]


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _normalize_feature(value: float) -> float:
    if not np.isfinite(value):
        return 0.0
    return round(float(value), 6)
