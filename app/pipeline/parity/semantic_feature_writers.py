from __future__ import annotations

from pathlib import Path
from typing import Mapping

import numpy as np

from app.pipeline.parity import resolve_run_output_path


AI_BEH_RELATION_OUTPUT_NAMES: tuple[str, str, str] = (
    "AI_BEH_VegRoot_REL_ND_DOM_lin_640.tif",
    "AI_BEH_IronOxide_REL_Ratio_DOM_lin_640.tif",
    "AI_BEH_ClayThermal_REL_Ratio_DOM_lin_640.tif",
)

AI_BEH_RELATION_NPY_OUTPUT_NAMES: dict[str, str] = {
    "AI_BEH_VegRoot_REL_ND_DOM_lin_640.tif": "AI_BEH_VegRoot_REL_ND_DOM_lin_640.npy",
    "AI_BEH_IronOxide_REL_Ratio_DOM_lin_640.tif": (
        "AI_BEH_IronOxide_REL_Ratio_DOM_lin_640.npy"
    ),
    "AI_BEH_ClayThermal_REL_Ratio_DOM_lin_640.tif": (
        "AI_BEH_ClayThermal_REL_Ratio_DOM_lin_640.npy"
    ),
}

AI_BEH_RELATION_REQUIRED_BANDS: tuple[str, ...] = ("B3", "B4", "B8", "B11", "B12")

AI_BEH_RELATION_DEFAULT_OUTPUT_DIR = "semantic_features/ai_beh_relation"


def compute_ai_beh_relation_features(
    bands: Mapping[str, object],
    *,
    denominator_epsilon: float = 1e-6,
) -> dict[str, np.ndarray]:
    """Compute the Phase C private AI_BEH relation feature family from 2D bands."""

    arrays = _validated_band_arrays(bands)
    return {
        "AI_BEH_VegRoot_REL_ND_DOM_lin_640.tif": _normalized_difference(
            arrays["B8"],
            arrays["B4"],
            denominator_epsilon=denominator_epsilon,
        ),
        "AI_BEH_IronOxide_REL_Ratio_DOM_lin_640.tif": _safe_divide(
            arrays["B4"],
            arrays["B3"],
            denominator_epsilon=denominator_epsilon,
        ),
        "AI_BEH_ClayThermal_REL_Ratio_DOM_lin_640.tif": _safe_divide(
            arrays["B11"],
            arrays["B12"],
            denominator_epsilon=denominator_epsilon,
        ),
    }


def write_ai_beh_relation_feature_npy_outputs(
    run_dir: str | Path,
    bands: Mapping[str, object],
    *,
    reference_profile: Mapping[str, object] | None = None,
    output_relative_dir: str | Path = AI_BEH_RELATION_DEFAULT_OUTPUT_DIR,
    denominator_epsilon: float = 1e-6,
) -> dict[str, object]:
    """Write private local NPY relation features under ``run_dir`` only."""

    output_dir = resolve_run_output_path(run_dir, output_relative_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    features = compute_ai_beh_relation_features(
        bands,
        denominator_epsilon=denominator_epsilon,
    )

    output_paths: dict[str, str] = {}
    for tif_name in AI_BEH_RELATION_OUTPUT_NAMES:
        npy_name = AI_BEH_RELATION_NPY_OUTPUT_NAMES[tif_name]
        output_path = resolve_run_output_path(run_dir, Path(output_relative_dir) / npy_name)
        np.save(output_path, features[tif_name])
        output_paths[tif_name] = str(output_path)

    return {
        "writer_family": "ai_beh_relation_semantic_features",
        "target_mode": "notebook_parity_private",
        "artifact_class": "LOCAL_SENSITIVE",
        "http_servable": False,
        "runtime_output_verified": True,
        "notebook_value_parity_verified": False,
        "outputs": output_paths,
        "reference_profile": dict(reference_profile or {}),
        "dtype_policy": "float32 with NaN for unsafe division denominators",
        "nodata_policy": "NaN in NPY outputs; frozen references required before TIFF nodata lock",
    }


def _validated_band_arrays(bands: Mapping[str, object]) -> dict[str, np.ndarray]:
    missing = [name for name in AI_BEH_RELATION_REQUIRED_BANDS if name not in bands]
    if missing:
        raise ValueError(f"missing required bands: {', '.join(missing)}")

    arrays = {
        name: np.asarray(bands[name], dtype=np.float64)
        for name in AI_BEH_RELATION_REQUIRED_BANDS
    }

    shapes = {array.shape for array in arrays.values()}
    if any(array.ndim != 2 for array in arrays.values()):
        raise ValueError("AI_BEH relation feature inputs must be 2D raster arrays")
    if len(shapes) != 1:
        raise ValueError("AI_BEH relation feature inputs must share the same 2D shape")

    return arrays


def _safe_divide(
    numerator: np.ndarray,
    denominator: np.ndarray,
    *,
    denominator_epsilon: float,
) -> np.ndarray:
    result = np.full(numerator.shape, np.nan, dtype=np.float64)
    valid = np.abs(denominator) > denominator_epsilon
    np.divide(numerator, denominator, out=result, where=valid)
    return result.astype(np.float32, copy=False)


def _normalized_difference(
    left: np.ndarray,
    right: np.ndarray,
    *,
    denominator_epsilon: float,
) -> np.ndarray:
    denominator = left + right
    numerator = left - right
    return _safe_divide(
        numerator,
        denominator,
        denominator_epsilon=denominator_epsilon,
    )
