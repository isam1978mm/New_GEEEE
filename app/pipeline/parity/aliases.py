from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil

from app.pipeline.parity import (
    ParityManifestEntry,
    ensure_standard_parity_dirs,
    resolve_parity_output_path,
    resolve_run_output_path,
    write_parity_manifest,
)


class AliasSourceMissingError(FileNotFoundError):
    """Raised when no configured app-native source exists for an alias."""


@dataclass(frozen=True)
class AliasSpec:
    id: str
    source_paths: tuple[str, ...]
    parity_path: str
    notebook_name_or_pattern: str
    family: str
    classification: str = "notebook-parity"
    target_mode: str = "notebook_parity"
    artifact_class: str = "LOCAL_SENSITIVE"
    http_servable: bool = False
    requires_coordinates: bool = False
    probability_only_required: bool = False
    notebook_value_parity_verified: bool = False
    notes: str = (
        "Phase 3 notebook-parity alias copied from an existing app-native output; "
        "notebook-value parity requires later reference comparison."
    )


@dataclass(frozen=True)
class AliasPlan:
    spec: AliasSpec
    source_path: Path
    parity_path: Path
    source_run_path: str
    parity_run_path: str
    entry: ParityManifestEntry


@dataclass(frozen=True)
class AliasCopyResult:
    status: str
    plan: AliasPlan
    entry: ParityManifestEntry
    manifest_path: Path


DEFAULT_RASTER_TENSOR_ALIAS_SPECS = (
    AliasSpec(
        id="dem_640",
        source_paths=("dem.tif",),
        parity_path="DEM_GEO8_TIFS/DEM_640.tif",
        notebook_name_or_pattern="DEM_640.tif",
        family="DEM/terrain outputs",
    ),
    AliasSpec(
        id="slope_deg_640",
        source_paths=("slope.tif",),
        parity_path="DEM_GEO8_TIFS/slope_deg_640.tif",
        notebook_name_or_pattern="slope_deg_640.tif",
        family="DEM/terrain outputs",
    ),
    AliasSpec(
        id="aspect_deg_640",
        source_paths=("aspect.tif",),
        parity_path="DEM_GEO8_TIFS/aspect_deg_640.tif",
        notebook_name_or_pattern="aspect_deg_640.tif",
        family="DEM/terrain outputs",
    ),
    AliasSpec(
        id="roughness_100m_640",
        source_paths=("roughness.tif",),
        parity_path="DEM_GEO8_TIFS/roughness_100m_640.tif",
        notebook_name_or_pattern="roughness_100m_640.tif",
        family="DEM/terrain outputs",
    ),
    AliasSpec(
        id="tpi_100m_640",
        source_paths=("TPI.tif",),
        parity_path="DEM_GEO8_TIFS/tpi_100m_640.tif",
        notebook_name_or_pattern="tpi_100m_640.tif",
        family="DEM/terrain outputs",
    ),
    AliasSpec(
        id="hillshade_0to1_640",
        source_paths=("hillshade.tif", "DEM_GEO8_TIFS/hillshade_0to1_640.tif"),
        parity_path="DEM_GEO8_TIFS/hillshade_0to1_640.tif",
        notebook_name_or_pattern="hillshade_0to1_640.tif",
        family="DEM/terrain outputs",
    ),
    AliasSpec(
        id="radar_vv_db_tif",
        source_paths=("VV_dB.tif",),
        parity_path="GEOTIFF_RADAR_BANDS/RADAR_VV_dB_640_app.tif",
        notebook_name_or_pattern="RADAR_VV_dB_640_app.tif",
        family="SAR/radar outputs",
    ),
    AliasSpec(
        id="radar_vh_db_tif",
        source_paths=("VH_dB.tif",),
        parity_path="GEOTIFF_RADAR_BANDS/RADAR_VH_dB_640_app.tif",
        notebook_name_or_pattern="RADAR_VH_dB_640_app.tif",
        family="SAR/radar outputs",
    ),
    AliasSpec(
        id="radar_logratio_db_tif",
        source_paths=("logRatio_dB.tif",),
        parity_path="GEOTIFF_RADAR_BANDS/RADAR_logRatio_dB_640_app.tif",
        notebook_name_or_pattern="RADAR_logRatio_dB_640_app.tif",
        family="SAR/radar outputs",
    ),
    AliasSpec(
        id="radar_angle_tif",
        source_paths=("incidence.tif",),
        parity_path="GEOTIFF_RADAR_BANDS/RADAR_angle_640_app.tif",
        notebook_name_or_pattern="RADAR_angle_640_app.tif",
        family="SAR/radar outputs",
    ),
    AliasSpec(
        id="radar_vv_db_npy",
        source_paths=("npy_radar_bands/VV_dB.npy",),
        parity_path="NPY_RADAR_BANDS/RADAR_VV_dB_640_app.npy",
        notebook_name_or_pattern="RADAR_VV_dB_640_app.npy",
        family="SAR/radar outputs",
        artifact_class="FILESYSTEM_ONLY",
    ),
    AliasSpec(
        id="radar_vh_db_npy",
        source_paths=("npy_radar_bands/VH_dB.npy",),
        parity_path="NPY_RADAR_BANDS/RADAR_VH_dB_640_app.npy",
        notebook_name_or_pattern="RADAR_VH_dB_640_app.npy",
        family="SAR/radar outputs",
        artifact_class="FILESYSTEM_ONLY",
    ),
    AliasSpec(
        id="radar_logratio_db_npy",
        source_paths=("npy_radar_bands/logRatio_dB.npy",),
        parity_path="NPY_RADAR_BANDS/RADAR_logRatio_dB_640_app.npy",
        notebook_name_or_pattern="RADAR_logRatio_dB_640_app.npy",
        family="SAR/radar outputs",
        artifact_class="FILESYSTEM_ONLY",
    ),
    AliasSpec(
        id="radar_angle_npy",
        source_paths=("npy_radar_bands/incidence.npy",),
        parity_path="NPY_RADAR_BANDS/RADAR_angle_640_app.npy",
        notebook_name_or_pattern="RADAR_angle_640_app.npy",
        family="SAR/radar outputs",
        artifact_class="FILESYSTEM_ONLY",
    ),
    AliasSpec(
        id="hypercube_tif",
        source_paths=("hypercube.tif",),
        parity_path="NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE.tif",
        notebook_name_or_pattern="FINAL_TESLA_V7_2_HYPERCUBE.tif",
        family="hypercube/tensor outputs",
    ),
    AliasSpec(
        id="hypercube_npy",
        source_paths=("hypercube.npy",),
        parity_path="NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE.npy",
        notebook_name_or_pattern="FINAL_TESLA_V7_2_HYPERCUBE.npy",
        family="hypercube/tensor outputs",
        artifact_class="FILESYSTEM_ONLY",
    ),
    AliasSpec(
        id="hypercube_patched_14b_tif",
        source_paths=(
            "NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE_PATCHED_14B.tif",
            "FINAL_TESLA_V7_2_HYPERCUBE_PATCHED_14B.tif",
        ),
        parity_path="NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE_PATCHED_14B.tif",
        notebook_name_or_pattern="FINAL_TESLA_V7_2_HYPERCUBE_PATCHED_14B.tif",
        family="hypercube/tensor outputs",
    ),
    AliasSpec(
        id="radar_stack_hwc_640_app_npy",
        source_paths=("NPY_STACKS/RADAR_STACK_HWC_640_app.npy",),
        parity_path="NPY_STACKS/RADAR_STACK_HWC_640_app.npy",
        notebook_name_or_pattern="RADAR_STACK_HWC_640_app.npy",
        family="hypercube/tensor outputs",
        artifact_class="FILESYSTEM_ONLY",
    ),
)


def get_default_alias_spec(alias_id: str) -> AliasSpec:
    for spec in DEFAULT_RASTER_TENSOR_ALIAS_SPECS:
        if spec.id == alias_id:
            return spec
    raise KeyError(f"unknown raster/tensor parity alias id: {alias_id}")


def create_alias_plan(run_dir: str | Path, spec: AliasSpec) -> AliasPlan:
    """Create a copy plan for a single app-native output alias."""

    ensure_standard_parity_dirs(run_dir)
    source_path, source_run_path = _resolve_first_existing_source(run_dir, spec)
    parity_path = resolve_parity_output_path(run_dir, spec.parity_path)
    parity_run_path = f"parity/{Path(spec.parity_path).as_posix()}"
    entry = ParityManifestEntry(
        source_path=source_run_path,
        parity_path=parity_run_path,
        notebook_name_or_pattern=spec.notebook_name_or_pattern,
        family=spec.family,
        classification=spec.classification,
        artifact_class=spec.artifact_class,
        target_mode=spec.target_mode,
        http_servable=spec.http_servable,
        requires_coordinates=spec.requires_coordinates,
        probability_only_required=spec.probability_only_required,
        runtime_output_verified=True,
        notebook_value_parity_verified=spec.notebook_value_parity_verified,
        notes=spec.notes,
    )
    return AliasPlan(
        spec=spec,
        source_path=source_path,
        parity_path=parity_path,
        source_run_path=source_run_path,
        parity_run_path=parity_run_path,
        entry=entry,
    )


def copy_alias(
    run_dir: str | Path,
    run_id: str,
    spec: AliasSpec,
    *,
    manifest_name: str = "parity_manifest.json",
) -> AliasCopyResult:
    """Copy one existing app-native output into the parity tree and write a manifest."""

    plan = create_alias_plan(run_dir, spec)
    plan.parity_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(plan.source_path, plan.parity_path)
    manifest_path = write_parity_manifest(
        run_dir,
        run_id,
        [plan.entry],
        manifest_name=manifest_name,
    )
    return AliasCopyResult(
        status="copied",
        plan=plan,
        entry=plan.entry,
        manifest_path=manifest_path,
    )


def _resolve_first_existing_source(run_dir: str | Path, spec: AliasSpec) -> tuple[Path, str]:
    checked: list[str] = []
    for source_run_path in spec.source_paths:
        source_path = resolve_run_output_path(run_dir, source_run_path)
        checked.append(source_run_path)
        if source_path.is_file():
            return source_path, Path(source_run_path).as_posix()
    raise AliasSourceMissingError(
        f"missing source for alias {spec.id}; checked: {', '.join(checked)}"
    )
