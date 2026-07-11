from __future__ import annotations

import argparse
import asyncio
from collections import Counter

import numpy as np
from PIL import Image

from app.config import Settings
from app.db.session import create_engine, create_session_factory
from app.pipeline.stages.classifier import _valid_feature_values
from app.pipeline.stages_experimental.classifier import NeutralFeatureVector, classify_feature_vector
from app.pipeline.stages_experimental.inputs import ExperimentalInputs, validate_experimental_inputs
from app.pipeline.stages_experimental.outputs import write_experimental_outputs
from app.services.storage import ensure_data_dirs


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the local experimental classifier for a completed run.")
    parser.add_argument("--run-id", required=True, help="Completed core run identifier.")
    return parser


async def run_cli(*, run_id: str) -> int:
    settings = Settings()
    ensure_data_dirs(settings)
    engine = create_engine(settings)
    session_factory = create_session_factory(settings, engine)

    try:
        inputs = await validate_experimental_inputs(settings=settings, session_factory=session_factory, run_id=run_id)
        classifications, summary = build_experimental_results(inputs)
        await write_experimental_outputs(
            session_factory=session_factory,
            run_dir=inputs.run_dir,
            run_id=run_id,
            classifications=classifications,
            summary=summary,
        )
    finally:
        await engine.dispose()

    return 0


def build_experimental_results(inputs: ExperimentalInputs) -> tuple[list[dict[str, object]], dict[str, object]]:
    hypercube = np.load(inputs.hypercube_npy_path).astype(np.float32)
    with Image.open(inputs.pca_anomaly_tif_path) as image:
        anomaly = np.array(image, dtype=np.float32)

    classifications: list[dict[str, object]] = []
    for row in inputs.object_rows:
        row_min = int(row["row_min"])
        row_max = int(row["row_max"])
        col_min = int(row["col_min"])
        col_max = int(row["col_max"])

        patch = hypercube[row_min : row_max + 1, col_min : col_max + 1, :]
        valid_values = _valid_feature_values(patch)
        anomaly_patch = anomaly[row_min : row_max + 1, col_min : col_max + 1]
        finite_anomaly = anomaly_patch[np.isfinite(anomaly_patch)]

        mean_signal = float(valid_values.mean()) if valid_values.size else 0.0
        peak_signal = float(finite_anomaly.max()) if finite_anomaly.size else 0.0
        spread_signal = float(valid_values.std()) if valid_values.size else 0.0
        feature_vector = NeutralFeatureVector(
            signal_mean=_normalize_feature(mean_signal),
            signal_peak=_normalize_feature(peak_signal),
            signal_spread=_normalize_feature(spread_signal),
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
        "run_id": inputs.run_id,
        "object_count": len(classifications),
        "cluster_count": len(inputs.cluster_rows),
        "class_counts": dict(sorted(counts.items())),
        "classifier_version": classifications[0]["classifier_version"] if classifications else "experimental_v1",
    }
    return classifications, summary


def _normalize_feature(value: float) -> float:
    return max(0.0, min(1.0, round(float(value), 6)))

def main() -> int:
    args = build_parser().parse_args()
    return asyncio.run(run_cli(run_id=args.run_id))


if __name__ == "__main__":
    raise SystemExit(main())

