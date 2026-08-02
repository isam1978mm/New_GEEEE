"""Report which public elevation sources actually have data over a run's area.

The source catalogue records what each product *should* provide. It cannot know
what exists over one particular patch of ground: lidar is flown project by
project, so a collection that covers most of a country can still be empty over
a specific site.

This asks Earth Engine directly and prints, per source:

- whether the asset resolves at all;
- how many images intersect the run's area;
- the band names actually present;
- the acquisition dates actually present.

Run it whenever the measurement stage reports an empty collection, an unknown
band, or an unavailable asset. It changes nothing and writes nothing.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in (None, ""):  # pragma: no cover - direct script execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import ee  # noqa: E402

from app.config import Settings  # noqa: E402
from app.pipeline.elevation_change.sources import (  # noqa: E402
    ASSET_IMAGE_COLLECTION,
    ELEVATION_SOURCES,
)
from app.pipeline.stages.dem import build_grid_region  # noqa: E402
from app.pipeline.stages.grid import grid_spec_from_manifest  # noqa: E402
from app.services.ee_session import initialize_ee_session  # noqa: E402
from app.services.grid import GridManifest  # noqa: E402


def _load_region(run_dir: Path):
    manifest_path = run_dir / "grid_manifest.json"
    if not manifest_path.is_file():
        raise SystemExit(f"missing grid manifest: {manifest_path}")
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    grid_spec = grid_spec_from_manifest(GridManifest(**payload))
    return build_grid_region(grid_spec), grid_spec


def _safe(callable_obj, default=None):
    """Earth Engine raises for many ordinary 'nothing here' cases."""

    try:
        return callable_obj()
    except Exception as exc:  # noqa: BLE001 - reporting tool, never fatal
        return f"<error: {type(exc).__name__}: {str(exc)[:160]}>" if default is None else default


def _millis_to_date(value: Any) -> Any:
    if not isinstance(value, (int, float)):
        return value
    return _safe(lambda: ee.Date(value).format("YYYY-MM-dd").getInfo())


def inspect(run_dir: Path) -> int:
    settings = Settings()
    initialize_ee_session(settings)
    region, grid_spec = _load_region(run_dir)

    print(f"Run grid : {grid_spec.crs}, {grid_spec.size} px at {grid_spec.manifest.scale_m} m")
    print(f"Centre   : approximately {grid_spec.manifest.bounds_m}")
    print()

    usable: list[str] = []

    for source in ELEVATION_SOURCES:
        print(f"=== {source.key}  ({source.asset_id}) ===")
        print(f"    expected band      : {source.band}")

        if source.asset_kind == ASSET_IMAGE_COLLECTION:
            collection = _safe(lambda s=source: ee.ImageCollection(s.asset_id).filterBounds(region))
            if isinstance(collection, str):
                print(f"    asset              : {collection}")
                print()
                continue

            count = _safe(lambda c=collection: c.size().getInfo())
            print(f"    images over the AOI: {count}")

            if isinstance(count, int) and count > 0:
                bands = _safe(lambda c=collection: c.first().bandNames().getInfo())
                print(f"    actual band names  : {bands}")
                start = _safe(
                    lambda c=collection: c.aggregate_min("system:time_start").getInfo()
                )
                end = _safe(lambda c=collection: c.aggregate_max("system:time_start").getInfo())
                print(f"    earliest date      : {_millis_to_date(start)}")
                print(f"    latest date        : {_millis_to_date(end)}")
                if isinstance(bands, list) and source.band in bands:
                    usable.append(source.key)
                else:
                    print("    NOTE: expected band is not in the actual band list")
            else:
                print("    NOTE: no images here, so this source cannot be used at this location")
        else:
            image = _safe(lambda s=source: ee.Image(s.asset_id))
            if isinstance(image, str):
                print(f"    asset              : {image}")
                print()
                continue
            bands = _safe(lambda i=image: i.bandNames().getInfo())
            print(f"    actual band names  : {bands}")
            if isinstance(bands, list) and source.band in bands:
                # A global single image still needs real values over the AOI.
                sample = _safe(
                    lambda i=image, s=source: i.select(s.band)
                    .reduceRegion(
                        reducer=ee.Reducer.mean(),
                        geometry=region,
                        scale=max(30, int(s.resolution_m)),
                        maxPixels=1_000_000,
                        bestEffort=True,
                    )
                    .getInfo()
                )
                print(f"    mean over the AOI  : {sample}")
                if isinstance(sample, dict) and sample.get(source.band) is not None:
                    usable.append(source.key)
                else:
                    print("    NOTE: no valid pixels here")
            else:
                print("    NOTE: expected band is not in the actual band list")
        print()

    print("=" * 60)
    print(f"USABLE AT THIS LOCATION: {usable if usable else 'none'}")
    if len(usable) < 2:
        print()
        print("Fewer than two usable sources means no elevation difference is")
        print("possible here. That is a real limit of the public data at this")
        print("location, not a software fault.")
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Report which public elevation sources have data over a run's area.",
    )
    parser.add_argument("--run-dir", required=True, type=Path)
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    return inspect(args.run_dir)


if __name__ == "__main__":
    raise SystemExit(main())
