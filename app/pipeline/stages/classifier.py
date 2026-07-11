from __future__ import annotations

import csv
import json
import shutil
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image

from app.db.models.enums import ArtifactClass
from app.errors import StageError
from app.pipeline._base import ParityCategory, Stage, StageContext, StageResult, build_stage_artifact
from app.pipeline.stages.classifier_core import CORE_CLASSIFIER_VERSION, NeutralFeatureVector, classify_feature_vector
from app.pipeline.stages.hypercube import HYPERCUBE_NPY_NAME
from app.pipeline.stages.object_extract import CLUSTERS_SUMMARY_NAME, OBJECTS_INDEX_NAME
from app.pipeline.stages.pca_anomaly import PCA_ANOMALY_TIF_NAME

CLASSIFIER_OUTPUT_DIRNAME = "classifier"
LEGACY_CLASSIFIER_OUTPUT_DIRNAME = "experimental"
CLASSIFICATIONS_CSV_NAME = "classifications.csv"
SUMMARY_JSON_NAME = "summary.json"
NEUTRAL_LABELS_JSON_NAME = "neutral_target_labels.json"

CORE_CLASSIFIER_ARTIFACTS = {
    "classifications": "classifier_classifications",
    "summary": "classifier_summary",
    "neutral_labels": "classifier_neutral_labels",
}
LEGACY_CLASSIFIER_ARTIFACTS = {
    "classifications": "experimental_classifications",
    "summary": "experimental_summary",
    "neutral_labels": "experimental_neutral_labels",
}


class ClassifierStage(Stage):
    name = "classifier"
    parity_category = ParityCategory.PARITY_REPLACES
    parity_reason = "Runs the core neutral classifier as a normal pipeline stage."

    async def run(self, context: StageContext) -> StageResult:
        classifications, summary = build_classifier_results(context.run_dir)
        outputs = write_classifier_outputs(context.run_dir, classifications, summary)
        artifacts = []
        for key, artifact_name in CORE_CLASSIFIER_ARTIFACTS.items():
            path = outputs[key]
            artifacts.append(
                build_stage_artifact(
                    name=artifact_name,
                    relative_path=path.relative_to(context.run_dir).as_posix(),
                    artifact_class=ArtifactClass.REDACTED_PUBLIC,
                    size_bytes=path.stat().st_size,
                )
            )
        for key, artifact_name in LEGACY_CLASSIFIER_ARTIFACTS.items():
            path = outputs[f"legacy_{key}"]
            artifacts.append(
                build_stage_artifact(
                    name=artifact_name,
                    relative_path=path.relative_to(context.run_dir).as_posix(),
                    artifact_class=ArtifactClass.REDACTED_PUBLIC,
                    size_bytes=path.stat().st_size,
                    metadata={"alias_for": CORE_CLASSIFIER_ARTIFACTS[key], "deprecated": True},
                )
            )
        return StageResult(
            artifacts=artifacts,
            metadata={
                "object_count": summary["object_count"],
                "cluster_count": summary["cluster_count"],
                "classifier_version": summary["classifier_version"],
                "classifier_stage": summary["classifier_stage"],
                "legacy_aliases_published": True,
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

    classifications: list[dict[str, object]] = []
    for row in object_rows:
        row_min = int(row["row_min"])
        row_max = int(row["row_max"])
        col_min = int(row["col_min"])
        col_max = int(row["col_max"])
        patch = hypercube[row_min : row_max + 1, col_min : col_max + 1, :]
        valid_values = _valid_feature_values(patch)
        anomaly_patch = anomaly[row_min : row_max + 1, col_min : col_max + 1]
        finite_anomaly = anomaly_patch[np.isfinite(anomaly_patch)]
        feature_vector = NeutralFeatureVector(
            signal_mean=_normalize_feature(float(valid_values.mean()) if valid_values.size else 0.0),
            signal_peak=_normalize_feature(float(finite_anomaly.max()) if finite_anomaly.size else 0.0),
            signal_spread=_normalize_feature(float(valid_values.std()) if valid_values.size else 0.0),
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
            }
        )

    counts = Counter(row["class_id"] for row in classifications)
    summary = {
        "classifier_stage": "core",
        "object_count": len(classifications),
        "cluster_count": len(cluster_rows),
        "class_counts": dict(sorted(counts.items())),
        "classifier_version": classifications[0]["classifier_version"] if classifications else CORE_CLASSIFIER_VERSION,
        "output_contract": "core_classifier_outputs_v1",
        "legacy_aliases": list(LEGACY_CLASSIFIER_ARTIFACTS.values()),
    }
    return classifications, summary


def write_classifier_outputs(run_dir: Path, classifications: list[dict[str, object]], summary: dict[str, object]) -> dict[str, Path]:
    output_dir = run_dir / CLASSIFIER_OUTPUT_DIRNAME
    legacy_output_dir = run_dir / LEGACY_CLASSIFIER_OUTPUT_DIRNAME
    output_dir.mkdir(parents=True, exist_ok=True)
    legacy_output_dir.mkdir(parents=True, exist_ok=True)

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

    legacy_classifications_path = legacy_output_dir / CLASSIFICATIONS_CSV_NAME
    legacy_summary_path = legacy_output_dir / SUMMARY_JSON_NAME
    legacy_neutral_labels_path = legacy_output_dir / NEUTRAL_LABELS_JSON_NAME
    shutil.copyfile(classifications_path, legacy_classifications_path)
    shutil.copyfile(summary_path, legacy_summary_path)
    shutil.copyfile(neutral_labels_path, legacy_neutral_labels_path)

    return {
        "classifications": classifications_path,
        "summary": summary_path,
        "neutral_labels": neutral_labels_path,
        "legacy_classifications": legacy_classifications_path,
        "legacy_summary": legacy_summary_path,
        "legacy_neutral_labels": legacy_neutral_labels_path,
    }


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
        "classifier_stage": summary.get("classifier_stage", "core"),
        "classifier_version": summary.get("classifier_version", CORE_CLASSIFIER_VERSION),
        "object_count": int(summary.get("object_count", len(object_labels))),
        "cluster_count": int(summary.get("cluster_count", len(cluster_labels))),
        "object_labels": object_labels,
        "cluster_labels": cluster_labels,
    }


def _valid_feature_values(patch: np.ndarray) -> np.ndarray:
    if patch.ndim != 3 or patch.shape[-1] == 0:
        return np.array([], dtype=np.float32)
    if patch.shape[-1] == 1:
        feature_patch = patch
        valid_mask = np.isfinite(feature_patch).all(axis=-1)
    else:
        feature_patch = patch[:, :, :-1]
        valid_mask = (patch[:, :, -1] > 0.5) & np.isfinite(feature_patch).all(axis=-1)
    values = feature_patch[valid_mask]
    values = values[np.isfinite(values)]
    return values.astype(np.float32, copy=False)


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
    return max(0.0, min(1.0, round(float(value), 6)))
