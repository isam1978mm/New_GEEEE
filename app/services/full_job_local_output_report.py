from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from app.db.models.enums import ArtifactClass

FULL_JOB_LOCAL_OUTPUT_REPORT_NAME = "full_job_local_output_comparison_report.json"


@dataclass(frozen=True, slots=True)
class OutputFamilySpec:
    family_id: str
    title: str
    artifact_classes: tuple[str, ...]
    outputs: tuple[str, ...]
    notes: str


APPROVED_OUTPUT_FAMILIES: tuple[OutputFamilySpec, ...] = (
    OutputFamilySpec(
        family_id="grid_dem_core",
        title="GRID and DEM core outputs",
        artifact_classes=(ArtifactClass.LOCAL_SENSITIVE.value, ArtifactClass.FILESYSTEM_ONLY.value),
        outputs=("grid_manifest.json", "dem.tif", "dem.npy", "qa/grid_dem/grid_guard_summary.json", "qa/grid_dem/dem_audit_summary.json"),
        notes="Core GRID/DEM outputs and approved QA support files.",
    ),
    OutputFamilySpec(
        family_id="sar_core_and_qa",
        title="SAR RTC core and QA outputs",
        artifact_classes=(ArtifactClass.LOCAL_SENSITIVE.value, ArtifactClass.FILESYSTEM_ONLY.value),
        outputs=(
            "VV_dB.tif",
            "VH_dB.tif",
            "logRatio_dB.tif",
            "incidence.tif",
            "npy_radar_bands/VV_dB.npy",
            "npy_radar_bands/VH_dB.npy",
            "npy_radar_bands/logRatio_dB.npy",
            "npy_radar_bands/incidence.npy",
            "qa/sar/sar_pair_diagnostics.json",
            "qa/sar/sar_summary.csv",
            "qa/sar/sar_nodata_audit.csv",
            "qa/sar/sar_alignment_summary.json",
        ),
        notes="Canonical SAR outputs plus approved local QA summaries.",
    ),
    OutputFamilySpec(
        family_id="s2_dem_thermal_core",
        title="S2 indices, DEM derivatives, and thermal outputs",
        artifact_classes=(ArtifactClass.LOCAL_SENSITIVE.value, ArtifactClass.FILESYSTEM_ONLY.value),
        outputs=(
            "NDVI.tif",
            "NDWI.tif",
            "NDMI.tif",
            "NBR.tif",
            "IRONOX.tif",
            "IRON_SWIR.tif",
            "BSI.tif",
            "slope.tif",
            "aspect.tif",
            "curvature.tif",
            "TPI.tif",
            "TRI.tif",
            "roughness.tif",
            "TWI.tif",
            "lst.tif",
            "qa/stacks/s2_indices_summary.json",
            "qa/stacks/dem_derivatives_summary.json",
            "qa/stacks/thermal_summary.json",
        ),
        notes="Science-core optical, terrain, and thermal outputs with approved summaries.",
    ),
    OutputFamilySpec(
        family_id="feature_stack_support",
        title="Feature stack and tensor support outputs",
        artifact_classes=(ArtifactClass.FILESYSTEM_ONLY.value,),
        outputs=(
            "stacks/tensor_support/science_core_stack.tif",
            "stacks/tensor_support/science_core_stack.npy",
            "stacks/tensor_support/radar_linear_support_stack.tif",
            "stacks/tensor_support/radar_linear_support_stack.npy",
            "stacks/tensor_support/ai_ready_support_stack.tif",
            "stacks/tensor_support/ai_ready_support_stack.npy",
            "stacks/optical_support/s2_mask_support_valid.tif",
            "qa/stacks/band_stats.csv",
            "qa/stacks/stack_presence_summary.json",
            "qa/stacks/tensor_audit_summary.json",
            "qa/stacks/geometry_consistency_summary.json",
        ),
        notes="Approved neutral stack variants and support audits.",
    ),
    OutputFamilySpec(
        family_id="focus_and_location_local",
        title="Focus-mask and exact-location local outputs",
        artifact_classes=(ArtifactClass.FILESYSTEM_ONLY.value,),
        outputs=(
            "full_job/focus/focus_zone_17m.tif",
            "full_job/focus/focus_zone_17m.npy",
            "full_job/focus/focus_zone_ai_ready_window.npy",
            "full_job/focus/focus_zone_summary.json",
            "full_job/focus/focus_zone_band_summary.csv",
            "full_job/location/site_location.geojson",
            "kmz/site_location.kmz",
        ),
        notes="Exact-location local-only outputs remain non-public and filesystem-only.",
    ),
    OutputFamilySpec(
        family_id="field_ops_local",
        title="Field-operations local outputs",
        artifact_classes=(ArtifactClass.FILESYSTEM_ONLY.value,),
        outputs=(
            "kmz/field_ops_navigation.kmz",
            "full_job/field_ops/field_ops_report.json",
            "full_job/field_ops/field_ops_brief.txt",
        ),
        notes="Field-operation deliverables remain local-only.",
    ),
    OutputFamilySpec(
        family_id="gps_comparison_local",
        title="GPS comparison local outputs",
        artifact_classes=(ArtifactClass.FILESYSTEM_ONLY.value,),
        outputs=(
            "full_job/gps/gps_point_comparison.json",
            "full_job/gps/gps_point_comparison.csv",
        ),
        notes="GPS comparison reports remain local-only.",
    ),
    OutputFamilySpec(
        family_id="hypercube_pca_objects_alignment",
        title="Hypercube, PCA, object, and alignment outputs",
        artifact_classes=(
            ArtifactClass.LOCAL_SENSITIVE.value,
            ArtifactClass.REDACTED_PUBLIC.value,
            ArtifactClass.FILESYSTEM_ONLY.value,
        ),
        outputs=(
            "hypercube.tif",
            "hypercube.npy",
            "hypercube_band_order.csv",
            "hypercube_band_stats.csv",
            "hypercube_norm_params.csv",
            "qa/parity/hypercube_audit.csv",
            "pca_anomaly.tif",
            "pca_eigenvalues.json",
            "qa/parity/parity_qa_summary.json",
            "objects_index.csv",
            "clusters_summary.csv",
            "objects/object_mask.npy",
            "objects/object_patches/object_###.npy",
            "alignment_qa.json",
            "alignment_audit.json",
            "alignment_mask_selection.json",
            "qa/alignment/alignment_summary_redacted.json",
        ),
        notes="Core anomaly and object outputs plus approved non-public object support files.",
    ),
    OutputFamilySpec(
        family_id="reference_locator_local",
        title="Reference locator local outputs",
        artifact_classes=(ArtifactClass.FILESYSTEM_ONLY.value,),
        outputs=("full_job/reference/reference_locator_inventory.json",),
        notes="Local path/reference inventory report only; never public-listed or served.",
    ),
    OutputFamilySpec(
        family_id="experimental_classifier_local",
        title="Experimental classifier local outputs",
        artifact_classes=(ArtifactClass.FILESYSTEM_ONLY.value,),
        outputs=(
            "experimental/classifications.csv",
            "experimental/summary.json",
            "experimental/neutral_target_labels.json",
        ),
        notes="Experimental outputs remain CLI-only and filesystem-only.",
    ),
    OutputFamilySpec(
        family_id="full_job_comparison_local",
        title="Full notebook local-output comparison reports",
        artifact_classes=(ArtifactClass.FILESYSTEM_ONLY.value,),
        outputs=(FULL_JOB_LOCAL_OUTPUT_REPORT_NAME,),
        notes="Local comparison reports remain non-public unless separately redacted and approved.",
    ),
)


CURRENT_APP_OUTPUT_FAMILIES: tuple[OutputFamilySpec, ...] = APPROVED_OUTPUT_FAMILIES

INTENTIONALLY_EXCLUDED_FAMILIES: tuple[OutputFamilySpec, ...] = (
    OutputFamilySpec(
        family_id="raw_notebook_runtime_mirrors",
        title="Raw notebook runtime mirrors and Drive-first folder dumps",
        artifact_classes=(ArtifactClass.FILESYSTEM_ONLY.value,),
        outputs=("raw notebook full-job mirrors", "Drive folder mirrors", "shell listings", "path crawls"),
        notes="The app does not mirror Colab or Drive runtime structures.",
    ),
    OutputFamilySpec(
        family_id="target_claim_and_detector_exports",
        title="Target-claim, detector, and exact-target exports",
        artifact_classes=(ArtifactClass.FILESYSTEM_ONLY.value,),
        outputs=(
            "target-claim CSV/TXT/JSON products",
            "detector GeoJSON outputs",
            "exact target tables",
            "heatmap or 3D target KMZ variants",
        ),
        notes="These remain excluded from the app local-output inventory at the current approval level.",
    ),
    OutputFamilySpec(
        family_id="coordinate_bearing_roi_dumps",
        title="Coordinate-bearing ROI and WKT dump outputs",
        artifact_classes=(ArtifactClass.FILESYSTEM_ONLY.value,),
        outputs=("raw WKT dumps", "exact ROI/point tables", "target-region reference dumps"),
        notes="Raw ROI and target coordinate dumps remain excluded from app reproduction.",
    ),
)


ON_HOLD_FAMILIES: tuple[OutputFamilySpec, ...] = (
    OutputFamilySpec(
        family_id="training_scaffolding",
        title="Training scaffolding and rebuilt ML training workflows",
        artifact_classes=(ArtifactClass.FILESYSTEM_ONLY.value,),
        outputs=("training scaffolds", "learned weights", "rebuilt ML training workflows"),
        notes="These remain on hold pending a separate approved ML phase.",
    ),
    OutputFamilySpec(
        family_id="deep_learning_inference",
        title="CNN, Swin, YOLO, and SegFormer inference workflows",
        artifact_classes=(ArtifactClass.FILESYSTEM_ONLY.value,),
        outputs=("CNN inference", "Swin inference", "YOLO inference", "SegFormer inference"),
        notes="Deep-learning inference remains on hold and out of the current app inventory.",
    ),
    OutputFamilySpec(
        family_id="broken_model_build_cells",
        title="Broken model-build notebook cells",
        artifact_classes=(ArtifactClass.FILESYSTEM_ONLY.value,),
        outputs=("broken model-build cells",),
        notes="Broken notebook model-build sections remain on hold and excluded from implementation.",
    ),
)


def build_full_job_local_output_comparison_report() -> dict[str, object]:
    approved_by_id = {item.family_id: item for item in APPROVED_OUTPUT_FAMILIES}
    current_by_id = {item.family_id: item for item in CURRENT_APP_OUTPUT_FAMILIES}

    covered_ids = sorted(set(approved_by_id) & set(current_by_id))
    missing_ids = sorted(set(approved_by_id) - set(current_by_id))

    covered_outputs = [_serialize_family(current_by_id[family_id], status="covered") for family_id in covered_ids]
    missing_outputs = [_serialize_family(approved_by_id[family_id], status="missing_approved") for family_id in missing_ids]
    excluded_outputs = [_serialize_family(item, status="intentionally_excluded") for item in INTENTIONALLY_EXCLUDED_FAMILIES]
    on_hold_outputs = [_serialize_family(item, status="on_hold") for item in ON_HOLD_FAMILIES]

    return {
        "report_type": "full_job_local_output_comparison",
        "artifact_class": ArtifactClass.FILESYSTEM_ONLY.value,
        "local_only": True,
        "source_documents": [
            "docs/NOTEBOOK_FULL_JOB_INVENTORY.md",
            "docs/NOTEBOOK_FULL_JOB_ARTIFACT_CONTRACT.md",
            "plan.md",
        ],
        "covered_outputs": covered_outputs,
        "missing_approved_outputs": missing_outputs,
        "intentionally_excluded_outputs": excluded_outputs,
        "on_hold_outputs": on_hold_outputs,
        "summary": {
            "covered_output_family_count": len(covered_outputs),
            "missing_approved_output_family_count": len(missing_outputs),
            "intentionally_excluded_output_family_count": len(excluded_outputs),
            "on_hold_output_family_count": len(on_hold_outputs),
        },
    }


def write_full_job_local_output_comparison_report(output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / FULL_JOB_LOCAL_OUTPUT_REPORT_NAME
    report_path.write_text(
        json.dumps(build_full_job_local_output_comparison_report(), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return report_path


def _serialize_family(item: OutputFamilySpec, *, status: str) -> dict[str, object]:
    payload = asdict(item)
    payload["status"] = status
    return payload
