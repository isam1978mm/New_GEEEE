from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

h5py = pytest.importorskip("h5py")

MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / "scripts"
    / "recover_campaign_014_nsidc_atl08.py"
)
SPEC = importlib.util.spec_from_file_location("campaign014_nsidc", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _polygon() -> list[dict[str, float]]:
    return [
        {"lon": -77.50, "lat": 38.90},
        {"lon": -77.40, "lat": 38.90},
        {"lon": -77.40, "lat": 39.10},
        {"lon": -77.50, "lat": 39.10},
        {"lon": -77.50, "lat": 38.90},
    ]


def _write_synthetic(path: Path) -> None:
    with h5py.File(path, "w") as handle:
        beam = handle.create_group("gt1l")
        beam.attrs["atlas_spot_number"] = 6
        land = beam.create_group("land_segments")
        land.create_dataset("delta_time", data=np.array([100.0, 200.0, 300.0]))
        land.create_dataset("latitude", data=np.array([38.95, 39.00, 41.00]))
        land.create_dataset("longitude", data=np.array([-77.45, -77.46, -77.45]))
        land.create_dataset("segment_id_beg", data=np.array([101, 102, 103]))
        land.create_dataset("segment_snowcover", data=np.array([1, 1, 1]))
        terrain = land.create_group("terrain")
        terrain.create_dataset("h_te_median", data=np.array([100.5, 101.0, 999.0]))
        terrain.create_dataset("h_te_uncertainty", data=np.array([0.2, 0.3, 0.4]))
        terrain.create_dataset("n_te_photons", data=np.array([8, 9, 10]))
        terrain.create_dataset("terrain_slope", data=np.array([0.01, 0.02, 0.03]))


def test_resource_metadata_decodes_rgt_cycle_region():
    assert MODULE._resource_metadata(
        "ATL08_20210504235905_06291102_007_01.h5"
    ) == (629, 11, 2)


def test_local_hdf5_reader_returns_existing_scanner_shape(tmp_path: Path):
    path = tmp_path / "ATL08_20210504235905_06291102_007_01.h5"
    _write_synthetic(path)

    frame = MODULE.frame_from_local_atl08(path, polygon=_polygon())

    assert len(frame) == 2
    assert frame.index.name == "time_ns"
    assert set(
        [
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
    ).issubset(frame.columns)
    assert frame["rgt"].tolist() == [629, 629]
    assert frame["cycle"].tolist() == [11, 11]
    assert frame["region"].tolist() == [2, 2]
    assert frame["spot"].tolist() == [6, 6]
    assert frame["gt"].tolist() == ["gt1l", "gt1l"]
    assert frame["segment_id_beg"].tolist() == [101, 102]
    assert frame["h_te_median"].tolist() == [100.5, 101.0]
    assert frame.index[1] - frame.index[0] == 100_000_000_000


def test_load_cached_resource_requires_exact_local_file(tmp_path: Path):
    with pytest.raises(
        MODULE.Campaign014DirectRecoveryError,
        match="run the Campaign 014 NSIDC bootstrap first",
    ):
        MODULE.load_cached_resource(
            "ATL08_20210504235905_06291102_007_01.h5",
            polygon=_polygon(),
            cache_dir=tmp_path,
        )


def test_download_searches_exact_granule_and_caches_expected_name(
    tmp_path: Path, monkeypatch
):
    calls: list[tuple[str, object]] = []
    resource = "ATL08_20210504235905_06291102_007_01.h5"

    class FakeEarthaccess:
        @staticmethod
        def login(strategy="all"):
            calls.append(("login", strategy))
            return object()

        @staticmethod
        def search_data(**kwargs):
            calls.append(("search", dict(kwargs)))
            return [SimpleNamespace(name=resource)]

        @staticmethod
        def download(results, target):
            calls.append(("download", target))
            path = Path(target) / resource
            _write_synthetic(path)
            return [str(path)]

    monkeypatch.setattr(MODULE, "_earthaccess", lambda: FakeEarthaccess)

    paths = MODULE.download_resources([resource], cache_dir=tmp_path)

    assert paths == [tmp_path / resource]
    search = next(value for name, value in calls if name == "search")
    assert search["short_name"] == "ATL08"
    assert search["version"] == "007"
    assert search["granule_name"] == resource
    assert (tmp_path / resource).is_file()
