"""Run a privacy-safe, multi-date Sentinel-1 feasibility screen for depth work.

This runner reuses the tested neutral feature extraction from
``run_buto_s1_method_screen.py``. Geometry, acquisition-screen manifests and
numeric results must remain outside Git. A site result is exploratory only and
never creates calibration truth, trains a depth model or enables app depth.
"""
from __future__ import annotations

import argparse
import json
import math
import os
from datetime import date
from pathlib import Path
from typing import Any, Callable

import run_buto_s1_method_screen as buto

REPO_ROOT = Path(__file__).resolve().parents[1]
SITE_IDS = (
    "river_road",
    "auburn_mcmaster",
    "john_sevier",
    "sconondoa",
)
SITE_ROLES = (
    "known_cover_surface_response",
    "depth_ordering",
)
MIN_ACCEPTED_ANCHORS = 2
MIN_TOTAL_SAME_ORBIT_SUPPORT = 6
MIN_STABLE_SIGNAL_FEATURES = 2
REQUIRED_CONTROL_FIELDS = (
    "weather_screened",
    "vegetation_screened",
    "construction_inactive",
    "geometry_reviewed",
)


class RadarLinkageScreenError(ValueError):
    """Raised when the exploratory site screen cannot proceed safely."""


def _require_outside_repo(path: Path, label: str) -> None:
    candidate = Path(path).expanduser().resolve(strict=False)
    repository = REPO_ROOT.resolve()
    if candidate == repository or repository in candidate.parents:
        raise RadarLinkageScreenError(f"{label} must remain outside the repository")


def _parse_iso_date(value: Any, label: str) -> str:
    try:
        return date.fromisoformat(str(value)).isoformat()
    except (TypeError, ValueError) as exc:
        raise RadarLinkageScreenError(f"{label} must use YYYY-MM-DD") from exc


def _safe_positive_int(value: Any, label: str) -> int:
    try:
        numeric = int(value)
    except (TypeError, ValueError) as exc:
        raise RadarLinkageScreenError(f"{label} must be an integer") from exc
    if numeric <= 0:
        raise RadarLinkageScreenError(f"{label} must be positive")
    return numeric


def _sanitize_anchor(raw: Any, index: int) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise RadarLinkageScreenError(f"anchor {index} must be an object")
    anchor = {
        "image_date": _parse_iso_date(raw.get("image_date"), f"anchor {index} image date"),
        "support_days": _safe_positive_int(
            raw.get("support_days", buto.DEFAULT_SUPPORT_DAYS),
            f"anchor {index} support days",
        ),
        "accepted": bool(raw.get("accepted", False)),
    }
    for field in REQUIRED_CONTROL_FIELDS:
        anchor[field] = bool(raw.get(field, False))
    if anchor["accepted"] and not all(anchor[field] for field in REQUIRED_CONTROL_FIELDS):
        raise RadarLinkageScreenError(
            f"accepted anchor {index} must pass all confounder controls"
        )
    return anchor


def load_screen_manifest(path: Path, expected_site_id: str) -> dict[str, Any]:
    path = Path(path)
    _require_outside_repo(path, "acquisition-screen manifest")
    if not path.is_file():
        raise RadarLinkageScreenError("acquisition-screen manifest is missing")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RadarLinkageScreenError(
            "acquisition-screen manifest is unreadable or invalid JSON"
        ) from exc
    if not isinstance(payload, dict):
        raise RadarLinkageScreenError("acquisition-screen manifest must be an object")
    site_id = str(payload.get("site_id", ""))
    if site_id != expected_site_id:
        raise RadarLinkageScreenError("manifest site_id does not match --site-id")
    raw_anchors = payload.get("anchors")
    if not isinstance(raw_anchors, list) or not raw_anchors:
        raise RadarLinkageScreenError("manifest must contain at least one anchor")
    anchors = [_sanitize_anchor(raw, index + 1) for index, raw in enumerate(raw_anchors)]
    accepted_dates = [anchor["image_date"] for anchor in anchors if anchor["accepted"]]
    if len(accepted_dates) != len(set(accepted_dates)):
        raise RadarLinkageScreenError("accepted anchor dates must be unique")
    return {
        "site_id": site_id,
        "anchors": anchors,
        "accepted_anchor_count": len(accepted_dates),
    }


def _direction(value: Any) -> str:
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise RadarLinkageScreenError("anchor result contains an invalid feature delta") from exc
    if not math.isfinite(numeric):
        raise RadarLinkageScreenError("anchor result contains a non-finite feature delta")
    if numeric > 1e-9:
        return "positive"
    if numeric < -1e-9:
        return "negative"
    return "zero"


def aggregate_anchor_results(
    anchor_results: list[dict[str, Any]], *, site_role: str
) -> dict[str, Any]:
    conclusive = [
        item
        for item in anchor_results
        if item.get("spatial_agreement_decision")
        in {"spatial_agreement_supported", "spatial_agreement_not_supported"}
    ]
    supported = [
        item
        for item in conclusive
        if item.get("spatial_agreement_decision") == "spatial_agreement_supported"
    ]
    total_same_orbit_support = sum(
        int(item.get("same_orbit_support_count") or 0) for item in conclusive
    )

    feature_summary: dict[str, Any] = {}
    stable_signal_feature_count = 0
    for feature in buto.SIGNAL_FEATURE_NAMES:
        directions: list[str] = []
        for item in conclusive:
            raw_feature = item.get("exact_feature_summary", {}).get(feature)
            if not isinstance(raw_feature, dict):
                continue
            if not raw_feature.get("stable_direction"):
                continue
            directions.append(
                _direction(raw_feature.get("exact_target_minus_background_median"))
            )
        non_zero = [value for value in directions if value != "zero"]
        positive = non_zero.count("positive")
        negative = non_zero.count("negative")
        dominant = "positive" if positive >= negative else "negative"
        dominant_count = max(positive, negative)
        same_direction_fraction = dominant_count / len(non_zero) if non_zero else None
        stable = bool(
            len(non_zero) >= MIN_ACCEPTED_ANCHORS
            and same_direction_fraction is not None
            and same_direction_fraction >= 2 / 3
        )
        if stable:
            stable_signal_feature_count += 1
        feature_summary[feature] = {
            "conclusive_anchor_count": len(non_zero),
            "dominant_direction": dominant if non_zero else "none",
            "same_direction_fraction": same_direction_fraction,
            "stable_across_anchors": stable,
        }

    if len(conclusive) < MIN_ACCEPTED_ANCHORS:
        site_decision = "site_screen_inconclusive"
    elif (
        len(supported) >= MIN_ACCEPTED_ANCHORS
        and total_same_orbit_support >= MIN_TOTAL_SAME_ORBIT_SUPPORT
        and stable_signal_feature_count >= MIN_STABLE_SIGNAL_FEATURES
    ):
        site_decision = "site_surface_response_supported"
    else:
        site_decision = "site_surface_response_not_supported"

    if site_role == "depth_ordering" and site_decision == "site_surface_response_supported":
        ordering_decision = "site_depth_ordering_signal_supported_exploratory"
    elif site_role == "depth_ordering":
        ordering_decision = "site_depth_ordering_not_supported_or_inconclusive"
    else:
        ordering_decision = "depth_ordering_not_available_at_this_site_stage"

    return {
        "conclusive_anchor_count": len(conclusive),
        "supported_anchor_count": len(supported),
        "total_same_orbit_support_count": total_same_orbit_support,
        "stable_signal_feature_count": stable_signal_feature_count,
        "feature_direction_summary": feature_summary,
        "site_surface_response_decision": site_decision,
        "site_depth_ordering_decision": ordering_decision,
        "cross_site_depth_linkage_decision": "not_evaluated_single_site_result",
    }


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        temporary.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        os.replace(temporary, path)
    except OSError as exc:
        raise RadarLinkageScreenError("site-screen output could not be written") from exc
    finally:
        if temporary.exists():
            temporary.unlink()


def run_site_screen(
    *,
    site_id: str,
    site_role: str,
    target_geojson: Path,
    comparison_geojson: Path,
    manifest_path: Path,
    analysis_scale_meters: int = buto.DEFAULT_ANALYSIS_SCALE_METERS,
    execute: bool = False,
    output_path: Path | None = None,
    query_fn: Callable[..., list[dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    if site_id not in SITE_IDS:
        raise RadarLinkageScreenError("unsupported site_id")
    if site_role not in SITE_ROLES:
        raise RadarLinkageScreenError("unsupported site role")
    analysis_scale_meters = _safe_positive_int(
        analysis_scale_meters, "analysis scale"
    )
    try:
        target = buto.load_local_geometry(target_geojson, "target geometry")
        comparison = buto.load_local_geometry(
            comparison_geojson, "comparison geometry"
        )
    except buto.ButoMethodScreenError as exc:
        raise RadarLinkageScreenError(str(exc)) from exc
    if target == comparison:
        raise RadarLinkageScreenError("target and comparison geometries must be different")
    manifest = load_screen_manifest(manifest_path, site_id)
    accepted = [anchor for anchor in manifest["anchors"] if anchor["accepted"]]

    result: dict[str, Any] = {
        "status": "site_screen_dry_run_ready",
        "site_id": site_id,
        "site_role": site_role,
        "query_executed": False,
        "analysis_scale_meters": analysis_scale_meters,
        "accepted_anchor_count": len(accepted),
        "comparison_area_is_confirmed_negative": False,
        "coordinates_printed": False,
        "image_ids_printed": False,
        "private_paths_printed": False,
        "depth_measured": False,
        "training_started": False,
        "calibration_record_created": False,
        "app_depth_enabled": False,
        "output_written": False,
    }

    if execute:
        if len(accepted) < MIN_ACCEPTED_ANCHORS:
            result.update(
                {
                    "status": "site_screen_not_ready_insufficient_accepted_anchors",
                    "site_surface_response_decision": "site_screen_inconclusive",
                    "site_depth_ordering_decision": "site_screen_inconclusive",
                    "cross_site_depth_linkage_decision": "not_evaluated_single_site_result",
                }
            )
        else:
            active_query = query_fn or buto.query_s1_region_summaries
            anchor_results: list[dict[str, Any]] = []
            for anchor in accepted:
                rows = active_query(
                    target_geometry_payload=target,
                    background_geometry_payload=comparison,
                    image_date=anchor["image_date"],
                    support_days=anchor["support_days"],
                    analysis_scale_meters=analysis_scale_meters,
                )
                anchor_result = buto.summarize_rows(
                    rows, image_date=anchor["image_date"]
                )
                anchor_result["image_date"] = anchor["image_date"]
                anchor_result["support_days"] = anchor["support_days"]
                anchor_results.append(anchor_result)
            result.update(aggregate_anchor_results(anchor_results, site_role=site_role))
            result["anchor_results"] = anchor_results
            result["status"] = "site_screen_complete"
            result["query_executed"] = True

    if output_path is not None:
        _require_outside_repo(output_path, "site-screen output")
        result["output_written"] = True
        _atomic_write_json(Path(output_path), result)
    return result


def redacted_console_summary(result: dict[str, Any]) -> dict[str, Any]:
    safe_keys = (
        "status",
        "site_id",
        "site_role",
        "query_executed",
        "analysis_scale_meters",
        "accepted_anchor_count",
        "conclusive_anchor_count",
        "supported_anchor_count",
        "total_same_orbit_support_count",
        "stable_signal_feature_count",
        "site_surface_response_decision",
        "site_depth_ordering_decision",
        "cross_site_depth_linkage_decision",
        "comparison_area_is_confirmed_negative",
        "coordinates_printed",
        "image_ids_printed",
        "private_paths_printed",
        "depth_measured",
        "training_started",
        "calibration_record_created",
        "app_depth_enabled",
        "output_written",
    )
    return {key: result[key] for key in safe_keys if key in result}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a multi-date Sentinel-1 depth-linkage feasibility screen."
    )
    parser.add_argument("--site-id", choices=SITE_IDS, required=True)
    parser.add_argument("--site-role", choices=SITE_ROLES, required=True)
    parser.add_argument("--target-geojson", type=Path, required=True)
    parser.add_argument("--comparison-geojson", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument(
        "--analysis-scale-meters",
        type=int,
        default=buto.DEFAULT_ANALYSIS_SCALE_METERS,
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Query Earth Engine. Without this flag, validate private inputs only.",
    )
    parser.add_argument("--output", type=Path, help="Detailed JSON path outside Git.")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    try:
        result = run_site_screen(
            site_id=args.site_id,
            site_role=args.site_role,
            target_geojson=args.target_geojson,
            comparison_geojson=args.comparison_geojson,
            manifest_path=args.manifest,
            analysis_scale_meters=args.analysis_scale_meters,
            execute=args.execute,
            output_path=args.output,
        )
    except RadarLinkageScreenError as exc:
        print(
            json.dumps(
                {
                    "status": "site_screen_failed",
                    "error": str(exc),
                    "coordinates_printed": False,
                    "image_ids_printed": False,
                    "private_paths_printed": False,
                    "depth_measured": False,
                    "app_depth_enabled": False,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 1
    print(json.dumps(redacted_console_summary(result), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
