"""Secret layers stage: AI_READY_640_Secret_* raster generation.

Computes the six notebook secret layers that feed the FINAL_TESLA_V7_2_HYPERCUBE.
Each layer is implemented only when exact source-equivalent inputs are available
from previously-persisted pipeline outputs.

Layers with missing source bands are recorded as not_implemented_no_source_equivalent.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from app.db.models.enums import ArtifactClass
from app.errors import StageError
from app.pipeline._base import ParityCategory, Stage, StageContext, StageResult, build_stage_artifact
from app.pipeline.qa_paths import ensure_run_qa_dir
from app.pipeline.stages.dem import write_georeferenced_raster, write_raster_sidecar
from app.pipeline.stages.dem_derivatives import box_mean_nanaware
from app.pipeline.stages.grid import GridSpec
from app.pipeline.stages.s2_indices import S2_SOURCE_BANDS, S2_RAW_CUBE_NPY_NAME
from app.pipeline.stages.thermal import LST_TIF_NAME

EPS = 1e-10
SECRET_LAYER_OUTPUT_DIR = "AI_READY_640"

# Band index mapping within the raw S2 cube: (B2, B3, B4, B8, B11, B12, B1)
_S2_BAND_INDEX = {name: index for index, name in enumerate(S2_SOURCE_BANDS)}

# --- Layer definitions -------------------------------------------------------

SECRET_LAYER_SPECS = [
    {
        "name": "AI_READY_640_Secret_Gold_Halo",
        "formula": "B12 / (B8 + eps)",
        "source_type": "s2_raw",
        "inputs": ["B12", "B8"],
    },
    {
        "name": "AI_READY_640_Secret_Silver_Oxide",
        "formula": "B2 / (B1 + eps)",
        "source_type": "s2_raw",
        "inputs": ["B2", "B1"],
    },
    {
        "name": "AI_READY_640_Secret_Tunnel_Ceiling",
        "formula": "B8 - B4",
        "source_type": "s2_raw",
        "inputs": ["B8", "B4"],
    },
    {
        "name": "AI_READY_640_Secret_Thermal_Inertia",
        "formula": "l9_col / focal_mean(l9_col, 500m)",
        "source_type": "thermal",
        "inputs": ["lst"],
    },
    {
        "name": "AI_READY_640_Secret_Chemical_Protector",
        "formula": "B1 / (B11 + eps)",
        "source_type": "s2_raw",
        "inputs": ["B1", "B11"],
    },
    {
        "name": "AI_READY_640_Secret_Hidden_Doors",
        "formula": "hillshade(315,35) - hillshade(135,35)",
        "source_type": "dem",
        "inputs": ["dem"],
    },
]

# --- Hillshade (parameterized azimuth/altitude) ------------------------------


def compute_hillshade_parameterized(
    dem: np.ndarray, *, nodata: float, scale_m: float, azimuth_deg: float, altitude_deg: float
) -> np.ndarray:
    """Compute hillshade for arbitrary sun azimuth and altitude (in degrees)."""
    dem_float = dem.astype(np.float32, copy=True)
    dem_float = np.where(dem_float == nodata, np.nan, dem_float)
    source_valid = np.isfinite(dem_float)
    dz_dy, dz_dx = np.gradient(dem_float, scale_m, scale_m)
    slope_rad = np.arctan(np.sqrt(dz_dx**2 + dz_dy**2))
    aspect_rad = np.arctan2(-dz_dx, dz_dy)
    azimuth_rad = np.deg2rad(azimuth_deg)
    altitude_rad = np.deg2rad(altitude_deg)
    hillshade = (
        np.sin(altitude_rad) * np.cos(slope_rad)
        + np.cos(altitude_rad) * np.sin(slope_rad) * np.cos(azimuth_rad - aspect_rad)
    )
    hillshade = np.clip(hillshade, 0.0, 1.0).astype(np.float32)
    hillshade[~source_valid] = nodata
    hillshade[~np.isfinite(hillshade)] = nodata
    return hillshade.astype(np.float32, copy=False)


# --- Layer computation -------------------------------------------------------


def _check_source_available(spec: dict, available_s2_bands: set[str]) -> tuple[bool, str]:
    """Return (is_available, reason) for a layer spec."""
    if spec["source_type"] == "s2_raw":
        missing = [band for band in spec["inputs"] if band not in available_s2_bands]
        if missing:
            return False, f"Raw S2 band(s) {', '.join(missing)} not available in app S2_SOURCE_BANDS {sorted(available_s2_bands)}"
        return True, ""
    # thermal and dem are always available if the stage ran
    return True, ""


def compute_secret_gold_halo(s2_cube: np.ndarray, *, nodata: float) -> np.ndarray:
    """B12 / (B8 + eps)"""
    b12 = s2_cube[:, :, _S2_BAND_INDEX["B12"]]
    b8 = s2_cube[:, :, _S2_BAND_INDEX["B8"]]
    valid = (b12 != nodata) & (b8 != nodata) & np.isfinite(b12) & np.isfinite(b8)
    result = np.full(b12.shape, nodata, dtype=np.float32)
    result[valid] = (b12[valid] / (b8[valid] + EPS)).astype(np.float32)
    return result


def compute_secret_silver_oxide(s2_cube: np.ndarray, *, nodata: float) -> np.ndarray:
    """B2 / (B1 + eps)"""
    b2 = s2_cube[:, :, _S2_BAND_INDEX["B2"]]
    b1 = s2_cube[:, :, _S2_BAND_INDEX["B1"]]
    valid = (b2 != nodata) & (b1 != nodata) & np.isfinite(b2) & np.isfinite(b1)
    result = np.full(b2.shape, nodata, dtype=np.float32)
    result[valid] = (b2[valid] / (b1[valid] + EPS)).astype(np.float32)
    return result


def compute_secret_chemical_protector(s2_cube: np.ndarray, *, nodata: float) -> np.ndarray:
    """B1 / (B11 + eps)"""
    b1 = s2_cube[:, :, _S2_BAND_INDEX["B1"]]
    b11 = s2_cube[:, :, _S2_BAND_INDEX["B11"]]
    valid = (b1 != nodata) & (b11 != nodata) & np.isfinite(b1) & np.isfinite(b11)
    result = np.full(b1.shape, nodata, dtype=np.float32)
    result[valid] = (b1[valid] / (b11[valid] + EPS)).astype(np.float32)
    return result


def compute_secret_tunnel_ceiling(s2_cube: np.ndarray, *, nodata: float) -> np.ndarray:
    """B8 - B4"""
    b8 = s2_cube[:, :, _S2_BAND_INDEX["B8"]]
    b4 = s2_cube[:, :, _S2_BAND_INDEX["B4"]]
    valid = (b8 != nodata) & (b4 != nodata) & np.isfinite(b8) & np.isfinite(b4)
    result = np.full(b8.shape, nodata, dtype=np.float32)
    result[valid] = (b8[valid] - b4[valid]).astype(np.float32)
    return result


def compute_secret_thermal_inertia(
    lst: np.ndarray, *, nodata: float, scale_m: float
) -> np.ndarray:
    """l9_col / focal_mean(l9_col, 500m)"""
    lst_float = lst.astype(np.float32, copy=True)
    lst_float = np.where(lst_float == nodata, np.nan, lst_float)
    # 500m focal mean radius in pixels
    radius_px = max(1, int(round(500.0 / scale_m)))
    focal_mean = box_mean_nanaware(lst_float, radius_px)
    source_valid = np.isfinite(lst_float) & np.isfinite(focal_mean) & (focal_mean != 0.0)
    result = np.full(lst.shape, nodata, dtype=np.float32)
    result[source_valid] = (lst_float[source_valid] / focal_mean[source_valid]).astype(np.float32)
    return result


def compute_secret_hidden_doors(
    dem: np.ndarray, *, nodata: float, scale_m: float
) -> np.ndarray:
    """hillshade(315,35) - hillshade(135,35)"""
    hs_315 = compute_hillshade_parameterized(dem, nodata=nodata, scale_m=scale_m, azimuth_deg=315.0, altitude_deg=35.0)
    hs_135 = compute_hillshade_parameterized(dem, nodata=nodata, scale_m=scale_m, azimuth_deg=135.0, altitude_deg=35.0)
    valid = (hs_315 != nodata) & (hs_135 != nodata) & np.isfinite(hs_315) & np.isfinite(hs_135)
    result = np.full(dem.shape[:2], nodata, dtype=np.float32)
    result[valid] = (hs_315[valid] - hs_135[valid]).astype(np.float32)
    return result


# --- Source loading -----------------------------------------------------------


def load_s2_raw_cube(run_dir: Path) -> np.ndarray:
    """Load the raw S2 band cube persisted by the S2 indices stage."""
    path = run_dir / S2_RAW_CUBE_NPY_NAME
    if not path.is_file():
        raise StageError("S2 raw band cube is required before secret layers stage.")
    return np.load(path)


def load_dem_array(run_dir: Path) -> np.ndarray:
    """Load the DEM array persisted by the DEM stage."""
    path = run_dir / "dem.npy"
    if not path.is_file():
        raise StageError("DEM stage output is required before secret layers stage.")
    return np.load(path)


def load_lst_array(run_dir: Path, *, nodata: float) -> np.ndarray:
    """Load the LST raster persisted by the thermal stage."""
    from PIL import Image

    path = run_dir / LST_TIF_NAME
    if not path.is_file():
        raise StageError("Thermal stage output is required before secret layers stage.")
    with Image.open(path) as image:
        return np.array(image, dtype=np.float32)


# --- Output writing -----------------------------------------------------------


def write_secret_layer_output(
    run_dir: Path, grid_spec: GridSpec, name: str, array: np.ndarray
) -> Path:
    """Write a single secret layer as a georeferenced GeoTIFF under AI_READY_640/."""
    output_dir = run_dir / SECRET_LAYER_OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    tif_path = output_dir / f"{name}.tif"
    write_georeferenced_raster(tif_path, array, grid_spec)
    write_raster_sidecar(
        tif_path,
        grid_manifest=grid_spec.manifest,
        nodata=grid_spec.nodata,
        dtype="float32",
        shape=array.shape[:2],
    )
    return tif_path


def write_secret_layers_manifest(
    run_dir: Path,
    *,
    implemented: list[dict],
    not_implemented: list[dict],
) -> Path:
    """Write a manifest documenting secret layer status."""
    qa_dir = ensure_run_qa_dir(run_dir) / "stacks"
    qa_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = qa_dir / "secret_layers_manifest.json"
    payload = {
        "schema": "secret_layers_manifest_v1",
        "stage": "secret_layers",
        "layer_count": len(SECRET_LAYER_SPECS),
        "implemented_count": len(implemented),
        "not_implemented_count": len(not_implemented),
        "implemented": implemented,
        "not_implemented": not_implemented,
    }
    manifest_path.write_text(
        json.dumps(payload, indent=2, sort_keys=False),
        encoding="utf-8",
    )
    return manifest_path


# --- Stage class --------------------------------------------------------------


class SecretLayersStage(Stage):
    """Compute AI_READY_640_Secret_* layers from persisted pipeline outputs."""

    name = "secret_layers"
    parity_category = ParityCategory.PARITY_REPRODUCES

    def __init__(self, *, grid_spec: GridSpec) -> None:
        self.grid_spec = grid_spec

    async def run(self, context: StageContext) -> StageResult:
        available_s2_bands = set(S2_SOURCE_BANDS)
        scale_m = float(self.grid_spec.manifest.scale_m)
        nodata = self.grid_spec.nodata

        # Load source data (lazy — only load if needed)
        s2_cube = None
        dem = None
        lst = None

        implemented_specs: list[dict] = []
        not_implemented_specs: list[dict] = []
        artifacts = []
        layer_metadata: dict[str, dict] = {}

        for spec in SECRET_LAYER_SPECS:
            available, reason = _check_source_available(spec, available_s2_bands)
            if not available:
                not_implemented_specs.append({
                    "name": spec["name"],
                    "formula": spec["formula"],
                    "status": "not_implemented_no_source_equivalent",
                    "reason": reason,
                })
                layer_metadata[spec["name"]] = {
                    "status": "not_implemented_no_source_equivalent",
                    "reason": reason,
                }
                continue

            # Compute the layer
            if spec["name"] == "AI_READY_640_Secret_Gold_Halo":
                if s2_cube is None:
                    s2_cube = load_s2_raw_cube(context.run_dir)
                array = compute_secret_gold_halo(s2_cube, nodata=nodata)
            elif spec["name"] == "AI_READY_640_Secret_Silver_Oxide":
                if s2_cube is None:
                    s2_cube = load_s2_raw_cube(context.run_dir)
                array = compute_secret_silver_oxide(s2_cube, nodata=nodata)
            elif spec["name"] == "AI_READY_640_Secret_Tunnel_Ceiling":
                if s2_cube is None:
                    s2_cube = load_s2_raw_cube(context.run_dir)
                array = compute_secret_tunnel_ceiling(s2_cube, nodata=nodata)
            elif spec["name"] == "AI_READY_640_Secret_Thermal_Inertia":
                if lst is None:
                    lst = load_lst_array(context.run_dir, nodata=nodata)
                array = compute_secret_thermal_inertia(lst, nodata=nodata, scale_m=scale_m)
            elif spec["name"] == "AI_READY_640_Secret_Chemical_Protector":
                if s2_cube is None:
                    s2_cube = load_s2_raw_cube(context.run_dir)
                array = compute_secret_chemical_protector(s2_cube, nodata=nodata)
            elif spec["name"] == "AI_READY_640_Secret_Hidden_Doors":
                if dem is None:
                    dem = load_dem_array(context.run_dir)
                array = compute_secret_hidden_doors(dem, nodata=nodata, scale_m=scale_m)
            else:
                # Should not reach here for implemented layers
                continue

            # Validate output shape
            expected_shape = (self.grid_spec.size, self.grid_spec.size)
            if array.shape[:2] != expected_shape:
                raise StageError(
                    f"Secret layer {spec['name']} shape {array.shape[:2]} != expected {expected_shape}"
                )

            tif_path = write_secret_layer_output(
                context.run_dir, self.grid_spec, spec["name"], array
            )
            artifacts.append(
                build_stage_artifact(
                    name=spec["name"],
                    relative_path=tif_path.relative_to(context.run_dir).as_posix(),
                    artifact_class=ArtifactClass.LOCAL_SENSITIVE,
                    size_bytes=tif_path.stat().st_size,
                )
            )
            implemented_specs.append({
                "name": spec["name"],
                "formula": spec["formula"],
                "status": "implemented",
                "source_type": spec["source_type"],
                "inputs": spec["inputs"],
                "output_path": f"{SECRET_LAYER_OUTPUT_DIR}/{spec['name']}.tif",
            })
            layer_metadata[spec["name"]] = {
                "status": "implemented",
                "formula": spec["formula"],
            }

        # Write manifest
        manifest_path = write_secret_layers_manifest(
            context.run_dir,
            implemented=implemented_specs,
            not_implemented=not_implemented_specs,
        )
        artifacts.append(
            build_stage_artifact(
                name="secret_layers_manifest",
                relative_path=manifest_path.relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=manifest_path.stat().st_size,
                http_servable=False,
            )
        )

        return StageResult(
            artifacts=artifacts,
            metadata={
                "implemented_layers": [spec["name"] for spec in implemented_specs],
                "not_implemented_layers": [spec["name"] for spec in not_implemented_specs],
                "layer_details": layer_metadata,
            },
        )
