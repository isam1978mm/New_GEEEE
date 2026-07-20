"""Run exact-manifest Sentinel-1 feature extraction in small safe batches.

This launcher preserves the existing feature-extraction contract but avoids one
large Earth Engine computation graph. Detailed values and image identities remain
in the private output written by extract_depth_s1_matched_features.py.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any, Callable

import check_depth_s1_coverage as coverage
import extract_depth_s1_matched_features as extractor


DEFAULT_BATCH_SIZE = 10
MAX_BATCH_SIZE = 50


def validate_batch_size(value: int) -> int:
    try:
        size = int(value)
    except (TypeError, ValueError) as exc:
        raise extractor.DepthS1MatchedFeatureError("batch size must be an integer") from exc
    if size < 1 or size > MAX_BATCH_SIZE:
        raise extractor.DepthS1MatchedFeatureError(
            f"batch size must be between 1 and {MAX_BATCH_SIZE}"
        )
    return size


def _chunk_rows(rows: list[dict[str, str]], batch_size: int) -> list[list[dict[str, str]]]:
    return [rows[index : index + batch_size] for index in range(0, len(rows), batch_size)]


def query_exact_s1_feature_summaries_batched(
    *,
    manifest_rows: list[dict[str, str]],
    site_geometry_payload: dict[str, Any],
    background_geometry_payload: dict[str, Any],
    resolution_meters: int,
    batch_size: int = DEFAULT_BATCH_SIZE,
    single_batch_query_fn: Callable[..., list[dict[str, Any]]] | None = None,
) -> list[dict[str, Any]]:
    size = validate_batch_size(batch_size)
    if not isinstance(manifest_rows, list):
        raise extractor.DepthS1MatchedFeatureError("manifest rows must be a list")
    if not manifest_rows:
        return []

    batches = _chunk_rows(manifest_rows, size)
    active_query = single_batch_query_fn or extractor.query_exact_s1_feature_summaries
    combined: list[dict[str, Any]] = []

    for batch_index, batch in enumerate(batches, start=1):
        try:
            returned = active_query(
                manifest_rows=batch,
                site_geometry_payload=site_geometry_payload,
                background_geometry_payload=background_geometry_payload,
                resolution_meters=resolution_meters,
            )
        except Exception as exc:
            raise extractor.DepthS1MatchedFeatureError(
                "Earth Engine matched feature batch failed "
                f"(batch {batch_index} of {len(batches)}, batch_size={len(batch)})"
            ) from exc
        if not isinstance(returned, list):
            raise extractor.DepthS1MatchedFeatureError(
                "Earth Engine matched feature batch returned an invalid response "
                f"(batch {batch_index} of {len(batches)})"
            )
        combined.extend(returned)

    return combined


def run_batched_matched_feature_extraction(
    *,
    site_geojson: Path,
    background_geojson: Path,
    match_manifest: Path,
    output_path: Path | None = None,
    execute: bool = False,
    batch_size: int = DEFAULT_BATCH_SIZE,
    single_batch_query_fn: Callable[..., list[dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    size = validate_batch_size(batch_size)

    def batched_query(**kwargs: Any) -> list[dict[str, Any]]:
        return query_exact_s1_feature_summaries_batched(
            **kwargs,
            batch_size=size,
            single_batch_query_fn=single_batch_query_fn,
        )

    result = extractor.run_matched_feature_extraction(
        site_geojson=site_geojson,
        background_geojson=background_geojson,
        match_manifest=match_manifest,
        output_path=output_path,
        execute=execute,
        query_fn=batched_query,
    )
    total_rows = int(result["manifest_pre_count"]) + int(result["manifest_post_count"])
    planned_batch_count = math.ceil(total_rows / size)
    result.update(
        {
            "batching_enabled": True,
            "batch_size": size,
            "planned_batch_count": planned_batch_count,
            "executed_batch_count": planned_batch_count if result["query_executed"] else 0,
        }
    )
    return result


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Dry-run or execute exact-manifest Sentinel-1 feature extraction in small batches."
    )
    parser.add_argument("--site-geojson", type=Path, required=True)
    parser.add_argument("--background-geojson", type=Path, required=True)
    parser.add_argument("--match-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, help="Required private detailed JSON output with --execute.")
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    parser.add_argument("--execute", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    try:
        result = run_batched_matched_feature_extraction(
            site_geojson=args.site_geojson,
            background_geojson=args.background_geojson,
            match_manifest=args.match_manifest,
            output_path=args.output,
            execute=args.execute,
            batch_size=args.batch_size,
        )
    except (extractor.DepthS1MatchedFeatureError, coverage.DepthS1CoverageError) as exc:
        print(
            json.dumps(
                {
                    "status": "matched_s1_feature_extraction_failed",
                    "error": str(exc),
                    "batching_enabled": True,
                    "batch_size": args.batch_size,
                    "coordinates_printed": False,
                    "geometry_printed": False,
                    "private_paths_printed": False,
                    "image_ids_printed": False,
                    "feature_values_printed": False,
                    "app_depth_enabled": False,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
