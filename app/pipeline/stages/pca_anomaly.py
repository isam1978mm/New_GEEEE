from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image

from app.db.models.enums import ArtifactClass
from app.errors import StageError
from app.pipeline._base import ParityCategory, Stage, StageContext, StageResult, build_stage_artifact
from app.pipeline.stages.dem import raster_sidecar_path, write_raster_sidecar
from app.pipeline.stages.grid import GridSpec
from app.pipeline.stages.hypercube import HYPERCUBE_NPY_NAME

PCA_ANOMALY_TIF_NAME = "pca_anomaly.tif"
PCA_REPORT_NAME = "pca_eigenvalues.json"
PCA_SAMPLE_SEED = 0
PCA_MAX_FIT_PIXELS = 120000
PCA_COMPONENTS = 3


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
    components = vt[:n_components].astype(np.float32)
    explained_variance = ((singular_values[:n_components] ** 2) / max(fit_matrix.shape[0] - 1, 1)).astype(np.float32)
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
) -> tuple[np.ndarray, dict[str, object]]:
    if cube.ndim != 3:
        raise StageError(f"Hypercube must be HWC 3D, got shape {cube.shape}.")

    cube_float = cube.astype(np.float32, copy=True)
    cube_float[cube_float == nodata] = np.nan
    cube_float[~np.isfinite(cube_float)] = np.nan
    cube_clean = robust_channel_fill_and_clip(cube_float, p_low=1.0, p_high=99.0)

    height, width, channels = cube_clean.shape
    matrix = cube_clean.reshape(-1, channels).astype(np.float32)
    pixel_count = matrix.shape[0]
    sample_size = min(max_fit_pixels, pixel_count)
    rng = np.random.default_rng(seed)
    sample_idx = rng.choice(pixel_count, size=sample_size, replace=False)
    fit_matrix = matrix[sample_idx]

    mean, components, explained_variance, explained_ratio = _fit_pca_components(fit_matrix, n_components=n_components)
    projected = (matrix - mean) @ components.T
    pc1 = projected[:, 0].reshape(height, width).astype(np.float32)
    pc2 = projected[:, 1].reshape(height, width).astype(np.float32)
    pc3 = projected[:, 2].reshape(height, width).astype(np.float32)

    magnitude_raw = np.sqrt(pc1**2 + pc2**2 + pc3**2).astype(np.float32)
    finite = magnitude_raw[np.isfinite(magnitude_raw)]
    p01, p99 = np.percentile(finite, [1, 99]) if finite.size else (0.0, 1.0)
    if not np.isfinite(p01) or not np.isfinite(p99) or p99 <= p01:
        p01 = float(np.nanmin(magnitude_raw))
        p99 = float(np.nanmax(magnitude_raw))
    anomaly = np.clip((magnitude_raw - p01) / (p99 - p01 + 1e-12), 0.0, 1.0).astype(np.float32)

    report = {
        "seed": int(seed),
        "sample_size": int(sample_size),
        "pixel_count": int(pixel_count),
        "components_count": int(n_components),
        "eigenvalues": [float(value) for value in explained_variance],
        "explained_variance": [float(value) for value in explained_variance],
        "explained_variance_ratio": [float(value) for value in explained_ratio],
        "mean_vector_length": int(mean.shape[0]),
        "percentile_range": {"p01": float(p01), "p99": float(p99)},
    }
    return anomaly, report


def write_pca_outputs(run_dir: Path, grid_spec: GridSpec, anomaly: np.ndarray, report: dict[str, object]) -> dict[str, Path]:
    tif_path = run_dir / PCA_ANOMALY_TIF_NAME
    report_path = run_dir / PCA_REPORT_NAME
    Image.fromarray(anomaly.astype(np.float32)).save(tif_path, format="TIFF")
    write_raster_sidecar(
        tif_path,
        grid_manifest=grid_spec.manifest,
        nodata=grid_spec.nodata,
        dtype="float32",
        shape=anomaly.shape,
    )
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    return {"pca_anomaly_tif": tif_path, "pca_report": report_path}


class PcaAnomalyStage(Stage):
    name = "pca_anomaly"
    parity_category = ParityCategory.PARITY_REPRODUCES

    def __init__(self, *, grid_spec: GridSpec, seed: int = PCA_SAMPLE_SEED) -> None:
        self.grid_spec = grid_spec
        self.seed = seed

    async def run(self, context: StageContext) -> StageResult:
        cube = load_hypercube_array(context.run_dir)
        anomaly, report = compute_pca_anomaly(cube, nodata=self.grid_spec.nodata, seed=self.seed)
        outputs = write_pca_outputs(context.run_dir, self.grid_spec, anomaly, report)
        artifacts = [
            build_stage_artifact(
                name="pca_anomaly_tif",
                relative_path=outputs["pca_anomaly_tif"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.LOCAL_SENSITIVE,
                size_bytes=outputs["pca_anomaly_tif"].stat().st_size,
            ),
            build_stage_artifact(
                name="pca_eigenvalues",
                relative_path=outputs["pca_report"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.LOCAL_SENSITIVE,
                size_bytes=outputs["pca_report"].stat().st_size,
            ),
        ]
        return StageResult(
            artifacts=artifacts,
            metadata={
                "seed": self.seed,
                "explained_variance_ratio": report["explained_variance_ratio"],
                "shape": [self.grid_spec.size, self.grid_spec.size],
            },
        )
