from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image

from app.db.models.enums import ArtifactClass
from app.errors import StageError
from app.pipeline._base import ParityCategory, Stage, StageContext, StageResult, build_stage_artifact
from app.pipeline.qa_paths import ensure_run_qa_dir
from app.pipeline.stages.dem import raster_sidecar_path, write_raster_sidecar
from app.pipeline.stages.grid import GridSpec
from app.pipeline.stages.hypercube import HYPERCUBE_NPY_NAME

PCA_ANOMALY_TIF_NAME = "pca_anomaly.tif"
PCA_REPORT_NAME = "pca_eigenvalues.json"
PCA_PARITY_QA_NAME = "parity_qa_summary.json"
PCA_SAMPLE_SEED = 0
PCA_MAX_FIT_PIXELS = 120000
PCA_COMPONENTS = 3
PCA_MIN_FEATURE_STD = 1e-9
PCA_RAW_SCORE_NPY_NAME = "pca_anomaly_raw.npy"


def load_hypercube_array(run_dir: Path) -> np.ndarray:
    hypercube_path = run_dir / HYPERCUBE_NPY_NAME
    if not hypercube_path.is_file():
        raise StageError("Hypercube stage output is required before PCA anomaly.")
    return np.load(hypercube_path).astype(np.float32)


def robust_channel_fill_and_clip(cube_in: np.ndarray, *, p_low: float = 1.0, p_high: float = 99.0) -> np.ndarray:
    cube_out = cube_in.copy().astype(np.float32)
    _height, _width, channels = cube_out.shape
    for index in range(channels):
        channel = cube_out[:, :, index]
        good = np.isfinite(channel)
        if good.any():
            median = np.median(channel[good]).astype(np.float32)
            channel[~good] = median
            low, high = np.percentile(channel, [p_low, p_high])
            if np.isfinite(low) and np.isfinite(high) and high > low:
                channel = np.clip(channel, low, high).astype(np.float32)
        else:
            channel[:] = 0.0
        cube_out[:, :, index] = channel
    return cube_out.astype(np.float32)


def _fit_pca_components(
    fit_matrix: np.ndarray,
    *,
    n_components: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    mean = fit_matrix.mean(axis=0, dtype=np.float64)
    centered = fit_matrix - mean
    _u, singular_values, vt = np.linalg.svd(centered, full_matrices=False)
    actual_components = min(n_components, vt.shape[0])
    components = vt[:actual_components].astype(np.float32)
    explained_variance = ((singular_values[:actual_components] ** 2) / max(fit_matrix.shape[0] - 1, 1)).astype(np.float32)
    total_variance = float(np.var(fit_matrix, axis=0, ddof=1).sum()) if fit_matrix.shape[0] > 1 else float(explained_variance.sum())
    explained_ratio = (explained_variance / max(total_variance, 1e-12)).astype(np.float32)
    return mean.astype(np.float32), components, explained_variance, explained_ratio


def compute_pca_anomaly(
    cube: np.ndarray,
    *,
    nodata: float,
    seed: int = PCA_SAMPLE_SEED,
    max_fit_pixels: int = PCA_MAX_FIT_PIXELS,
    n_components: int = PCA_COMPONENTS,
    valid_mask_channel: bool | None = None,
    return_raw_score: bool = False,
) -> tuple[np.ndarray, dict[str, object]] | tuple[np.ndarray, np.ndarray, dict[str, object]]:
    if cube.ndim != 3:
        raise StageError(f"Hypercube must be HWC 3D, got shape {cube.shape}.")

    cube_float = cube.astype(np.float32, copy=True)
    cube_float[cube_float == nodata] = np.nan
    cube_float[~np.isfinite(cube_float)] = np.nan
    feature_cube, support_mask, used_valid_mask_channel = _split_feature_cube_and_valid_mask(
        cube_float,
        valid_mask_channel=valid_mask_channel,
    )
    if feature_cube.shape[-1] == 0:
        raise StageError("PCA anomaly requires at least one feature channel after support-mask removal.")

    input_feature_channel_count = int(feature_cube.shape[-1])
    selected_feature_cube, included_feature_channels, excluded_feature_channels = _select_pca_feature_channels(
        feature_cube,
        support_mask,
    )
    valid_mask = support_mask & np.isfinite(selected_feature_cube).all(axis=-1)

    cube_clean = robust_channel_fill_and_clip(selected_feature_cube, p_low=1.0, p_high=99.0)

    height, width, channels = cube_clean.shape
    matrix = cube_clean.reshape(-1, channels).astype(np.float32)
    valid_flat = valid_mask.reshape(-1)
    valid_indexes = np.flatnonzero(valid_flat)
    if valid_indexes.size == 0:
        raise StageError("PCA anomaly requires at least one valid selected hypercube pixel.")
    sample_size = min(max_fit_pixels, int(valid_indexes.size))
    rng = np.random.default_rng(seed)
    sample_idx = rng.choice(valid_indexes, size=sample_size, replace=False)
    fit_matrix = matrix[sample_idx]

    actual_components = min(n_components, channels, sample_size)
    mean, components, explained_variance, explained_ratio = _fit_pca_components(fit_matrix, n_components=actual_components)
    projected = (matrix - mean) @ components.T
    magnitude_raw = np.sqrt(np.sum(projected**2, axis=1)).reshape(height, width).astype(np.float32)
    raw_score = np.full((height, width), nodata, dtype=np.float32)
    raw_valid_mask = valid_mask & np.isfinite(magnitude_raw)
    raw_score[raw_valid_mask] = magnitude_raw[raw_valid_mask]
    raw_score_valid = raw_score[(raw_score != nodata) & np.isfinite(raw_score)]

    p01, p99 = np.percentile(raw_score_valid, [1, 99]) if raw_score_valid.size else (0.0, 1.0)
    if not np.isfinite(p01) or not np.isfinite(p99) or p99 <= p01:
        p01 = float(np.nanmin(raw_score_valid)) if raw_score_valid.size else 0.0
        p99 = float(np.nanmax(raw_score_valid)) if raw_score_valid.size else 1.0
    anomaly = np.full((height, width), nodata, dtype=np.float32)
    anomaly_valid = np.clip((magnitude_raw - p01) / (p99 - p01 + 1e-12), 0.0, 1.0).astype(np.float32)
    anomaly[raw_valid_mask] = anomaly_valid[raw_valid_mask]

    report = {
        "seed": int(seed),
        "sample_size": int(sample_size),
        "pixel_count": int(matrix.shape[0]),
        "valid_pixel_count": int(valid_indexes.size),
        "components_count": int(components.shape[0]),
        "input_feature_channel_count": int(input_feature_channel_count),
        "feature_channel_count": int(channels),
        "excluded_feature_channel_count": int(len(excluded_feature_channels)),
        "included_feature_channels": included_feature_channels,
        "excluded_feature_channels": excluded_feature_channels,
        "used_valid_mask_channel": bool(used_valid_mask_channel),
        "valid_mask_policy": "last_binary_channel_excluded_from_features" if used_valid_mask_channel else "finite_selected_feature_channels_after_degenerate_exclusion",
        "pca_feature_policy": "exclude_valid_mask_all_nodata_and_near_constant_channels",
        "eigenvalues": [float(value) for value in explained_variance],
        "explained_variance": [float(value) for value in explained_variance],
        "explained_variance_ratio": [float(value) for value in explained_ratio],
        "mean_vector_length": int(mean.shape[0]),
        "percentile_range": {"p01": float(p01), "p99": float(p99)},
        "raw_score_method": "pca_projected_component_magnitude",
        "display_stretch_method": "percentile_1_99_on_valid_raw_score",
        "raw_score_range": {
            "min": float(raw_score_valid.min()) if raw_score_valid.size else None,
            "max": float(raw_score_valid.max()) if raw_score_valid.size else None,
            "mean": float(raw_score_valid.mean()) if raw_score_valid.size else None,
        },
    }
    if return_raw_score:
        return anomaly, raw_score, report
    return anomaly, report


def _split_feature_cube_and_valid_mask(
    cube: np.ndarray,
    *,
    valid_mask_channel: bool | None,
) -> tuple[np.ndarray, np.ndarray, bool]:
    use_last_channel = _looks_like_valid_mask(cube[:, :, -1]) if valid_mask_channel is None else bool(valid_mask_channel)
    if use_last_channel and cube.shape[-1] > 1:
        feature_cube = cube[:, :, :-1]
        support_mask = (cube[:, :, -1] > 0.5) & np.isfinite(cube[:, :, -1])
        return feature_cube, support_mask.astype(bool), True
    support_mask = np.ones(cube.shape[:2], dtype=bool)
    return cube, support_mask, False


def _select_pca_feature_channels(
    feature_cube: np.ndarray,
    support_mask: np.ndarray,
) -> tuple[np.ndarray, list[int], list[dict[str, object]]]:
    included: list[int] = []
    excluded: list[dict[str, object]] = []
    for channel_index in range(feature_cube.shape[-1]):
        channel = feature_cube[:, :, channel_index]
        values = channel[support_mask]
        finite_values = values[np.isfinite(values)]
        if finite_values.size == 0:
            excluded.append(
                {
                    "channel_index": int(channel_index),
                    "reason": "no_finite_values",
                    "valid_value_count": 0,
                }
            )
            continue
        channel_std = float(np.nanstd(finite_values))
        if not np.isfinite(channel_std) or channel_std <= PCA_MIN_FEATURE_STD:
            excluded.append(
                {
                    "channel_index": int(channel_index),
                    "reason": "near_constant",
                    "valid_value_count": int(finite_values.size),
                    "std": channel_std,
                }
            )
            continue
        included.append(int(channel_index))

    if not included:
        raise StageError("PCA anomaly requires at least one non-degenerate feature channel.")
    return feature_cube[:, :, included], included, excluded


def _looks_like_valid_mask(channel: np.ndarray) -> bool:
    finite = channel[np.isfinite(channel)]
    if finite.size == 0:
        return False
    is_binary = np.isclose(finite, 0.0, atol=1e-6) | np.isclose(finite, 1.0, atol=1e-6)
    return bool(is_binary.all())


def write_pca_outputs(
    run_dir: Path,
    grid_spec: GridSpec,
    anomaly: np.ndarray,
    raw_score: np.ndarray,
    report: dict[str, object],
) -> dict[str, Path]:
    tif_path = run_dir / PCA_ANOMALY_TIF_NAME
    raw_score_path = run_dir / PCA_RAW_SCORE_NPY_NAME
    report_path = run_dir / PCA_REPORT_NAME
    qa_path = ensure_run_qa_dir(run_dir) / "parity" / PCA_PARITY_QA_NAME
    qa_path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(anomaly.astype(np.float32)).save(tif_path, format="TIFF")
    write_raster_sidecar(
        tif_path,
        grid_manifest=grid_spec.manifest,
        nodata=grid_spec.nodata,
        dtype="float32",
        shape=anomaly.shape,
    )
    np.save(raw_score_path, raw_score.astype(np.float32, copy=False))
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    valid_anomaly = anomaly[(anomaly != grid_spec.nodata) & np.isfinite(anomaly)]
    qa_payload = {
        "stage": "pca_anomaly",
        "seed": int(report["seed"]),
        "sample_size": int(report["sample_size"]),
        "components_count": int(report["components_count"]),
        "input_feature_channel_count": int(report.get("input_feature_channel_count", report["feature_channel_count"])),
        "feature_channel_count": int(report["feature_channel_count"]),
        "excluded_feature_channel_count": int(report.get("excluded_feature_channel_count", 0)),
        "used_valid_mask_channel": bool(report["used_valid_mask_channel"]),
        "valid_mask_policy": str(report["valid_mask_policy"]),
        "pca_feature_policy": str(report.get("pca_feature_policy", "legacy")),
        "raw_score_method": str(report.get("raw_score_method", "legacy_projected_magnitude")),
        "display_stretch_method": str(report.get("display_stretch_method", "legacy_percentile_display")),
        "raw_score_range": report.get("raw_score_range"),
        "pixel_count": int(report["pixel_count"]),
        "valid_pixel_count": int(report["valid_pixel_count"]),
        "anomaly_min": float(valid_anomaly.min()) if valid_anomaly.size else None,
        "anomaly_max": float(valid_anomaly.max()) if valid_anomaly.size else None,
        "anomaly_mean": float(valid_anomaly.mean()) if valid_anomaly.size else None,
    }
    qa_path.write_text(json.dumps(qa_payload, indent=2, sort_keys=True), encoding="utf-8")
    return {
        "pca_anomaly_tif": tif_path,
        "pca_anomaly_raw_npy": raw_score_path,
        "pca_report": report_path,
        "parity_qa_summary": qa_path,
    }


class PcaAnomalyStage(Stage):
    name = "pca_anomaly"
    parity_category = ParityCategory.PARITY_REPRODUCES

    def __init__(self, *, grid_spec: GridSpec, seed: int = PCA_SAMPLE_SEED) -> None:
        self.grid_spec = grid_spec
        self.seed = seed

    async def run(self, context: StageContext) -> StageResult:
        cube = load_hypercube_array(context.run_dir)
        anomaly, raw_score, report = compute_pca_anomaly(
            cube,
            nodata=self.grid_spec.nodata,
            seed=self.seed,
            return_raw_score=True,
        )
        outputs = write_pca_outputs(context.run_dir, self.grid_spec, anomaly, raw_score, report)
        artifacts = [
            build_stage_artifact(
                name="pca_anomaly_tif",
                relative_path=outputs["pca_anomaly_tif"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.LOCAL_SENSITIVE,
                size_bytes=outputs["pca_anomaly_tif"].stat().st_size,
            ),
            build_stage_artifact(
                name="pca_anomaly_raw_npy",
                relative_path=outputs["pca_anomaly_raw_npy"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.LOCAL_SENSITIVE,
                size_bytes=outputs["pca_anomaly_raw_npy"].stat().st_size,
            ),
            build_stage_artifact(
                name="pca_eigenvalues",
                relative_path=outputs["pca_report"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.LOCAL_SENSITIVE,
                size_bytes=outputs["pca_report"].stat().st_size,
            ),
            build_stage_artifact(
                name="parity_qa_summary",
                relative_path=outputs["parity_qa_summary"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=outputs["parity_qa_summary"].stat().st_size,
                http_servable=False,
            ),
        ]
        return StageResult(artifacts=artifacts, metadata=report)
