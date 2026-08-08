"""Direct NASA/NSIDC recovery for the two Campaign 014 ATL08 granules.

SlideRule broad and explicit-resource requests repeatedly returned partial reads
for two ATL08 release-007 granules needed by Campaign 014.  This module provides
an independent recovery path:

* locate/download the exact ATL08 granules with NASA ``earthaccess``;
* store them in a Campaign-014-only local cache;
* read the official 100 m ATL08 land-segment fields directly with ``h5py``;
* return a pandas DataFrame compatible with the existing ICESat-2 repeat-series
  parser.

No scientific threshold, EPA spatial/event gate, generic scanner, application
behavior, or other campaign is changed by this helper.
"""

from __future__ import annotations

import argparse
import math
import re
import sys
from pathlib import Path
from typing import Any, Iterable

if __package__ in (None, ""):
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root))
    sys.path.insert(0, str(Path(__file__).resolve().parent))

CAMPAIGN_ID = "mid_atlantic_earthwork_pilot_v14_epa_hidden_lane_recent_earthwork"
DIRECT_CACHE_DIR = (
    Path("data")
    / "research"
    / "icesat2_broad_track_scan"
    / CAMPAIGN_ID
    / "nsidc_direct_atl08"
)
ATL08_SHORT_NAME = "ATL08"
ATL08_VERSION = "007"
ATL08_EPOCH_UTC = "2018-01-01T00:00:00Z"
GROUND_TRACKS = ("gt1l", "gt1r", "gt2l", "gt2r", "gt3l", "gt3r")

UNRESOLVED_RESOURCES = (
    "ATL08_20210504235905_06291102_007_01.h5",
    "ATL08_20251226145703_01873002_007_01.h5",
)

_FILENAME_RE = re.compile(
    r"^ATL08_\d{14}_(?P<rgt>\d{4})(?P<cycle>\d{2})(?P<region>\d{2})_007_\d{2}\.h5$"
)


class Campaign014DirectRecoveryError(RuntimeError):
    """Raised when direct NASA/NSIDC recovery cannot produce a valid frame."""


def _imports():
    """Load optional direct-recovery dependencies only when this path is used."""

    try:
        import h5py
        import numpy as np
        import pandas as pd
    except ImportError as exc:
        raise Campaign014DirectRecoveryError(
            "Campaign 014 direct recovery requires optional packages h5py, numpy, "
            "and pandas. Install them in the project virtual environment."
        ) from exc
    return h5py, np, pd


def _earthaccess():
    try:
        import earthaccess
    except ImportError as exc:
        raise Campaign014DirectRecoveryError(
            "Campaign 014 direct download requires optional package earthaccess."
        ) from exc
    return earthaccess


def _resource_metadata(resource: str) -> tuple[int, int, int]:
    match = _FILENAME_RE.fullmatch(resource)
    if match is None:
        raise Campaign014DirectRecoveryError(
            f"unexpected ATL08 release-007 resource name: {resource}"
        )
    return (
        int(match.group("rgt")),
        int(match.group("cycle")),
        int(match.group("region")),
    )


def _scalar_int(value: Any) -> int | None:
    try:
        if hasattr(value, "shape") and getattr(value, "shape", None) != ():
            flat = value.reshape(-1)
            if len(flat) != 1:
                return None
            value = flat[0]
        parsed = int(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return parsed


def _dataset(group: Any, relative_path: str, *, required: bool) -> Any | None:
    try:
        return group[relative_path]
    except (KeyError, TypeError):
        if required:
            raise Campaign014DirectRecoveryError(
                f"ATL08 direct file is missing required dataset {group.name}/{relative_path}"
            )
        return None


def _array(group: Any, relative_path: str, *, required: bool, length: int | None = None):
    _h5py, np, _pd = _imports()
    dataset = _dataset(group, relative_path, required=required)
    if dataset is None:
        if length is None:
            return None
        return np.full(length, np.nan)
    values = np.asarray(dataset[:])
    if values.ndim != 1:
        values = values.reshape(-1)
    if length is not None and len(values) != length:
        raise Campaign014DirectRecoveryError(
            f"ATL08 dataset length mismatch at {dataset.name}: {len(values)} != {length}"
        )
    return values


def _polygon_bounds(polygon: list[dict[str, float]]) -> tuple[float, float, float, float]:
    if len(polygon) < 4:
        raise Campaign014DirectRecoveryError("Campaign 014 direct recovery polygon is invalid")
    longitudes = [float(point["lon"]) for point in polygon]
    latitudes = [float(point["lat"]) for point in polygon]
    if not all(math.isfinite(value) for value in (*longitudes, *latitudes)):
        raise Campaign014DirectRecoveryError("Campaign 014 direct recovery polygon is non-finite")
    return min(longitudes), min(latitudes), max(longitudes), max(latitudes)


def _inside_bounds(longitude: Any, latitude: Any, bounds: tuple[float, float, float, float]):
    _h5py, np, _pd = _imports()
    west, south, east, north = bounds
    return (
        np.isfinite(longitude)
        & np.isfinite(latitude)
        & (longitude >= west)
        & (longitude <= east)
        & (latitude >= south)
        & (latitude <= north)
    )


def _beam_frame(
    file_handle: Any,
    *,
    gt: str,
    rgt: int,
    cycle: int,
    region: int,
    bounds: tuple[float, float, float, float],
):
    _h5py, np, pd = _imports()
    if gt not in file_handle:
        return None
    beam = file_handle[gt]
    if "land_segments" not in beam:
        return None
    land = beam["land_segments"]

    latitude = _array(land, "latitude", required=True)
    if latitude is None:
        return None
    length = len(latitude)
    longitude = _array(land, "longitude", required=True, length=length)
    delta_time = _array(land, "delta_time", required=True, length=length)
    segment_id = _array(land, "segment_id_beg", required=True, length=length)
    height = _array(land, "terrain/h_te_median", required=True, length=length)

    uncertainty = _array(land, "terrain/h_te_uncertainty", required=False, length=length)
    ground_photons = _array(land, "terrain/n_te_photons", required=False, length=length)
    terrain_slope = _array(land, "terrain/terrain_slope", required=False, length=length)
    snowcover = _array(land, "segment_snowcover", required=False, length=length)

    spot = _scalar_int(beam.attrs.get("atlas_spot_number"))
    if spot not in {1, 2, 3, 4, 5, 6}:
        raise Campaign014DirectRecoveryError(
            f"ATL08 direct file has no valid atlas_spot_number on {gt}"
        )

    mask = _inside_bounds(longitude, latitude, bounds)
    if not bool(np.any(mask)):
        return None

    selected_delta = np.asarray(delta_time[mask], dtype="float64")
    epoch = pd.Timestamp(ATL08_EPOCH_UTC)
    times = epoch + pd.to_timedelta(selected_delta, unit="s")
    time_ns = times.astype("int64")

    frame = pd.DataFrame(
        {
            "longitude": np.asarray(longitude[mask], dtype="float64"),
            "latitude": np.asarray(latitude[mask], dtype="float64"),
            "h_te_median": np.asarray(height[mask], dtype="float64"),
            "h_te_uncertainty": np.asarray(uncertainty[mask], dtype="float64"),
            "n_te_photons": np.asarray(ground_photons[mask], dtype="float64"),
            "terrain_slope": np.asarray(terrain_slope[mask], dtype="float64"),
            "segment_snowcover": np.asarray(snowcover[mask], dtype="float64"),
            "segment_id_beg": np.asarray(segment_id[mask]),
            "rgt": rgt,
            "cycle": cycle,
            "region": region,
            "spot": spot,
            "gt": gt,
        },
        index=time_ns,
    )
    frame.index.name = "time_ns"
    return frame


def frame_from_local_atl08(
    path: Path,
    *,
    polygon: list[dict[str, float]],
):
    """Read one official ATL08 HDF5 file into the existing scanner frame shape."""

    h5py, _np, pd = _imports()
    path = Path(path)
    if not path.is_file():
        raise Campaign014DirectRecoveryError(f"missing direct ATL08 file: {path}")
    rgt, cycle, region = _resource_metadata(path.name)
    bounds = _polygon_bounds(polygon)

    frames: list[Any] = []
    try:
        with h5py.File(path, "r") as file_handle:
            for gt in GROUND_TRACKS:
                frame = _beam_frame(
                    file_handle,
                    gt=gt,
                    rgt=rgt,
                    cycle=cycle,
                    region=region,
                    bounds=bounds,
                )
                if frame is not None and len(frame):
                    frames.append(frame)
    except OSError as exc:
        raise Campaign014DirectRecoveryError(
            f"cannot read official ATL08 HDF5 file {path.name}: {exc}"
        ) from exc

    if not frames:
        # A clean official granule may legitimately contain no land segments in
        # this particular 25 km tile. Return an empty frame with the expected
        # columns rather than inventing observations.
        empty = pd.DataFrame(
            columns=[
                "longitude",
                "latitude",
                "h_te_median",
                "h_te_uncertainty",
                "n_te_photons",
                "terrain_slope",
                "segment_snowcover",
                "segment_id_beg",
                "rgt",
                "cycle",
                "region",
                "spot",
                "gt",
            ]
        )
        empty.index.name = "time_ns"
        return empty

    combined = pd.concat(frames, axis=0).sort_index()
    combined.attrs["campaign014_direct_source"] = "NASA NSIDC ATL08 release 007 HDF5"
    combined.attrs["campaign014_direct_resource"] = path.name
    return combined


def local_resource_path(resource: str, *, cache_dir: Path = DIRECT_CACHE_DIR) -> Path:
    _resource_metadata(resource)
    return Path(cache_dir) / resource


def load_cached_resource(
    resource: str,
    *,
    polygon: list[dict[str, float]],
    cache_dir: Path = DIRECT_CACHE_DIR,
):
    path = local_resource_path(resource, cache_dir=cache_dir)
    if not path.is_file():
        raise Campaign014DirectRecoveryError(
            "direct NASA/NSIDC copy is not cached for "
            f"{resource}; run the Campaign 014 NSIDC bootstrap first"
        )
    return frame_from_local_atl08(path, polygon=polygon)


def _login(earthaccess: Any) -> Any:
    # Newer earthaccess supports strategy="all" (environment, netrc, then
    # interactive). Keep compatibility with older installed releases.
    try:
        return earthaccess.login(strategy="all")
    except (TypeError, ValueError):
        return earthaccess.login()


def download_resources(
    resources: Iterable[str] = UNRESOLVED_RESOURCES,
    *,
    cache_dir: Path = DIRECT_CACHE_DIR,
) -> list[Path]:
    """Download exact official ATL08 v007 granules using NASA earthaccess."""

    earthaccess = _earthaccess()
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    requested = [str(resource) for resource in resources]
    for resource in requested:
        _resource_metadata(resource)

    missing = [resource for resource in requested if not (cache_dir / resource).is_file()]
    if not missing:
        return [cache_dir / resource for resource in requested]

    _login(earthaccess)
    for resource in missing:
        results = earthaccess.search_data(
            short_name=ATL08_SHORT_NAME,
            version=ATL08_VERSION,
            granule_name=resource,
            count=10,
        )
        if not results:
            raise Campaign014DirectRecoveryError(
                f"NASA CMR returned no ATL08 v007 match for {resource}"
            )
        downloaded = earthaccess.download(results, str(cache_dir))
        paths = [Path(item) for item in downloaded]
        expected = cache_dir / resource
        if not expected.is_file():
            matching = [path for path in paths if path.name == resource and path.is_file()]
            if matching:
                if matching[0] != expected:
                    matching[0].replace(expected)
            else:
                raise Campaign014DirectRecoveryError(
                    f"earthaccess did not produce expected file {resource}"
                )

    return [cache_dir / resource for resource in requested]


def validate_cached_resources(
    *,
    cache_dir: Path = DIRECT_CACHE_DIR,
) -> dict[str, object]:
    """Open both HDF5 files and report their required structural fields."""

    h5py, _np, _pd = _imports()
    report: dict[str, object] = {}
    for resource in UNRESOLVED_RESOURCES:
        path = local_resource_path(resource, cache_dir=cache_dir)
        if not path.is_file():
            report[resource] = {"present": False, "valid_hdf5": False}
            continue
        valid_beams: list[str] = []
        try:
            with h5py.File(path, "r") as file_handle:
                for gt in GROUND_TRACKS:
                    if gt not in file_handle or "land_segments" not in file_handle[gt]:
                        continue
                    land = file_handle[gt]["land_segments"]
                    required = (
                        "delta_time",
                        "latitude",
                        "longitude",
                        "segment_id_beg",
                        "terrain/h_te_median",
                    )
                    if all(name in land for name in required):
                        spot = _scalar_int(file_handle[gt].attrs.get("atlas_spot_number"))
                        if spot in {1, 2, 3, 4, 5, 6}:
                            valid_beams.append(gt)
        except OSError as exc:
            report[resource] = {
                "present": True,
                "valid_hdf5": False,
                "error": str(exc),
            }
            continue
        report[resource] = {
            "present": True,
            "valid_hdf5": len(valid_beams) > 0,
            "valid_beams": valid_beams,
            "size_bytes": path.stat().st_size,
        }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--download",
        action="store_true",
        help="Authenticate with NASA Earthdata if needed and download the two exact ATL08 files.",
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=DIRECT_CACHE_DIR,
        help="Campaign-014-only local cache directory.",
    )
    args = parser.parse_args()

    if args.download:
        paths = download_resources(cache_dir=args.cache_dir)
        for path in paths:
            print(f"direct ATL08 cached: {path}")

    report = validate_cached_resources(cache_dir=args.cache_dir)
    import json

    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if all(
        isinstance(item, dict) and item.get("valid_hdf5") is True
        for item in report.values()
    ) else 1


if __name__ == "__main__":
    raise SystemExit(main())
