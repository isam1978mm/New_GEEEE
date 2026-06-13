"""V6 scoring and ranking over reduced feature rows."""

from __future__ import annotations

from dataclasses import dataclass, asdict
import math
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class V6ScoringThresholds:
    builtup_warning_frac: float = 0.02
    builtup_near_warning_frac: float = 0.05
    cropland_heavy_frac: float = 0.65
    water_edge_warning_frac: float = 0.05
    v6_strong_built_frac: float = 0.01
    v6_building_near_frac: float = 0.03
    v6_road_like_edge_frac: float = 0.08
    v6_modern_corridor_frac: float = 0.025


@dataclass(frozen=True)
class V6ScoredCandidate:
    cell_id: str
    candidate_score: float
    remote_sensing_contrast: float
    s2_confidence: float
    builtup_warning: int
    cropland_heavy_warning: int
    water_edge_warning: int
    modern_linear_edge_warning: int
    v6_building_warning: int
    v6_road_like_warning: int
    false_positive_warning_count: int
    v6_false_positive_warning_count: int
    v6_false_positive_penalty: float
    v6_quality_adjusted_score: float
    v6_no_warning_bonus: float
    v6_review_priority_score: float
    final_priority_rank_v6: int

    def safe_summary(self) -> dict[str, Any]:
        return {
            "cell_id": self.cell_id,
            "final_priority_rank_v6": self.final_priority_rank_v6,
            "v6_review_priority_score": self.v6_review_priority_score,
            "v6_false_positive_warning_count": self.v6_false_positive_warning_count,
            "contains_geometry": False,
        }

    def as_package_row(self) -> dict[str, Any]:
        return asdict(self)


def score_v6_candidates(
    rows: Sequence[Mapping[str, Any]],
    *,
    thresholds: V6ScoringThresholds | None = None,
) -> tuple[V6ScoredCandidate, ...]:
    """Score and rank reduced V6 feature rows.

    This is a pure-Python scoring step. It does not call external geospatial
    services and does not require package-writer code.
    """

    config = thresholds or V6ScoringThresholds()
    prepared = [_prepare_row(row, config) for row in rows]
    if not prepared:
        return ()

    spectral_q75 = _quantile([row["spectral_contrast"] for row in prepared], 0.75)
    terrain_median = _quantile([row["terrain_score"] for row in prepared], 0.50)

    for row in prepared:
        row["builtup_warning"] = int(
            row["builtup_frac"] >= config.builtup_warning_frac
            or row["builtup_near_frac"] >= config.builtup_near_warning_frac
        )
        row["cropland_heavy_warning"] = int(row["cropland_frac"] >= config.cropland_heavy_frac)
        row["water_edge_warning"] = int(row["water_edge_frac"] >= config.water_edge_warning_frac)
        row["modern_linear_edge_warning"] = int(
            row["spectral_contrast"] >= spectral_q75
            and row["terrain_score"] <= terrain_median
            and (
                row["builtup_warning"] == 1
                or row["cropland_heavy_warning"] == 1
                or row["water_edge_warning"] == 1
            )
        )
        row["v6_building_warning"] = int(
            row["v6_strong_built_frac"] >= config.v6_strong_built_frac
            or row["v6_building_near_frac"] >= config.v6_building_near_frac
        )
        row["v6_road_like_warning"] = int(
            row["v6_road_like_edge_frac"] >= config.v6_road_like_edge_frac
            or row["v6_modern_corridor_frac"] >= config.v6_modern_corridor_frac
        )
        row["false_positive_warning_count"] = (
            row["builtup_warning"]
            + row["cropland_heavy_warning"]
            + row["water_edge_warning"]
            + row["modern_linear_edge_warning"]
        )
        row["v6_false_positive_warning_count"] = (
            row["v6_building_warning"]
            + row["v6_road_like_warning"]
            + row["cropland_heavy_warning"]
            + row["water_edge_warning"]
        )
        row["v6_false_positive_penalty"] = _clip01(row["v6_false_positive_warning_count"] * 0.07, upper=0.28)
        row["v6_quality_adjusted_score"] = row["candidate_score"] * (1 - row["v6_false_positive_penalty"])
        row["v6_no_warning_bonus"] = _clip01(1 - (min(row["v6_false_positive_warning_count"], 4) / 4))

    quality_norm = _norm_values([row["v6_quality_adjusted_score"] for row in prepared])
    gap_norm = _norm_values([row["score_gap_from_median"] for row in prepared])

    for index, row in enumerate(prepared):
        row["v6_review_priority_score"] = _clip01(
            0.35 * quality_norm[index]
            + 0.25 * _clip01(row["confidence_score_all"])
            + 0.20 * _clip01(row["stability_score_norm"])
            + 0.10 * _clip01(row["season_stability_norm"])
            + 0.05 * gap_norm[index]
            + 0.05 * row["v6_no_warning_bonus"]
        )

    ranked = sorted(
        prepared,
        key=lambda row: (
            row["v6_false_positive_warning_count"],
            -row["top10_count"],
            -row["season_top10_count"],
            -row["top25_count"],
            -row["season_top25_count"],
            -row["v6_review_priority_score"],
            row["cell_id"],
        ),
    )

    return tuple(_scored_candidate_from_row(row, rank=index + 1) for index, row in enumerate(ranked))


def validate_v6_scoring_input_row(row: Mapping[str, Any]) -> tuple[str, ...]:
    issues: list[str] = []
    if not isinstance(row.get("cell_id"), str) or not str(row.get("cell_id")).strip():
        issues.append("missing_cell_id")
    for field in _SCORING_NUMERIC_FIELDS:
        if field not in row:
            issues.append(f"missing_score_feature:{field}")
            continue
        try:
            _finite_float(row[field], field)
        except ValueError:
            issues.append(f"invalid_score_feature:{field}")
    return tuple(issues)


_SCORING_NUMERIC_FIELDS = (
    "visibility_score",
    "spectral_contrast",
    "terrain_score",
    "s2_count",
    "builtup_frac",
    "cropland_frac",
    "water_edge_frac",
    "v6_strong_built_frac",
    "v6_building_near_frac",
    "v6_road_like_edge_frac",
    "v6_modern_corridor_frac",
)


def _prepare_row(row: Mapping[str, Any], thresholds: V6ScoringThresholds) -> dict[str, Any]:
    issues = validate_v6_scoring_input_row(row)
    if issues:
        raise ValueError("invalid V6 scoring row:" + ";".join(issues))

    spectral_contrast = _finite_float(row["spectral_contrast"], "spectral_contrast")
    sar_contrast = _finite_float(row.get("sar_contrast", spectral_contrast), "sar_contrast")
    remote_sensing_contrast = _clip01((0.70 * spectral_contrast) + (0.30 * sar_contrast))
    s2_count = _finite_float(row["s2_count"], "s2_count")
    s2_confidence = _clip01(s2_count / 8)

    visibility_score = _clip01(_finite_float(row["visibility_score"], "visibility_score"))
    terrain_score = _clip01(_finite_float(row["terrain_score"], "terrain_score"))
    candidate_score = _clip01(
        0.35 * visibility_score
        + 0.35 * remote_sensing_contrast
        + 0.20 * terrain_score
        + 0.10 * s2_confidence
    )

    return {
        "cell_id": str(row["cell_id"]).strip(),
        "candidate_score": candidate_score,
        "remote_sensing_contrast": remote_sensing_contrast,
        "s2_confidence": s2_confidence,
        "visibility_score": visibility_score,
        "spectral_contrast": spectral_contrast,
        "terrain_score": terrain_score,
        "builtup_frac": _clip01(_finite_float(row["builtup_frac"], "builtup_frac")),
        "builtup_near_frac": _clip01(_finite_float(row.get("builtup_near_frac", 0), "builtup_near_frac")),
        "cropland_frac": _clip01(_finite_float(row["cropland_frac"], "cropland_frac")),
        "water_edge_frac": _clip01(_finite_float(row["water_edge_frac"], "water_edge_frac")),
        "v6_strong_built_frac": _clip01(_finite_float(row["v6_strong_built_frac"], "v6_strong_built_frac")),
        "v6_building_near_frac": _clip01(_finite_float(row["v6_building_near_frac"], "v6_building_near_frac")),
        "v6_road_like_edge_frac": _clip01(_finite_float(row["v6_road_like_edge_frac"], "v6_road_like_edge_frac")),
        "v6_modern_corridor_frac": _clip01(_finite_float(row["v6_modern_corridor_frac"], "v6_modern_corridor_frac")),
        "confidence_score_all": _clip01(_finite_float(row.get("confidence_score_all", s2_confidence), "confidence_score_all")),
        "stability_score_norm": _clip01(_finite_float(row.get("stability_score_norm", 0), "stability_score_norm")),
        "season_stability_norm": _clip01(_finite_float(row.get("season_stability_norm", 0), "season_stability_norm")),
        "score_gap_from_median": _finite_float(row.get("score_gap_from_median", 0), "score_gap_from_median"),
        "top10_count": int(_finite_float(row.get("top10_count", 0), "top10_count")),
        "top25_count": int(_finite_float(row.get("top25_count", 0), "top25_count")),
        "season_top10_count": int(_finite_float(row.get("season_top10_count", 0), "season_top10_count")),
        "season_top25_count": int(_finite_float(row.get("season_top25_count", 0), "season_top25_count")),
    }


def _scored_candidate_from_row(row: Mapping[str, Any], *, rank: int) -> V6ScoredCandidate:
    return V6ScoredCandidate(
        cell_id=str(row["cell_id"]),
        candidate_score=round(float(row["candidate_score"]), 6),
        remote_sensing_contrast=round(float(row["remote_sensing_contrast"]), 6),
        s2_confidence=round(float(row["s2_confidence"]), 6),
        builtup_warning=int(row["builtup_warning"]),
        cropland_heavy_warning=int(row["cropland_heavy_warning"]),
        water_edge_warning=int(row["water_edge_warning"]),
        modern_linear_edge_warning=int(row["modern_linear_edge_warning"]),
        v6_building_warning=int(row["v6_building_warning"]),
        v6_road_like_warning=int(row["v6_road_like_warning"]),
        false_positive_warning_count=int(row["false_positive_warning_count"]),
        v6_false_positive_warning_count=int(row["v6_false_positive_warning_count"]),
        v6_false_positive_penalty=round(float(row["v6_false_positive_penalty"]), 6),
        v6_quality_adjusted_score=round(float(row["v6_quality_adjusted_score"]), 6),
        v6_no_warning_bonus=round(float(row["v6_no_warning_bonus"]), 6),
        v6_review_priority_score=round(float(row["v6_review_priority_score"]), 6),
        final_priority_rank_v6=rank,
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


def _clip01(value: float, *, upper: float = 1.0) -> float:
    return max(0.0, min(float(value), upper))


def _norm_values(values: Sequence[float]) -> list[float]:
    if not values:
        return []
    min_value = min(values)
    max_value = max(values)
    if max_value == min_value:
        return [1.0 for _ in values]
    return [(value - min_value) / (max_value - min_value) for value in values]


def _quantile(values: Sequence[float], q: float) -> float:
    if not values:
        raise ValueError("values must not be empty")
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * q
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[int(position)]
    lower_value = ordered[lower]
    upper_value = ordered[upper]
    return lower_value + ((upper_value - lower_value) * (position - lower))
