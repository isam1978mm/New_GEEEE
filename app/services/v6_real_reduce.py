"""V6 feature-stack reduction and scorer connection."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Mapping, Sequence

from app.services.v6_real_gee_features import REQUIRED_V6_FEATURE_BANDS, validate_v6_feature_row
from app.services.v6_real_gee_runtime import V6EarthEngineRuntime, V6GridCell
from app.services.v6_real_scoring import V6ScoredCandidate, score_v6_candidates


_SCORING_OPTIONAL_FIELDS: tuple[str, ...] = (
    "sar_contrast",
    "builtup_near_frac",
    "confidence_score_all",
    "stability_score_norm",
    "season_stability_norm",
    "score_gap_from_median",
    "top10_count",
    "top25_count",
    "season_top10_count",
    "season_top25_count",
)


@dataclass(frozen=True)
class V6FeatureReductionConfig:
    scale_m: int = 10
    tile_scale: int = 4

    def __post_init__(self) -> None:
        if isinstance(self.scale_m, bool) or isinstance(self.tile_scale, bool):
            raise ValueError("scale_m and tile_scale must be positive integers")
        if not isinstance(self.scale_m, int) or not isinstance(self.tile_scale, int):
            raise ValueError("scale_m and tile_scale must be positive integers")
        if self.scale_m <= 0 or self.tile_scale <= 0:
            raise ValueError("scale_m and tile_scale must be positive integers")


@dataclass(frozen=True)
class V6ReducedFeatureRow:
    cell_id: str
    grid_row: int | None
    grid_col: int | None
    features: dict[str, float]
    scoring_metadata: dict[str, float]

    def as_scoring_input(self) -> dict[str, Any]:
        return {
            "cell_id": self.cell_id,
            **self.features,
            **self.scoring_metadata,
        }

    def safe_summary(self) -> dict[str, Any]:
        return {
            "cell_id": self.cell_id,
            "grid_row": self.grid_row,
            "grid_col": self.grid_col,
            "feature_count": len(self.features),
            "scoring_metadata_count": len(self.scoring_metadata),
            "contains_feature_values": False,
            "contains_geometry": False,
        }


class V6FeatureStackReducer:
    """Boundary for reducing a feature stack over grid cells.

    Runtime calls happen only here and can be avoided in unit tests by using
    `reduced_feature_rows_from_records` with fake records.
    """

    def __init__(
        self,
        runtime: V6EarthEngineRuntime,
        config: V6FeatureReductionConfig | None = None,
    ) -> None:
        self.runtime = runtime
        self.config = config or V6FeatureReductionConfig()

    def reduce_to_rows(self, *, feature_stack: Any, grid_cells: Sequence[V6GridCell]) -> tuple[V6ReducedFeatureRow, ...]:
        ee = self.runtime.initialize()
        features = []
        for cell in grid_cells:
            geom = ee.Geometry.Rectangle(
                [cell.bounds.west, cell.bounds.south, cell.bounds.east, cell.bounds.north],
                proj=None,
                geodesic=False,
            )
            features.append(
                ee.Feature(
                    geom,
                    {
                        "cell_id": cell.cell_id,
                        "grid_row": cell.row,
                        "grid_col": cell.col,
                    },
                )
            )
        reduced = feature_stack.reduceRegions(
            collection=ee.FeatureCollection(features),
            reducer=ee.Reducer.mean(),
            scale=self.config.scale_m,
            tileScale=self.config.tile_scale,
        )
        response = reduced.getInfo()
        records = response.get("features", []) if isinstance(response, Mapping) else []
        return reduced_feature_rows_from_records(records)


def reduced_feature_rows_from_records(records: Sequence[Mapping[str, Any]]) -> tuple[V6ReducedFeatureRow, ...]:
    rows = [_row_from_record(record, index) for index, record in enumerate(records)]
    return tuple(rows)


def score_reduced_v6_feature_rows(rows: Sequence[V6ReducedFeatureRow]) -> tuple[V6ScoredCandidate, ...]:
    return score_v6_candidates([row.as_scoring_input() for row in rows])


def safe_reduction_summary(rows: Sequence[V6ReducedFeatureRow]) -> dict[str, Any]:
    return {
        "row_count": len(rows),
        "first_cell_id": rows[0].cell_id if rows else None,
        "last_cell_id": rows[-1].cell_id if rows else None,
        "contains_feature_values": False,
        "contains_geometry": False,
    }


def _row_from_record(record: Mapping[str, Any], index: int) -> V6ReducedFeatureRow:
    properties = record.get("properties", record)
    if not isinstance(properties, Mapping):
        raise ValueError(f"reduced feature record {index} has no properties mapping")

    cell_id_raw = properties.get("cell_id")
    if not isinstance(cell_id_raw, str) or not cell_id_raw.strip():
        raise ValueError(f"reduced feature record {index} is missing cell_id")
    cell_id = cell_id_raw.strip()

    issues = validate_v6_feature_row(properties)
    if issues:
        raise ValueError(f"invalid reduced feature row:{cell_id}:" + ";".join(issues))

    features = {band: _finite_float(properties[band], band) for band in REQUIRED_V6_FEATURE_BANDS}
    scoring_metadata = {
        field: _finite_float(properties[field], field)
        for field in _SCORING_OPTIONAL_FIELDS
        if field in properties and properties[field] is not None
    }

    return V6ReducedFeatureRow(
        cell_id=cell_id,
        grid_row=_optional_int(properties.get("grid_row", properties.get("row"))),
        grid_col=_optional_int(properties.get("grid_col", properties.get("col"))),
        features=features,
        scoring_metadata=scoring_metadata,
    )


def _finite_float(value: object, name: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{name} must be a finite number")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a finite number") from exc
    if not math.isfinite(number):
        raise ValueError(f"{name} must be a finite number")
    return number


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        raise ValueError("grid index must be an integer")
    number = _finite_float(value, "grid index")
    if int(number) != number:
        raise ValueError("grid index must be an integer")
    return int(number)
