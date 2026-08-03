"""Measured elevation-change stage.

Fetches two public elevation epochs onto the run's locked grid, co-registers
them, and writes the measured placed-material thickness together with the
reviewed zones derived from it.

Both epochs are fetched through the same tiling and grid specification the DEM
stage already uses, so the two surfaces and the run's radar rasters are
co-located by construction. That is what makes the measured zones usable as
anchors for the existing local-depth engine without any change to it.

Every output is filesystem-only. The zone file contains real polygon
coordinates, and the repository contract forbids exposing geometry, coordinates
or paths through any HTTP surface.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Sequence

import numpy as np

from app.db.models.enums import ArtifactClass
from app.errors import StageError
from app.pipeline._base import (
    ParityCategory,
    Stage,
    StageContext,
    StageResult,
    build_stage_artifact,
)
from app.pipeline.elevation_change.coregistration import (
    CoregistrationError,
    CoregistrationResult,
    coregister_elevation_pair,
)
from app.pipeline.elevation_change.sources import (
    COVERAGE_UNITED_STATES,
    ElevationPair,
    ElevationSourceError,
    select_source_pair,
)
from app.pipeline.elevation_change.thickness import (
    DEFAULT_CORRELATION_LENGTH_M,
    DEFAULT_DETECTION_SIGMA,
)
from app.pipeline.elevation_change.zones import (
    ANCHOR_ROLE,
    CANDIDATE_ROLE,
    MIN_ZONES_WITH_WITHHELD_CANDIDATE,
    ZoneGenerationError,
    assign_roles,
    generate_measured_zones,
    zones_to_geojson,
)
from app.pipeline.stages.dem import (
    build_dem_tile_requests,
    write_georeferenced_raster,
    write_raster_sidecar,
)
from app.pipeline.stages.grid import GridSpec

STAGE_DIR_NAME = "elevation_change"
CHANGE_TIF_NAME = "elevation_change_m.tif"
ZONES_GEOJSON_NAME = "measured_zones.geojson"
SUMMARY_NAME = "elevation_change_summary.json"
SUMMARY_SCHEMA = "elevation_change_summary_v1"

STATUS_MEASURED = "measured"
STATUS_NO_MEASURABLE_CHANGE = "no_measurable_change"
STATUS_NOT_AVAILABLE = "not_available"

# A zone must cover at least this many cells of the *source* data, not of the
# run grid. The run grid is 10 m while the coarsest sources are 30 m, so a
# threshold expressed in grid pixels silently admits zones only two or three
# real samples across. Such a zone is a noise excursion wearing a feature's
# clothes: its interior pixels are copies of each other, so its apparent
# precision is fabricated by resampling.
MIN_SOURCE_CELLS_PER_ZONE = 25


def minimum_zone_pixels(*, source_resolution_m: float, grid_scale_m: float,
                        min_source_cells: int = MIN_SOURCE_CELLS_PER_ZONE) -> int:
    """Translate a source-cell requirement into run-grid pixels."""

    if source_resolution_m <= 0 or grid_scale_m <= 0:
        raise ValueError("resolutions must be positive")
    cells_per_axis = max(1.0, float(source_resolution_m) / float(grid_scale_m))
    return int(round(int(min_source_cells) * cells_per_axis * cells_per_axis))

# Fetches both epochs, so a fetcher signature identical to the DEM stage's.
EpochTileFetcher = Callable[..., np.ndarray]


@dataclass(frozen=True, slots=True)
class ElevationChangeOutputs:
    change_tif: Path
    summary_json: Path
    zones_geojson: Path | None


def _fetch_epoch_array(
    grid_spec: GridSpec,
    *,
    tile_fetcher: EpochTileFetcher,
    tile_size: int,
) -> np.ndarray:
    """Assemble one epoch on the locked grid using the DEM stage's tiling."""

    requests = build_dem_tile_requests(grid_spec, tile_size=tile_size)
    surface = np.full((grid_spec.size, grid_spec.size), grid_spec.nodata, dtype=np.float32)
    for request in requests:
        tile = tile_fetcher(
            grid_spec=grid_spec,
            tile_row=request.tile_row,
            tile_col=request.tile_col,
            xmin=request.xmin,
            ymin=request.ymin,
            xmax=request.xmax,
            ymax=request.ymax,
            size=request.size,
        )
        if tile.shape != (request.size, request.size):
            raise StageError(
                f"elevation tile ({request.tile_row},{request.tile_col}) returned shape "
                f"{tile.shape}, expected {(request.size, request.size)}."
            )
        row_start = request.tile_row * request.size
        col_start = request.tile_col * request.size
        surface[row_start : row_start + request.size, col_start : col_start + request.size] = tile
    return surface


def _write_summary(
    path: Path,
    *,
    status: str,
    pair: ElevationPair | None,
    coregistration: CoregistrationResult | None,
    zone_summary: list[dict[str, Any]],
    warnings: list[str],
) -> None:
    payload: dict[str, Any] = {
        "schema_version": SUMMARY_SCHEMA,
        "stage": "elevation_change",
        "status": status,
        "measurement_kind": "public_elevation_change_v1",
        "measures": "placed_material_thickness",
        "does_not_measure": "depth_to_a_buried_object",
        "source_pair": pair.as_mapping() if pair is not None else None,
        "coregistration": coregistration.as_mapping() if coregistration is not None else None,
        "zone_count": len(zone_summary),
        "anchor_count": sum(1 for zone in zone_summary if zone["role"] == ANCHOR_ROLE),
        "candidate_count": sum(1 for zone in zone_summary if zone["role"] == CANDIDATE_ROLE),
        "zones": zone_summary,
        "warnings": sorted(set(warnings)),
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


class ElevationChangeStage(Stage):
    name = "elevation_change"
    parity_category = ParityCategory.PARITY_REPLACES
    parity_reason = (
        "Adds a measured public elevation-change stage with no notebook equivalent. "
        "It measures placed material thickness directly and does not reuse any "
        "depth-named radar proxy."
    )

    def __init__(
        self,
        *,
        grid_spec: GridSpec,
        coverage: str = COVERAGE_UNITED_STATES,
        target_thickness_m: float | None = None,
        source_keys: Sequence[str] | None = None,
        early_tile_fetcher: EpochTileFetcher | None = None,
        late_tile_fetcher: EpochTileFetcher | None = None,
        tile_size: int = 320,
        erosion_pixels: int = 2,
        min_pixels: int | None = None,
        band_count: int = 3,
        correlation_length_m: float = DEFAULT_CORRELATION_LENGTH_M,
        detection_sigma: float = DEFAULT_DETECTION_SIGMA,
        withhold_for_validation: bool = True,
    ) -> None:
        self.grid_spec = grid_spec
        self.coverage = coverage
        self.target_thickness_m = target_thickness_m
        # Lets an operator pin a pair after a diagnostic shows the default
        # pair shares data at their location.
        self.source_keys = list(source_keys) if source_keys else None
        self.early_tile_fetcher = early_tile_fetcher
        self.late_tile_fetcher = late_tile_fetcher
        self.tile_size = int(tile_size)
        self.erosion_pixels = int(erosion_pixels)
        # None means "derive it from the source resolution once the pair is
        # chosen", which is the only way to express the requirement honestly.
        self.min_pixels = None if min_pixels is None else int(min_pixels)
        self.band_count = int(band_count)
        self.correlation_length_m = float(correlation_length_m)
        self.detection_sigma = float(detection_sigma)
        self.withhold_for_validation = bool(withhold_for_validation)

    def _build_fetchers(self, settings: Any, pair: ElevationPair) -> tuple[EpochTileFetcher, EpochTileFetcher]:
        if self.early_tile_fetcher is not None and self.late_tile_fetcher is not None:
            return self.early_tile_fetcher, self.late_tile_fetcher

        # Imported here so the stage remains importable, and unit-testable with
        # injected fetchers, without an Earth Engine session.
        from app.pipeline.elevation_change.ee_fetch import create_ee_elevation_tile_fetcher

        early = self.early_tile_fetcher or create_ee_elevation_tile_fetcher(
            settings, self.grid_spec, pair.early
        )
        late = self.late_tile_fetcher or create_ee_elevation_tile_fetcher(
            settings, self.grid_spec, pair.late
        )
        return early, late

    async def run(self, context: StageContext) -> StageResult:
        stage_dir = context.run_dir / STAGE_DIR_NAME
        stage_dir.mkdir(parents=True, exist_ok=True)
        summary_path = stage_dir / SUMMARY_NAME

        try:
            pair = select_source_pair(
                coverage=self.coverage,
                target_thickness_m=self.target_thickness_m,
                available_keys=self.source_keys,
            )
        except ElevationSourceError as exc:
            _write_summary(
                summary_path,
                status=STATUS_NOT_AVAILABLE,
                pair=None,
                coregistration=None,
                zone_summary=[],
                warnings=[f"source_selection_failed:{exc}"],
            )
            return self._result(context, ElevationChangeOutputs(
                change_tif=stage_dir / CHANGE_TIF_NAME,
                summary_json=summary_path,
                zones_geojson=None,
            ), status=STATUS_NOT_AVAILABLE, wrote_raster=False)

        warnings = list(pair.warnings)

        early_fetcher, late_fetcher = self._build_fetchers(context.settings, pair)
        early = _fetch_epoch_array(
            self.grid_spec, tile_fetcher=early_fetcher, tile_size=self.tile_size
        )
        late = _fetch_epoch_array(
            self.grid_spec, tile_fetcher=late_fetcher, tile_size=self.tile_size
        )

        try:
            coregistration = coregister_elevation_pair(
                early, late, nodata=self.grid_spec.nodata
            )
        except CoregistrationError as exc:
            _write_summary(
                summary_path,
                status=STATUS_NOT_AVAILABLE,
                pair=pair,
                coregistration=None,
                zone_summary=[],
                warnings=[*warnings, f"coregistration_failed:{exc}"],
            )
            return self._result(context, ElevationChangeOutputs(
                change_tif=stage_dir / CHANGE_TIF_NAME,
                summary_json=summary_path,
                zones_geojson=None,
            ), status=STATUS_NOT_AVAILABLE, wrote_raster=False)

        # NaN marks pixels invalid in either epoch; the run grid uses an explicit
        # nodata sentinel, so convert before writing.
        change_raster = np.where(
            np.isfinite(coregistration.delta_m),
            coregistration.delta_m,
            self.grid_spec.nodata,
        ).astype(np.float32)
        change_path = stage_dir / CHANGE_TIF_NAME
        write_georeferenced_raster(change_path, change_raster, self.grid_spec)
        write_raster_sidecar(
            change_path,
            grid_manifest=self.grid_spec.manifest,
            nodata=self.grid_spec.nodata,
            dtype="float32",
            shape=change_raster.shape,
        )

        grid_scale_m = float(self.grid_spec.manifest.scale_m)
        pixel_area_m2 = grid_scale_m**2
        min_pixels = self.min_pixels
        if min_pixels is None:
            min_pixels = minimum_zone_pixels(
                source_resolution_m=pair.working_resolution_m,
                grid_scale_m=grid_scale_m,
            )
            warnings.append(f"minimum_zone_pixels_derived_from_source_resolution:{min_pixels}")

        zones = generate_measured_zones(
            coregistration.delta_m,
            sigma_stable_m=coregistration.stats.sigma_m,
            pixel_area_m2=pixel_area_m2,
            band_count=self.band_count,
            erosion_pixels=self.erosion_pixels,
            min_pixels=min_pixels,
            correlation_length_m=self.correlation_length_m,
            detection_sigma=self.detection_sigma,
        )

        zones_path: Path | None = None
        zone_summary: list[dict[str, Any]] = []
        status = STATUS_MEASURED

        if not zones:
            status = STATUS_NO_MEASURABLE_CHANGE
            warnings.append("no_measurable_placed_material")
        else:
            withhold = self.withhold_for_validation and len(zones) >= MIN_ZONES_WITH_WITHHELD_CANDIDATE
            if self.withhold_for_validation and not withhold:
                warnings.append("too_few_zones_to_withhold_a_validation_zone")
            try:
                assigned = assign_roles(zones, withhold_for_validation=withhold)
            except ZoneGenerationError as exc:
                status = STATUS_NO_MEASURABLE_CHANGE
                warnings.append(f"zone_assignment_failed:{exc}")
                assigned = []

            if assigned:
                zone_summary = [
                    {
                        "zone_id": zone.zone_id,
                        "role": zone.role,
                        **zone.thickness.as_mapping(),
                    }
                    for zone in assigned
                ]
                if any(zone.role == CANDIDATE_ROLE for zone in assigned):
                    zones_path = stage_dir / ZONES_GEOJSON_NAME
                    payload = zones_to_geojson(
                        assigned,
                        transform=self.grid_spec.transform,
                        crs=self.grid_spec.crs,
                    )
                    zones_path.write_text(
                        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
                    )
                else:
                    warnings.append("no_candidate_zone_so_no_reviewed_zone_file")

        _write_summary(
            summary_path,
            status=status,
            pair=pair,
            coregistration=coregistration,
            zone_summary=zone_summary,
            warnings=warnings,
        )

        return self._result(
            context,
            ElevationChangeOutputs(
                change_tif=change_path,
                summary_json=summary_path,
                zones_geojson=zones_path,
            ),
            status=status,
            wrote_raster=True,
            coregistration=coregistration,
            pair=pair,
            zone_summary=zone_summary,
        )

    def _result(
        self,
        context: StageContext,
        outputs: ElevationChangeOutputs,
        *,
        status: str,
        wrote_raster: bool,
        coregistration: CoregistrationResult | None = None,
        pair: ElevationPair | None = None,
        zone_summary: list[dict[str, Any]] | None = None,
    ) -> StageResult:
        artifacts = []
        # Everything here is filesystem-only. The zone file carries real polygon
        # coordinates and the raster carries the site's elevation surface;
        # neither may be reachable over HTTP.
        if wrote_raster and outputs.change_tif.is_file():
            artifacts.append(
                build_stage_artifact(
                    name="elevation_change_tif",
                    relative_path=outputs.change_tif.relative_to(context.run_dir).as_posix(),
                    artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                    size_bytes=outputs.change_tif.stat().st_size,
                    http_servable=False,
                )
            )
        if outputs.zones_geojson is not None and outputs.zones_geojson.is_file():
            artifacts.append(
                build_stage_artifact(
                    name="elevation_change_measured_zones",
                    relative_path=outputs.zones_geojson.relative_to(context.run_dir).as_posix(),
                    artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                    size_bytes=outputs.zones_geojson.stat().st_size,
                    http_servable=False,
                )
            )
        artifacts.append(
            build_stage_artifact(
                name="elevation_change_summary",
                relative_path=outputs.summary_json.relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=outputs.summary_json.stat().st_size,
                http_servable=False,
            )
        )

        metadata: dict[str, Any] = {
            "schema_version": SUMMARY_SCHEMA,
            "stage": self.name,
            "status": status,
            "measurement_kind": "public_elevation_change_v1",
            "zone_count": len(zone_summary or []),
        }
        if pair is not None:
            metadata["expected_sigma_m"] = round(pair.expected_sigma_m, 4)
            metadata["minimum_detectable_thickness_m"] = round(
                pair.minimum_detectable_thickness_m, 4
            )
        if coregistration is not None:
            metadata["stable_ground_sigma_m"] = round(coregistration.stats.sigma_m, 6)
            metadata["vertical_offset_removed_m"] = round(coregistration.stats.offset_m, 6)

        return StageResult(artifacts=artifacts, metadata=metadata)
