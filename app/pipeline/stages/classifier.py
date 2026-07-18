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
FINAL_FINDINGS_SUMMARY_VERSION = "final_area_findings_v1"
FINAL_FINDING_SCORE_TYPE = "app_score"

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
REQUIRED_OBJECT_COLUMNS = ("object_id", "cluster_id", "row_min", "row_max", "col_min", "col_max")
REQUIRED_CLUSTER_COLUMNS = ("cluster_id",)


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
    _validate_classifier_arrays(hypercube=hypercube, anomaly=anomaly)

    object_rows = _read_csv_rows(objects_path)
    cluster_rows = _read_csv_rows(clusters_path)
    _validate_csv_columns(path=objects_path, rows=object_rows, required_columns=REQUIRED_OBJECT_COLUMNS)
    _validate_csv_columns(path=clusters_path, rows=cluster_rows, required_columns=REQUIRED_CLUSTER_COLUMNS)

    classifications: list[dict[str, object]] = []
    for row in object_rows:
        object_id = _parse_required_int(row, "object_id")
        cluster_id = _parse_required_int(row, "cluster_id")
        row_min = _parse_required_int(row, "row_min")
        row_max = _parse_required_int(row, "row_max")
        col_min = _parse_required_int(row, "col_min")
        col_max = _parse_required_int(row, "col_max")
        _validate_object_bounds(
            object_id=object_id,
            row_min=row_min,
            row_max=row_max,
            col_min=col_min,
            col_max=col_max,
            height=int(hypercube.shape[0]),
            width=int(hypercube.shape[1]),
        )
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
        class_score = round(float(classification.class_score), 6)
        finding = classify_area_finding(
            score=class_score,
            row_min=row_min,
            row_max=row_max,
            col_min=col_min,
            col_max=col_max,
        )
        classifications.append(
            {
                "object_id": object_id,
                "cluster_id": cluster_id,
                "row_min": row_min,
                "row_max": row_max,
                "col_min": col_min,
                "col_max": col_max,
                "class_id": classification.class_id.value,
                "class_score": class_score,
                "class_family": classification.class_family,
                "classifier_version": classification.classifier_version,
                "classifier_quality": "input_contract_validated",
                "finding_label": finding["finding_label"],
                "finding_score": class_score,
                "score_type": FINAL_FINDING_SCORE_TYPE,
                "finding_reason": finding["finding_reason"],
                "review_order": finding["review_order"],
            }
        )

    counts = Counter(row["class_id"] for row in classifications)
    summary = {
        "classifier_stage": "core",
        "classifier_quality": "input_contract_validated",
        "object_count": len(classifications),
        "cluster_count": len(cluster_rows),
        "class_counts": dict(sorted(counts.items())),
        "classifier_version": classifications[0]["classifier_version"] if classifications else CORE_CLASSIFIER_VERSION,
        "output_contract": "core_classifier_outputs_v2",
        "input_contract": "classifier_inputs_v1",
        "legacy_aliases": list(LEGACY_CLASSIFIER_ARTIFACTS.values()),
        "final_area_findings": build_final_area_findings_summary(
            classifications,
            run_id=run_dir.name,
            data_quality_status="input_contract_validated",
        ),
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



def classify_area_finding(
    *,
    score: float,
    row_min: int,
    row_max: int,
    col_min: int,
    col_max: int,
) -> dict[str, str]:
    # Deterministic screening heuristic. The score is not a measured
    # probability and the label is not physical confirmation.
    height = max(1, int(row_max) - int(row_min) + 1)
    width = max(1, int(col_max) - int(col_min) + 1)
    long_side = max(height, width)
    short_side = max(1, min(height, width))
    ratio = long_side / short_side
    compact = long_side <= 3
    elongated = ratio >= 3.0
    score = max(0.0, min(1.0, float(score)))

    if score >= 0.7 and elongated:
        return {
            "finding_label": "ENTRANCE_SHAFT_TRACE",
            "finding_reason": f"app_score={score:.3f}; shape={height}x{width}; elongated",
            "review_order": "01_CORE_REVIEW",
        }
    if score >= 0.7 and compact:
        return {
            "finding_label": "COMPACT_CHAMBER_POINT",
            "finding_reason": f"app_score={score:.3f}; shape={height}x{width}; compact",
            "review_order": "01_CORE_REVIEW",
        }
    if score >= 0.7:
        return {
            "finding_label": "CHAMBER_VOID_AREA",
            "finding_reason": f"app_score={score:.3f}; shape={height}x{width}; area-like",
            "review_order": "01_CORE_REVIEW",
        }
    if score >= 0.6 and elongated:
        return {
            "finding_label": "POSSIBLE_ENTRANCE_SHAFT",
            "finding_reason": f"app_score={score:.3f}; shape={height}x{width}; elongated",
            "review_order": "02_SECOND_REVIEW",
        }
    if score >= 0.6:
        return {
            "finding_label": "POSSIBLE_CHAMBER_STRUCTURE_AREA",
            "finding_reason": f"app_score={score:.3f}; shape={height}x{width}; area-like",
            "review_order": "02_SECOND_REVIEW",
        }
    if score >= 0.5:
        return {
            "finding_label": "RING_CONTEXT_AREA",
            "finding_reason": f"app_score={score:.3f}; compare cluster context",
            "review_order": "03_CONTEXT_REVIEW",
        }
    if score >= 0.4:
        return {
            "finding_label": "WEAK_CONTEXT_AREA",
            "finding_reason": f"app_score={score:.3f}; use only near stronger objects",
            "review_order": "04_LATE_REVIEW",
        }
    return {
        "finding_label": "BACKGROUND_AREA",
        "finding_reason": f"app_score={score:.3f}",
        "review_order": "05_BACKGROUND",
    }


def build_final_area_findings_summary(
    classifications: list[dict[str, object]],
    *,
    run_id: str,
    data_quality_status: str,
) -> dict[str, object]:
    grouped: dict[str, dict[str, object]] = {}
    for row in classifications:
        label = str(row.get("finding_label") or "BACKGROUND_AREA")
        score = max(0.0, min(1.0, float(row.get("finding_score", row.get("class_score", 0.0)))))
        item = grouped.setdefault(
            label,
            {
                "finding_label": label,
                "finding_score": score,
                "score_type": FINAL_FINDING_SCORE_TYPE,
                "supporting_candidate_count": 0,
            },
        )
        item["supporting_candidate_count"] = int(item["supporting_candidate_count"]) + 1
        item["finding_score"] = max(float(item["finding_score"]), score)

    ranked_findings = sorted(
        grouped.values(),
        key=lambda item: (
            -float(item["finding_score"]),
            -int(item["supporting_candidate_count"]),
            str(item["finding_label"]),
        ),
    )
    top = ranked_findings[0] if ranked_findings else None
    top_score = float(top["finding_score"]) if top else 0.0
    tied_top_findings = [
        item
        for item in ranked_findings
        if abs(float(item["finding_score"]) - top_score) <= 1e-9
    ]

    if not classifications:
        result_status = "no_objects"
        best_finding = None
        best_score = None
        summary_text = "No classifier objects were found, so there is no area finding to rank."
    elif top_score < 0.4:
        result_status = "no_strong_result"
        best_finding = None
        best_score = None
        summary_text = (
            f"No strong result was found. The highest app score was {top_score * 100:.0f}%, "
            "which is in the background range."
        )
    elif top_score < 0.6:
        result_status = "unclear_result"
        best_finding = str(top["finding_label"])
        best_score = round(top_score, 6)
        summary_text = (
            f"The result is unclear. The strongest pattern was "
            f"{_easy_finding_name(best_finding)} with an app score of {top_score * 100:.0f}%, "
            "but it is only a context-level result."
        )
    else:
        best_finding = str(top["finding_label"])
        best_score = round(top_score, 6)
        support_count = int(top["supporting_candidate_count"])
        best_name = _easy_finding_name(best_finding)
        sentence_best_name = best_name[:1].upper() + best_name[1:]

        if len(tied_top_findings) > 1:
            result_status = "tied_top_result"
            summary_text = (
                f"The top findings are tied for the highest app score at "
                f"{top_score * 100:.0f}%. {sentence_best_name} ranks first because "
                f"{support_count} "
                f"{'object supports' if support_count == 1 else 'objects support'} it, "
                "the highest support count among the tied findings. "
                "Review all tied top findings."
            )
        else:
            result_status = "result_available"
            summary_text = (
                f"The strongest result is {best_name} with an app score of "
                f"{top_score * 100:.0f}%. {support_count} "
                f"{'object supports' if support_count == 1 else 'objects support'} this finding."
            )
            if len(ranked_findings) > 1:
                second = ranked_findings[1]
                summary_text += (
                    f" The next result is {_easy_finding_name(str(second['finding_label']))} "
                    f"with an app score of {float(second['finding_score']) * 100:.0f}%."
                )
            summary_text += " The strongest result is the first one to review."

    return {
        "summary_version": FINAL_FINDINGS_SUMMARY_VERSION,
        "run_id": run_id,
        "result_status": result_status,
        "best_finding": best_finding,
        "best_finding_score": best_score,
        "score_type": FINAL_FINDING_SCORE_TYPE,
        "ranked_findings": ranked_findings,
        "data_quality_status": data_quality_status,
        "summary_text_easy_english": summary_text,
        "depth_status": "not_available",
    }


def _easy_finding_name(label: str) -> str:
    names = {
        "ENTRANCE_SHAFT_TRACE": "an entrance or shaft-like trace",
        "COMPACT_CHAMBER_POINT": "a compact chamber-like point",
        "CHAMBER_VOID_AREA": "a chamber or void-like area",
        "POSSIBLE_ENTRANCE_SHAFT": "a possible entrance or shaft-like trace",
        "POSSIBLE_CHAMBER_STRUCTURE_AREA": "a possible chamber or structure-like area",
        "RING_CONTEXT_AREA": "a ring or context area",
        "WEAK_CONTEXT_AREA": "a weak context area",
        "BACKGROUND_AREA": "background variation",
    }
    return names.get(label, label.replace("_", " ").casefold())

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
        "classifier_quality": summary.get("classifier_quality", "input_contract_validated"),
        "classifier_version": summary.get("classifier_version", CORE_CLASSIFIER_VERSION),
        "object_count": int(summary.get("object_count", len(object_labels))),
        "cluster_count": int(summary.get("cluster_count", len(cluster_labels))),
        "object_labels": object_labels,
        "cluster_labels": cluster_labels,
    }


def _validate_classifier_arrays(*, hypercube: np.ndarray, anomaly: np.ndarray) -> None:
    if hypercube.ndim != 3:
        raise StageError(f"Classifier hypercube must be HWC, got shape {hypercube.shape}.")
    if hypercube.shape[-1] < 1:
        raise StageError("Classifier hypercube must contain at least one band.")
    if anomaly.ndim != 2:
        raise StageError(f"Classifier anomaly map must be 2D, got shape {anomaly.shape}.")
    if tuple(hypercube.shape[:2]) != tuple(anomaly.shape):
        raise StageError(
            f"Classifier input shape mismatch: hypercube={hypercube.shape[:2]}, anomaly={anomaly.shape}."
        )


def _validate_csv_columns(*, path: Path, rows: list[dict[str, str]], required_columns: tuple[str, ...]) -> None:
    if not rows:
        return
    missing = [column for column in required_columns if column not in rows[0]]
    if missing:
        raise StageError(f"Classifier input {path.name} is missing required columns: {', '.join(missing)}")


def _parse_required_int(row: dict[str, str], column: str) -> int:
    try:
        return int(row[column])
    except KeyError as exc:
        raise StageError(f"Classifier object row is missing required column: {column}") from exc
    except (TypeError, ValueError) as exc:
        raise StageError(f"Classifier object row has invalid integer value for {column}: {row.get(column)!r}") from exc


def _validate_object_bounds(
    *,
    object_id: int,
    row_min: int,
    row_max: int,
    col_min: int,
    col_max: int,
    height: int,
    width: int,
) -> None:
    if row_min > row_max or col_min > col_max:
        raise StageError(f"Classifier object {object_id} has inverted bounds.")
    if row_min < 0 or col_min < 0 or row_max >= height or col_max >= width:
        raise StageError(
            f"Classifier object {object_id} bounds exceed raster shape: "
            f"rows={row_min}-{row_max}, cols={col_min}-{col_max}, shape={height}x{width}."
        )


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
