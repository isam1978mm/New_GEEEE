"""Public elevation sources that can be read without contacting anyone.

Every source here is open data reachable from the existing Earth Engine service
account. None of them requires a site visit, a records request, a licence
negotiation, or correspondence with any organisation. That property is the whole
reason this route exists, so it is recorded per source and asserted in tests.

Two things decide whether a pair of sources can answer a question:

- the gap between their epochs, which must bracket the placement to see it;
- their combined vertical noise, which sets the thinnest cover that can be
  distinguished from nothing at all.

The second is what makes coverage matter. Airborne lidar resolves a 0.2 m cover.
Thirty-metre global DEMs cannot see a metre of soil and must say so rather than
return a confident-looking number.

Asset identifiers are data, deliberately gathered in one place, because Earth
Engine deprecates and renames collections. They are unverified against the live
catalogue in this environment: there is no Earth Engine credential here, so the
stage surfaces an unavailable asset as an explicit failure rather than silently
substituting another source.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

COVERAGE_UNITED_STATES = "united_states"
COVERAGE_GLOBAL = "global"

ASSET_IMAGE = "image"
ASSET_IMAGE_COLLECTION = "image_collection"


class ElevationSourceError(ValueError):
    """Raised when no usable pair of elevation sources exists."""


@dataclass(frozen=True, slots=True)
class ElevationSource:
    """One public elevation surface."""

    key: str
    asset_id: str
    asset_kind: str
    band: str
    epoch_start_year: int
    epoch_end_year: int
    nominal_vertical_sigma_m: float
    resolution_m: float
    coverage: str
    description: str
    multi_vintage: bool = False

    def __post_init__(self) -> None:
        if self.asset_kind not in {ASSET_IMAGE, ASSET_IMAGE_COLLECTION}:
            raise ElevationSourceError(f"unsupported asset kind for {self.key}")
        if self.epoch_end_year < self.epoch_start_year:
            raise ElevationSourceError(f"inverted epoch for {self.key}")
        if self.nominal_vertical_sigma_m <= 0:
            raise ElevationSourceError(f"vertical sigma must be positive for {self.key}")
        if self.multi_vintage and self.asset_kind != ASSET_IMAGE_COLLECTION:
            raise ElevationSourceError(
                f"only an image collection can be multi-vintage: {self.key}"
            )

    @property
    def epoch_midpoint_year(self) -> float:
        return (float(self.epoch_start_year) + float(self.epoch_end_year)) / 2.0

    def as_mapping(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "asset_id": self.asset_id,
            "asset_kind": self.asset_kind,
            "band": self.band,
            "epoch_start_year": int(self.epoch_start_year),
            "epoch_end_year": int(self.epoch_end_year),
            "nominal_vertical_sigma_m": float(self.nominal_vertical_sigma_m),
            "resolution_m": float(self.resolution_m),
            "coverage": self.coverage,
            "multi_vintage": bool(self.multi_vintage),
        }


@dataclass(frozen=True, slots=True)
class ElevationEpoch:
    """One source restricted to one acquisition window.

    A multi-vintage collection contributes several of these. That distinction
    carries the whole value of the United States tier: a pair is only as good as
    its worse half, so differencing metre-accurate lidar against a coarse legacy
    baseline discards the lidar's precision entirely and cannot see a soil cover.
    Two lidar vintages of the same collection can.
    """

    source: ElevationSource
    start_year: int
    end_year: int

    def __post_init__(self) -> None:
        if self.end_year < self.start_year:
            raise ElevationSourceError(f"inverted epoch window for {self.source.key}")

    @property
    def midpoint_year(self) -> float:
        return (float(self.start_year) + float(self.end_year)) / 2.0

    @property
    def label(self) -> str:
        if self.source.multi_vintage:
            return f"{self.source.key}@{self.start_year}-{self.end_year}"
        return self.source.key

    def as_mapping(self) -> dict[str, Any]:
        payload = self.source.as_mapping()
        payload["epoch_window_start_year"] = int(self.start_year)
        payload["epoch_window_end_year"] = int(self.end_year)
        payload["label"] = self.label
        return payload


def candidate_epochs(source: ElevationSource) -> list[ElevationEpoch]:
    """Acquisition windows a source can supply.

    A multi-vintage collection is split at its midpoint so an early and a late
    vintage of the same product can be differenced against each other.
    """

    if not source.multi_vintage:
        return [
            ElevationEpoch(
                source=source,
                start_year=source.epoch_start_year,
                end_year=source.epoch_end_year,
            )
        ]

    split = int(source.epoch_midpoint_year)
    return [
        ElevationEpoch(source=source, start_year=source.epoch_start_year, end_year=split),
        ElevationEpoch(source=source, start_year=split, end_year=source.epoch_end_year),
    ]


# Ordered oldest epoch first. Vertical sigma values are published nominal
# accuracies for the product as a whole; the measured stable-ground spread of an
# actual pair always overrides them downstream, and is usually the larger.
ELEVATION_SOURCES: tuple[ElevationSource, ...] = (
    ElevationSource(
        key="nasadem",
        asset_id="NASA/NASADEM_HGT/001",
        asset_kind=ASSET_IMAGE,
        band="elevation",
        epoch_start_year=2000,
        epoch_end_year=2000,
        nominal_vertical_sigma_m=3.0,
        resolution_m=30.0,
        coverage=COVERAGE_GLOBAL,
        description="Reprocessed SRTM, single February 2000 epoch, near-global.",
    ),
    ElevationSource(
        key="usgs_ned",
        asset_id="USGS/NED",
        asset_kind=ASSET_IMAGE,
        band="elevation",
        epoch_start_year=1999,
        epoch_end_year=2013,
        nominal_vertical_sigma_m=1.5,
        resolution_m=10.0,
        coverage=COVERAGE_UNITED_STATES,
        description="Seamless National Elevation Dataset, mixed vintage baseline.",
    ),
    ElevationSource(
        key="alos_aw3d30",
        asset_id="JAXA/ALOS/AW3D30/V3_2",
        asset_kind=ASSET_IMAGE_COLLECTION,
        band="DSM",
        epoch_start_year=2006,
        epoch_end_year=2011,
        nominal_vertical_sigma_m=3.0,
        resolution_m=30.0,
        coverage=COVERAGE_GLOBAL,
        description="ALOS World 3D, global optical stereo surface model.",
    ),
    ElevationSource(
        key="copernicus_glo30",
        asset_id="COPERNICUS/DEM/GLO30_2024_1",
        asset_kind=ASSET_IMAGE_COLLECTION,
        band="DEM",
        epoch_start_year=2011,
        epoch_end_year=2015,
        nominal_vertical_sigma_m=2.0,
        resolution_m=30.0,
        coverage=COVERAGE_GLOBAL,
        description="Copernicus GLO-30, already used by the run DEM stage.",
    ),
    ElevationSource(
        key="usgs_3dep_10m",
        asset_id="USGS/3DEP/10m",
        asset_kind=ASSET_IMAGE,
        band="elevation",
        epoch_start_year=2010,
        epoch_end_year=2023,
        nominal_vertical_sigma_m=0.5,
        resolution_m=10.0,
        coverage=COVERAGE_UNITED_STATES,
        description="Seamless 3DEP, largely lidar-derived over the conterminous US.",
    ),
    ElevationSource(
        key="usgs_3dep_1m",
        asset_id="USGS/3DEP/1m",
        asset_kind=ASSET_IMAGE_COLLECTION,
        band="elevation",
        epoch_start_year=2012,
        epoch_end_year=2026,
        nominal_vertical_sigma_m=0.1,
        resolution_m=1.0,
        coverage=COVERAGE_UNITED_STATES,
        description="Project-level 1 m lidar DEM; the only source fine enough for a thin cover.",
        multi_vintage=True,
    ),
)

SOURCES_BY_KEY: dict[str, ElevationSource] = {source.key: source for source in ELEVATION_SOURCES}

MIN_EPOCH_SEPARATION_YEARS = 3.0
DETECTION_SIGMA = 1.96


@dataclass(frozen=True, slots=True)
class ElevationPair:
    """Two epochs chosen to bracket a placement."""

    early: ElevationEpoch
    late: ElevationEpoch
    warnings: tuple[str, ...] = ()

    @property
    def same_source(self) -> bool:
        return self.early.source.key == self.late.source.key

    @property
    def epoch_separation_years(self) -> float:
        return self.late.midpoint_year - self.early.midpoint_year

    @property
    def expected_sigma_m(self) -> float:
        """Vertical noise expected of the difference, before measurement."""

        return float(
            (
                self.early.source.nominal_vertical_sigma_m**2
                + self.late.source.nominal_vertical_sigma_m**2
            )
            ** 0.5
        )

    @property
    def minimum_detectable_thickness_m(self) -> float:
        """Thinnest cover this pair could distinguish from nothing.

        Reported before any data is fetched so an infeasible request can be
        refused early rather than after a long download.
        """

        return DETECTION_SIGMA * self.expected_sigma_m

    @property
    def working_resolution_m(self) -> float:
        return max(self.early.source.resolution_m, self.late.source.resolution_m)

    def as_mapping(self) -> dict[str, Any]:
        return {
            "early": self.early.as_mapping(),
            "late": self.late.as_mapping(),
            "same_source": self.same_source,
            "epoch_separation_years": round(self.epoch_separation_years, 2),
            "expected_sigma_m": round(self.expected_sigma_m, 4),
            "minimum_detectable_thickness_m": round(self.minimum_detectable_thickness_m, 4),
            "working_resolution_m": self.working_resolution_m,
            "warnings": list(self.warnings),
        }


def sources_for_coverage(coverage: str) -> list[ElevationSource]:
    """Sources usable at a location. US locations may also use global sources."""

    if coverage == COVERAGE_UNITED_STATES:
        return list(ELEVATION_SOURCES)
    if coverage == COVERAGE_GLOBAL:
        return [source for source in ELEVATION_SOURCES if source.coverage == COVERAGE_GLOBAL]
    raise ElevationSourceError(f"unsupported coverage tier: {coverage}")


def select_source_pair(
    *,
    coverage: str,
    target_thickness_m: float | None = None,
    available_keys: Sequence[str] | None = None,
    min_epoch_separation_years: float = MIN_EPOCH_SEPARATION_YEARS,
) -> ElevationPair:
    """Choose the pair that can measure the thinnest cover at this location.

    Selection minimises expected noise rather than maximising epoch separation:
    a longer baseline is worthless if neither surface can resolve the cover.
    Ties are broken toward the longer baseline, which is more likely to bracket
    the placement date.
    """

    candidates = sources_for_coverage(coverage)
    if available_keys is not None:
        allowed = set(available_keys)
        candidates = [source for source in candidates if source.key in allowed]
    if not candidates:
        raise ElevationSourceError("no elevation source is available for this coverage")

    epochs: list[ElevationEpoch] = []
    for source in candidates:
        epochs.extend(candidate_epochs(source))
    if len(epochs) < 2:
        raise ElevationSourceError(
            f"at least two elevation epochs are required, found {len(epochs)}"
        )

    pairs: list[ElevationPair] = []
    for early in epochs:
        for late in epochs:
            if early is late:
                continue
            pair = ElevationPair(early=early, late=late)
            if pair.epoch_separation_years < float(min_epoch_separation_years):
                continue
            pairs.append(pair)

    if not pairs:
        raise ElevationSourceError(
            "no source pair has enough epoch separation to measure change"
        )

    best = min(
        pairs,
        key=lambda pair: (pair.expected_sigma_m, -pair.epoch_separation_years),
    )

    warnings: list[str] = []
    if best.working_resolution_m > 10.0:
        warnings.append("coarse_resolution_small_features_unresolvable")
    if target_thickness_m is not None:
        if float(target_thickness_m) < best.minimum_detectable_thickness_m:
            warnings.append("target_thickness_below_detection_floor")
    if best.expected_sigma_m > 1.0:
        warnings.append("expected_noise_exceeds_one_metre")
    if best.same_source:
        # Two vintages of one collection only exist where two acquisition
        # projects happen to overlap the area. The catalogue cannot know that;
        # only a live query against the actual footprint can.
        warnings.append("requires_two_overlapping_vintages_at_this_location")

    return ElevationPair(early=best.early, late=best.late, warnings=tuple(warnings))


def build_ee_elevation_image(epoch: ElevationEpoch, region: Any, *, ee_module: Any = None) -> Any:
    """Build the Earth Engine image for one epoch, clipped to ``region``.

    A multi-vintage collection is filtered to the epoch's acquisition window
    before mosaicking, which is what makes an early-lidar/late-lidar difference
    possible from a single collection.

    ``ee_module`` is injectable so this can be exercised without an Earth Engine
    session; production callers leave it unset.
    """

    if ee_module is None:  # pragma: no cover - exercised only with a live session
        import ee as ee_module  # type: ignore[no-redef]

    source = epoch.source
    if source.asset_kind == ASSET_IMAGE_COLLECTION:
        collection = ee_module.ImageCollection(source.asset_id).filterBounds(region)
        if source.multi_vintage:
            collection = collection.filterDate(
                f"{int(epoch.start_year)}-01-01",
                f"{int(epoch.end_year)}-12-31",
            )
        image = collection.mosaic()
    else:
        image = ee_module.Image(source.asset_id)
    return image.select(source.band).clip(region).toFloat()
