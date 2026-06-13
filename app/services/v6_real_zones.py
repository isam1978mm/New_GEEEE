"""V6 request-zone generation from scored candidates."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from app.services.v6_real_gee_runtime import V6AoiBounds, V6GridCell
from app.services.v6_real_scoring import V6ScoredCandidate


@dataclass(frozen=True)
class V6RequestZoneConfig:
    max_zones: int = 25
    zone_id_prefix: str = "V6_RZ"
    quote_id_prefix: str = "V6_QUOTE"

    def __post_init__(self) -> None:
        if isinstance(self.max_zones, bool) or not isinstance(self.max_zones, int):
            raise ValueError("max_zones must be a positive integer")
        if self.max_zones <= 0:
            raise ValueError("max_zones must be a positive integer")
        if not self.zone_id_prefix.strip() or not self.quote_id_prefix.strip():
            raise ValueError("zone and quote prefixes are required")


@dataclass(frozen=True)
class V6RequestZone:
    request_zone_id: str
    source_cell_id: str
    quote_id: str
    final_priority_rank_v6: int
    v6_review_priority_score: float
    v6_false_positive_warning_count: int
    bounds: V6AoiBounds

    def as_csv_row(self) -> dict[str, Any]:
        return {
            "request_zone_id": self.request_zone_id,
            "source_cell_id": self.source_cell_id,
            "quote_id": self.quote_id,
            "final_priority_rank_v6": self.final_priority_rank_v6,
            "v6_review_priority_score": self.v6_review_priority_score,
            "v6_false_positive_warning_count": self.v6_false_positive_warning_count,
        }

    def as_geojson_feature(self) -> dict[str, Any]:
        ring = _bounds_to_polygon_ring(self.bounds)
        return {
            "type": "Feature",
            "properties": self.as_csv_row(),
            "geometry": {
                "type": "Polygon",
                "coordinates": [ring],
            },
        }

    def safe_summary(self) -> dict[str, Any]:
        return {
            "request_zone_id": self.request_zone_id,
            "source_cell_id": self.source_cell_id,
            "quote_id": self.quote_id,
            "final_priority_rank_v6": self.final_priority_rank_v6,
            "v6_review_priority_score": self.v6_review_priority_score,
            "v6_false_positive_warning_count": self.v6_false_positive_warning_count,
            "contains_geometry": False,
            "bounds_values_redacted": True,
        }


def generate_v6_request_zones(
    scored_candidates: Sequence[V6ScoredCandidate],
    grid_cells: Sequence[V6GridCell] | Mapping[str, V6GridCell],
    *,
    config: V6RequestZoneConfig | None = None,
) -> tuple[V6RequestZone, ...]:
    zone_config = config or V6RequestZoneConfig()
    grid_by_id = _grid_by_id(grid_cells)
    ranked_candidates = sorted(
        scored_candidates,
        key=lambda candidate: (candidate.final_priority_rank_v6, candidate.cell_id),
    )[: zone_config.max_zones]

    zones: list[V6RequestZone] = []
    for index, candidate in enumerate(ranked_candidates, start=1):
        cell = grid_by_id.get(candidate.cell_id)
        if cell is None:
            raise ValueError(f"missing_grid_cell_for_candidate:{candidate.cell_id}")
        zones.append(
            V6RequestZone(
                request_zone_id=f"{zone_config.zone_id_prefix}_{index:03d}",
                source_cell_id=candidate.cell_id,
                quote_id=f"{zone_config.quote_id_prefix}_{index:03d}",
                final_priority_rank_v6=candidate.final_priority_rank_v6,
                v6_review_priority_score=candidate.v6_review_priority_score,
                v6_false_positive_warning_count=candidate.v6_false_positive_warning_count,
                bounds=cell.bounds,
            )
        )
    return tuple(zones)


def request_zones_to_csv_rows(zones: Sequence[V6RequestZone]) -> tuple[dict[str, Any], ...]:
    return tuple(zone.as_csv_row() for zone in zones)


def request_zones_to_geojson(zones: Sequence[V6RequestZone]) -> dict[str, Any]:
    return {
        "type": "FeatureCollection",
        "features": [zone.as_geojson_feature() for zone in zones],
    }


def safe_request_zone_summary(zones: Sequence[V6RequestZone]) -> dict[str, Any]:
    return {
        "zone_count": len(zones),
        "first_request_zone_id": zones[0].request_zone_id if zones else None,
        "last_request_zone_id": zones[-1].request_zone_id if zones else None,
        "contains_geometry": False,
        "bounds_values_redacted": True,
    }


def _grid_by_id(grid_cells: Sequence[V6GridCell] | Mapping[str, V6GridCell]) -> dict[str, V6GridCell]:
    if isinstance(grid_cells, Mapping):
        return dict(grid_cells)
    return {cell.cell_id: cell for cell in grid_cells}


def _bounds_to_polygon_ring(bounds: V6AoiBounds) -> list[list[float]]:
    return [
        [bounds.west, bounds.south],
        [bounds.east, bounds.south],
        [bounds.east, bounds.north],
        [bounds.west, bounds.north],
        [bounds.west, bounds.south],
    ]
