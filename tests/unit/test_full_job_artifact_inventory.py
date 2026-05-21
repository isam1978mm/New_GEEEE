from __future__ import annotations

import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory

from app.db.models.enums import ArtifactClass
from app.pipeline._base import StageContext
from app.pipeline.stages.alignment_qa import AlignmentQaStage
from app.pipeline.stages.dem import DemStage, deterministic_dem_tile
from app.pipeline.stages.dem_derivatives import OUTPUT_NAMES as DEM_DERIVATIVE_NAMES, DemDerivativesStage
from app.pipeline.stages.feature_stacks import FeatureStacksStage
from app.pipeline.stages.grid import GridStage, build_run_grid
from app.pipeline.stages.hypercube import HypercubeStage
from app.pipeline.stages.object_extract import ObjectExtractStage
from app.pipeline.stages.pca_anomaly import PcaAnomalyStage
from app.pipeline.stages.s2_indices import INDEX_NAMES, S2IndicesStage, deterministic_s2_cube_fetcher
from app.pipeline.stages.sar_rtc import SarRtcStage, deterministic_radar_cube_fetcher
from app.pipeline.stages.thermal import ThermalStage, deterministic_lst_fetcher
from app.pipeline.stages.zero_shift import ZeroShiftStage


def test_full_job_artifact_families_are_emitted_by_owner_stages() -> None:
    with TemporaryDirectory() as temp_dir:
        run_dir = Path(temp_dir)
        settings = _settings(run_dir)
        grid_spec = build_run_grid(35.59499, 36.12694)
        context = StageContext(run_id="run-1", settings=settings, run_dir=run_dir)

        grid_result = asyncio.run(GridStage(latitude=35.59499, longitude=36.12694).run(context))
        dem_result = asyncio.run(DemStage(grid_spec=grid_spec, tile_fetcher=deterministic_dem_tile).run(context))
        zero_shift_result = asyncio.run(ZeroShiftStage(grid_spec=grid_spec).run(context))
        sar_result = asyncio.run(SarRtcStage(grid_spec=grid_spec, radar_cube_fetcher=deterministic_radar_cube_fetcher).run(context))
        s2_result = asyncio.run(S2IndicesStage(grid_spec=grid_spec, s2_cube_fetcher=deterministic_s2_cube_fetcher).run(context))
        dem_derivatives_result = asyncio.run(DemDerivativesStage(grid_spec=grid_spec).run(context))
        thermal_result = asyncio.run(ThermalStage(grid_spec=grid_spec, lst_fetcher=deterministic_lst_fetcher).run(context))
        feature_stacks_result = asyncio.run(FeatureStacksStage(grid_spec=grid_spec).run(context))
        hypercube_result = asyncio.run(HypercubeStage(grid_spec=grid_spec).run(context))
        pca_result = asyncio.run(PcaAnomalyStage(grid_spec=grid_spec).run(context))
        object_result = asyncio.run(ObjectExtractStage(grid_spec=grid_spec).run(context))
        alignment_result = asyncio.run(AlignmentQaStage(grid_spec=grid_spec).run(context))

        assert _artifact_classes(grid_result) == {
            "grid_manifest": ArtifactClass.LOCAL_SENSITIVE,
            "grid_guard_summary": ArtifactClass.FILESYSTEM_ONLY,
        }
        assert _artifact_classes(dem_result) == {
            "dem_tif": ArtifactClass.LOCAL_SENSITIVE,
            "dem_npy": ArtifactClass.LOCAL_SENSITIVE,
            "dem_audit_summary": ArtifactClass.FILESYSTEM_ONLY,
        }
        assert _artifact_classes(zero_shift_result) == {
            "zero_shift_summary": ArtifactClass.FILESYSTEM_ONLY,
            "drift_audit": ArtifactClass.FILESYSTEM_ONLY,
        }
        assert _artifact_classes(sar_result) == {
            "VV_dB": ArtifactClass.LOCAL_SENSITIVE,
            "VH_dB": ArtifactClass.LOCAL_SENSITIVE,
            "logRatio_dB": ArtifactClass.LOCAL_SENSITIVE,
            "incidence": ArtifactClass.LOCAL_SENSITIVE,
            "sar_pair_diagnostics": ArtifactClass.FILESYSTEM_ONLY,
            "sar_summary": ArtifactClass.FILESYSTEM_ONLY,
            "sar_nodata_audit": ArtifactClass.FILESYSTEM_ONLY,
            "sar_alignment_summary": ArtifactClass.FILESYSTEM_ONLY,
        }
        assert _artifact_classes(s2_result) == {
            **{name: ArtifactClass.LOCAL_SENSITIVE for name in INDEX_NAMES},
            "s2_indices_summary": ArtifactClass.FILESYSTEM_ONLY,
        }
        assert _artifact_classes(dem_derivatives_result) == {
            **{name: ArtifactClass.LOCAL_SENSITIVE for name in DEM_DERIVATIVE_NAMES},
            "dem_derivatives_summary": ArtifactClass.FILESYSTEM_ONLY,
        }
        assert _artifact_classes(thermal_result) == {
            "lst": ArtifactClass.LOCAL_SENSITIVE,
            "thermal_summary": ArtifactClass.FILESYSTEM_ONLY,
        }
        assert _artifact_classes(feature_stacks_result) == {
            "science_core_stack_tif": ArtifactClass.FILESYSTEM_ONLY,
            "science_core_stack_npy": ArtifactClass.FILESYSTEM_ONLY,
            "radar_linear_support_stack_tif": ArtifactClass.FILESYSTEM_ONLY,
            "radar_linear_support_stack_npy": ArtifactClass.FILESYSTEM_ONLY,
            "ai_ready_support_stack_tif": ArtifactClass.FILESYSTEM_ONLY,
            "ai_ready_support_stack_npy": ArtifactClass.FILESYSTEM_ONLY,
            "s2_mask_support_valid": ArtifactClass.FILESYSTEM_ONLY,
            "band_stats": ArtifactClass.FILESYSTEM_ONLY,
            "stack_presence_summary": ArtifactClass.FILESYSTEM_ONLY,
            "tensor_audit_summary": ArtifactClass.FILESYSTEM_ONLY,
            "geometry_consistency_summary": ArtifactClass.FILESYSTEM_ONLY,
        }
        assert _artifact_classes(hypercube_result) == {
            "hypercube_tif": ArtifactClass.LOCAL_SENSITIVE,
            "hypercube_npy": ArtifactClass.LOCAL_SENSITIVE,
            "hypercube_band_order": ArtifactClass.LOCAL_SENSITIVE,
            "hypercube_band_stats": ArtifactClass.LOCAL_SENSITIVE,
            "hypercube_norm_params": ArtifactClass.LOCAL_SENSITIVE,
            "hypercube_audit": ArtifactClass.FILESYSTEM_ONLY,
        }
        assert _artifact_classes(pca_result) == {
            "pca_anomaly_tif": ArtifactClass.LOCAL_SENSITIVE,
            "pca_eigenvalues": ArtifactClass.LOCAL_SENSITIVE,
            "parity_qa_summary": ArtifactClass.FILESYSTEM_ONLY,
        }
        object_classes = _artifact_classes(object_result)
        assert object_classes["objects_index"] == ArtifactClass.REDACTED_PUBLIC
        assert object_classes["clusters_summary"] == ArtifactClass.REDACTED_PUBLIC
        assert object_classes["object_mask"] == ArtifactClass.FILESYSTEM_ONLY
        patch_names = [name for name in object_classes if name.startswith("object_patch_")]
        assert patch_names
        assert all(object_classes[name] == ArtifactClass.FILESYSTEM_ONLY for name in patch_names)
        assert _artifact_classes(alignment_result) == {
            "alignment_qa": ArtifactClass.REDACTED_PUBLIC,
            "alignment_audit": ArtifactClass.REDACTED_PUBLIC,
            "alignment_mask_selection": ArtifactClass.REDACTED_PUBLIC,
            "alignment_summary_redacted": ArtifactClass.LOCAL_SENSITIVE,
        }


def _artifact_classes(result) -> dict[str, ArtifactClass]:
    return {artifact.name: artifact.artifact_class for artifact in result.artifacts}


def _settings(run_dir: Path):
    from app.config import Settings

    data_dir = run_dir / "data"
    return Settings(data_dir=data_dir, database_path=data_dir / "db.sqlite")
