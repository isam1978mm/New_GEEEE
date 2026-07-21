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

MODE_REDUCED_FEATURE_BANDS: tuple[str, ...] = ("worldcover_class",)
MEAN_REDUCED_FEATURE_BANDS: tuple[str, ...] = tuple(
    band for band in REQUIRED_V6_FEATURE_BANDS if band not in MODE_REDUCED_FEATURE_BANDS
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

        feature_collection = ee.FeatureCollection(features)
        mean_reduced = feature_stack.select(list(MEAN_REDUCED_FEATURE_BANDS)).reduceRegions(
            collection=feature_collection,
            reducer=ee.Reducer.mean(),
            scale=self.config.scale_m,
            tileScale=self.config.tile_scale,
        )
        mode_reduced = feature_stack.select(list(MODE_REDUCED_FEATURE_BANDS)).reduceRegions(
            collection=feature_collection,
            reducer=ee.Reducer.mode(),
            scale=self.config.scale_m,
            tileScale=self.config.tile_scale,
        )

        mean_records = _records_from_response(mean_reduced.getInfo(), "continuous mean")
        mode_records = _records_from_response(mode_reduced.getInfo(), "categorical mode")
        merged_records = merge_reduced_feature_records(mean_records, mode_records)
        return reduced_feature_rows_from_records(merged_records)


def merge_reduced_feature_records(
    mean_records: Sequence[Mapping[str, Any]],
    mode_records: Sequence[Mapping[str, Any]],
) -> tuple[Mapping[str, Any], ...]:
    """Merge continuous-mean and categorical-mode rows by stable cell identity."""

    mode_by_cell = _index_records_by_cell_id(mode_records, "categorical mode")
    merged: list[Mapping[str, Any]] = []
    seen_mean_cells: set[str] = set()

    for index, mean_record in enumerate(mean_records):
        mean_properties = _record_properties(mean_record, index, "continuous mean")
        cell_id = _required_cell_id(mean_properties, index, "continuous mean")
        if cell_id in seen_mean_cells:
            raise ValueError(f"continuous mean reduction contains duplicate cell_id:{cell_id}")
        seen_mean_cells.add(cell_id)

        mode_record = mode_by_cell.pop(cell_id, None)
        if mode_record is None:
            raise ValueError(f"categorical mode reduction is missing cell_id:{cell_id}")
        mode_properties = _record_properties(mode_record, index, "categorical mode")
        _validate_matching_grid_identity(cell_id, mean_properties, mode_properties)

        merged_properties = dict(mean_properties)
        for band in MODE_REDUCED_FEATURE_BANDS:
            if band not in mode_properties:
                raise ValueError(f"categorical mode reduction is missing {band}:{cell_id}")
            merged_properties[band] = mode_properties[band]

        merged_record = dict(mean_record)
        merged_record["properties"] = merged_properties
        merged.append(merged_record)

    if mode_by_cell:
        extra_cells = ",".join(sorted(mode_by_cell))
        raise ValueError(f"categorical mode reduction contains unexpected cell_id values:{extra_cells}")

    return tuple(merged)


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


def _records_from_response(response: object, reduction_name: str) -> tuple[Mapping[str, Any], ...]:
    if not isinstance(response, Mapping):
        raise ValueError(f"{reduction_name} reduction returned no feature mapping")
    records = response.get("features")
    if not isinstance(records, Sequence) or isinstance(records, (str, bytes)):
        raise ValueError(f"{reduction_name} reduction returned no feature list")
    normalized: list[Mapping[str, Any]] = []
    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            raise ValueError(f"{reduction_name} reduction record {index} is invalid")
        normalized.append(record)
    return tuple(normalized)


def _index_records_by_cell_id(
    records: Sequence[Mapping[str, Any]],
    reduction_name: str,
) -> dict[str, Mapping[str, Any]]:
    indexed: dict[str, Mapping[str, Any]] = {}
    for index, record in enumerate(records):
        properties = _record_properties(record, index, reduction_name)
        cell_id = _required_cell_id(properties, index, reduction_name)
        if cell_id in indexed:
            raise ValueError(f"{reduction_name} reduction contains duplicate cell_id:{cell_id}")
        indexed[cell_id] = record
    return indexed


def _record_properties(record: Mapping[str, Any], index: int, reduction_name: str) -> Mapping[str, Any]:
    properties = record.get("properties", record)
    if not isinstance(properties, Mapping):
        raise ValueError(f"{reduction_name} reduction record {index} has no properties mapping")
    return properties


def _required_cell_id(properties: Mapping[str, Any], index: int, reduction_name: str) -> str:
    cell_id_raw = properties.get("cell_id")
    if not isinstance(cell_id_raw, str) or not cell_id_raw.strip():
        raise ValueError(f"{reduction_name} reduction record {index} is missing cell_id")
    return cell_id_raw.strip()


def _validate_matching_grid_identity(
    cell_id: str,
    mean_properties: Mapping[str, Any],
    mode_properties: Mapping[str, Any],
) -> None:
    for field in ("grid_row", "grid_col"):
        mean_value = mean_properties.get(field)
        mode_value = mode_properties.get(field)
        if mean_value is not None and mode_value is not None and mean_value != mode_value:
            raise ValueError(f"reduction grid identity mismatch:{cell_id}:{field}")


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
